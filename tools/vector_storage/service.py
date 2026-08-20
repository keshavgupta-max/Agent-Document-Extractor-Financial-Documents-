"""Service responsible for persisting document embedding vectors to local ChromaDB."""

import time
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from logger import logger
from tools.embedding.models import GeneratedDocumentEmbeddings
from tools.vector_storage.constants import (
    DEFAULT_COLLECTION_NAME,
    DEFAULT_CHROMA_STORAGE_DIR,
    ID_SEPARATOR,
    META_KEY_CHUNK_ID,
    META_KEY_CHUNK_INDEX,
    META_KEY_DOCUMENT_ID,
    META_KEY_DOCUMENT_TYPE,
    META_KEY_EMBEDDING_MODEL,
    META_KEY_VECTOR_DIMENSIONS,
    META_KEY_WORKSPACE_ID,
)
from tools.vector_storage.exceptions import (
    InvalidVectorDataError,
    VectorDatabaseConnectionError,
    VectorStorageError,
    VectorStorageOperationError,
)
from tools.vector_storage.models import VectorStorageInput, VectorStorageResult


class VectorStorageService:
    """Core persistence service providing idempotent vector storage in local ChromaDB."""

    def __init__(self) -> None:
        """Initialize the service using only application-controlled storage configuration."""
        self._persist_dir = DEFAULT_CHROMA_STORAGE_DIR
        self._collection_name = DEFAULT_COLLECTION_NAME
        self._client: Optional[chromadb.ClientAPI] = None

    def _get_client(self) -> chromadb.ClientAPI:
        """Lazy initialization of local persistent ChromaDB client."""
        if self._client is None:
            try:
                self._persist_dir.mkdir(parents=True, exist_ok=True)

                self._client = chromadb.PersistentClient(
                    path=str(self._persist_dir),
                    settings=ChromaSettings(
                        anonymized_telemetry=False,
                    ),
                )

            except Exception as exc:
                error_msg = (
                    "Failed to initialize local ChromaDB client "
                    "at the application-configured storage path."
                )

                logger.error(
                    "ChromaDB connection error: %s",
                    str(exc),
                    exc_info=True,
                )

                raise VectorDatabaseConnectionError(error_msg) from exc

        return self._client

    def store_embeddings(
        self,
        input_data: VectorStorageInput,
    ) -> VectorStorageResult:
        """Persist generated document embeddings using deterministic IDs and idempotent upserts.

        Raises:
            InvalidVectorDataError: If the input payload contains missing,
                empty, duplicate, or inconsistent vector data.
            VectorDatabaseConnectionError: If local ChromaDB initialization fails.
            VectorStorageOperationError: If the ChromaDB persistence operation fails.
            VectorStorageError: For unexpected storage failures.
        """
        gen_embeddings: GeneratedDocumentEmbeddings = input_data.generated_embeddings

        self._validate_input_payload(gen_embeddings)

        start_time = time.perf_counter()

        doc_id = gen_embeddings.document_id.strip()
        workspace_id = gen_embeddings.workspace_id.strip()
        doc_type = gen_embeddings.document_type.strip()
        meta_info = gen_embeddings.metadata

        try:
            client = self._get_client()

            collection = client.get_or_create_collection(
                name=self._collection_name,
            )

            record_ids: List[str] = []
            vectors: List[List[float]] = []
            metadatas: List[Dict[str, Any]] = []
            documents: List[str] = []

            for emb in gen_embeddings.embeddings:
                chunk_id = emb.chunk_id.strip()

                # Deterministic record ID:
                # workspace_id : document_id : chunk_id
                record_id = (
                    f"{workspace_id}"
                    f"{ID_SEPARATOR}"
                    f"{doc_id}"
                    f"{ID_SEPARATOR}"
                    f"{chunk_id}"
                )

                chunk_metadata: Dict[str, Any] = {
                    META_KEY_WORKSPACE_ID: workspace_id,
                    META_KEY_DOCUMENT_ID: doc_id,
                    META_KEY_DOCUMENT_TYPE: doc_type,
                    META_KEY_CHUNK_ID: chunk_id,
                    META_KEY_CHUNK_INDEX: emb.chunk_index,
                    META_KEY_EMBEDDING_MODEL: meta_info.embedding_model,
                    META_KEY_VECTOR_DIMENSIONS: meta_info.vector_dimensions,
                }

                record_ids.append(record_id)
                vectors.append(emb.vector)
                metadatas.append(chunk_metadata)
                documents.append(emb.text_content)

            logger.info(
                "Upserting %d vectors into collection for doc_id: %s | Workspace: %s",
                len(record_ids),
                doc_id,
                workspace_id,
            )

            # Idempotent persistence via upsert.
            collection.upsert(
                ids=record_ids,
                embeddings=vectors,
                metadatas=metadatas,
                documents=documents,
            )

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            result = VectorStorageResult(
                document_id=doc_id,
                workspace_id=workspace_id,
                stored_count=len(record_ids),
                record_ids=record_ids,
                collection_name=self._collection_name,
                processing_time_ms=round(elapsed_ms, 2),
            )

            logger.info(
                "Successfully stored %d vectors for document_id: %s in %.2fms",
                result.stored_count,
                doc_id,
                result.processing_time_ms,
            )

            return result

        except (
            InvalidVectorDataError,
            VectorDatabaseConnectionError,
        ):
            raise

        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            error_msg = (
                f"Failed to persist vectors for document '{doc_id}': "
                f"{str(exc)}"
            )

            logger.error(
                error_msg,
                exc_info=True,
            )

            raise VectorStorageOperationError(error_msg) from exc

    def _validate_input_payload(
        self,
        gen_embeddings: GeneratedDocumentEmbeddings,
    ) -> None:
        """Strictly validate vector payload completeness and consistency before database operations."""

        if not gen_embeddings:
            raise InvalidVectorDataError(
                "Input generated_embeddings payload cannot be None."
            )

        if (
            not gen_embeddings.workspace_id
            or not gen_embeddings.workspace_id.strip()
        ):
            raise InvalidVectorDataError(
                "Mandatory field 'workspace_id' is missing or empty."
            )

        if (
            not gen_embeddings.document_id
            or not gen_embeddings.document_id.strip()
        ):
            raise InvalidVectorDataError(
                "Mandatory field 'document_id' is missing or empty."
            )

        if (
            not gen_embeddings.document_type
            or not gen_embeddings.document_type.strip()
        ):
            raise InvalidVectorDataError(
                "Mandatory field 'document_type' is missing or empty."
            )

        if not gen_embeddings.embeddings:
            raise InvalidVectorDataError(
                f"No vector embeddings present in payload for document "
                f"'{gen_embeddings.document_id}'."
            )

        expected_dim = gen_embeddings.metadata.vector_dimensions

        # Track chunk IDs to prevent duplicate deterministic ChromaDB IDs.
        seen_chunk_ids = set()

        for idx, emb in enumerate(gen_embeddings.embeddings):
            if not emb.chunk_id or not emb.chunk_id.strip():
                raise InvalidVectorDataError(
                    f"Embedding item at index {idx} is missing a valid "
                    "'chunk_id'."
                )

            chunk_id = emb.chunk_id.strip()

            if chunk_id in seen_chunk_ids:
                raise InvalidVectorDataError(
                    f"Duplicate chunk_id '{chunk_id}' found in embedding "
                    f"payload at index {idx}."
                )

            seen_chunk_ids.add(chunk_id)

            if not emb.vector:
                raise InvalidVectorDataError(
                    f"Vector data for chunk '{chunk_id}' at index {idx} "
                    "is empty or None."
                )

            if expected_dim > 0 and len(emb.vector) != expected_dim:
                raise InvalidVectorDataError(
                    f"Vector dimension mismatch for chunk '{chunk_id}': "
                    f"expected {expected_dim}, got {len(emb.vector)}."
                )