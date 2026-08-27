"""Service executing vector similarity search over local ChromaDB with strict metadata isolation."""

import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import chromadb
from chromadb.config import Settings as ChromaSettings

from logger import logger
from tools.embedding.constants import DEFAULT_VECTOR_DIMENSIONS
from tools.vector_retrieval.constants import (
    DEFAULT_CHROMA_STORAGE_DIR,
    DEFAULT_COLLECTION_NAME,
    MAX_TOP_K,
    META_KEY_CHUNK_ID,
    META_KEY_CHUNK_INDEX,
    META_KEY_DOCUMENT_ID,
    META_KEY_DOCUMENT_TYPE,
    META_KEY_WORKSPACE_ID,
)
from tools.vector_retrieval.exceptions import (
    InvalidRetrievalInputError,
    VectorDatabaseConnectionError,
    VectorRetrievalOperationError,
)
from tools.vector_retrieval.models import (
    RetainedChunkMetadata,
    RetrievedChunk,
    VectorRetrievalInput,
    VectorRetrievalResult,
)

# Deterministic aggregate query keyword patterns
AGGREGATE_KEYWORD_PATTERNS = [
    r"\btotal\b",
    r"\bsum\b",
    r"\bcombined\b",
    r"\baggregate\b",
    r"\boverall\b",
    r"\baltogether\b",
    r"\bentire\b",
    r"\bhow much in total\b",
    r"\btotal amount\b",
    r"\btotal credited\b",
    r"\btotal debited\b",
    r"\bgrand total\b",
    r"\bnet balance\b",
    r"\btotal spent\b",
    r"\btotal received\b",
    r"\bacross all\b",
    r"\bcombined total\b",
]


class VectorRetrievalService:
    """Service responsible for querying ChromaDB with mandatory workspace and document scope filters."""

    def __init__(
        self,
        persist_dir: Optional[Path] = None,
        collection_name: Optional[str] = None,
    ) -> None:
        self._persist_dir = persist_dir or DEFAULT_CHROMA_STORAGE_DIR
        self._collection_name = collection_name or DEFAULT_COLLECTION_NAME
        self._client: Optional[chromadb.ClientAPI] = None

    def _get_client(self) -> chromadb.ClientAPI:
        """Lazy initialization of persistent ChromaDB client."""
        if self._client is None:
            try:
                if not self._persist_dir.exists():
                    logger.error(
                        "Configured ChromaDB directory does not exist: %s",
                        self._persist_dir,
                    )
                    raise VectorDatabaseConnectionError(
                        "Vector database storage is unavailable."
                    )

                self._client = chromadb.PersistentClient(
                    path=str(self._persist_dir),
                    settings=ChromaSettings(anonymized_telemetry=False),
                )

            except VectorDatabaseConnectionError:
                raise

            except Exception as exc:
                logger.error(
                    "ChromaDB connection error during retrieval at configured storage path.",
                    exc_info=True,
                )
                raise VectorDatabaseConnectionError(
                    "Vector database storage is unavailable."
                ) from exc

        return self._client

    def _is_aggregate_query(self, query_text: Optional[str]) -> bool:
        """Determines if query expresses aggregate/holistic summary intent using deterministic regex rules."""
        if not query_text or not query_text.strip():
            return False
        clean_q = query_text.strip().lower()
        for pat in AGGREGATE_KEYWORD_PATTERNS:
            if re.search(pat, clean_q):
                return True
        return False

    def retrieve(
        self,
        input_data: VectorRetrievalInput,
    ) -> VectorRetrievalResult:
        """Executes vector similarity search against ChromaDB using mandatory workspace and document filters.

        Raises:
            InvalidRetrievalInputError: If retrieval input fails validation.
            VectorDatabaseConnectionError: If ChromaDB storage cannot be accessed.
            VectorRetrievalOperationError: If vector search execution fails.
        """
        self._validate_input(input_data)

        start_time = time.perf_counter()

        workspace_id = input_data.workspace_id.strip()
        doc_ids = [doc_id.strip() for doc_id in input_data.selected_document_ids]
        query_embedding = input_data.query_embedding
        top_k = input_data.top_k

        try:
            client = self._get_client()
            collection = client.get_collection(name=self._collection_name)

            where_filter = self._build_where_filter(
                workspace_id,
                doc_ids,
            )

            logger.info(
                "Executing vector retrieval for workspace '%s' | "
                "Document Scope: %s | top_k: %d",
                workspace_id,
                doc_ids,
                top_k,
            )

            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_filter,
                include=["documents", "metadatas", "distances"],
            )

            retrieved_chunks: List[RetrievedChunk] = []
            seen_chunk_ids: Set[str] = set()

            if results and results.get("ids") and len(results["ids"]) > 0:
                raw_ids = results["ids"][0]
                raw_docs = (
                    results["documents"][0]
                    if results.get("documents")
                    else []
                )
                raw_metas = (
                    results["metadatas"][0]
                    if results.get("metadatas")
                    else []
                )
                raw_dists = (
                    results["distances"][0]
                    if results.get("distances")
                    else []
                )

                for i, raw_id in enumerate(raw_ids):
                    if i >= len(raw_metas):
                        raise VectorRetrievalOperationError(
                            "Vector database returned incomplete metadata."
                        )

                    meta = raw_metas[i]

                    if not isinstance(meta, dict):
                        raise VectorRetrievalOperationError(
                            "Vector database returned invalid metadata."
                        )

                    # Mandatory metadata must come from the stored record.
                    # Never manufacture security-sensitive metadata from the request.
                    required_metadata = (
                        META_KEY_CHUNK_ID,
                        META_KEY_DOCUMENT_ID,
                        META_KEY_WORKSPACE_ID,
                        META_KEY_CHUNK_INDEX,
                        META_KEY_DOCUMENT_TYPE,
                    )

                    missing_keys = [
                        key
                        for key in required_metadata
                        if key not in meta or meta[key] is None
                    ]

                    if missing_keys:
                        raise VectorRetrievalOperationError(
                            "Vector database returned a record with missing "
                            "mandatory metadata."
                        )

                    chunk_id = str(meta[META_KEY_CHUNK_ID]).strip()
                    doc_id = str(meta[META_KEY_DOCUMENT_ID]).strip()
                    chunk_ws_id = str(meta[META_KEY_WORKSPACE_ID]).strip()
                    doc_type = str(meta[META_KEY_DOCUMENT_TYPE]).strip()

                    if (
                        not chunk_id
                        or not doc_id
                        or not chunk_ws_id
                        or not doc_type
                    ):
                        raise VectorRetrievalOperationError(
                            "Vector database returned a record with invalid "
                            "mandatory metadata."
                        )

                    try:
                        chunk_idx = int(meta[META_KEY_CHUNK_INDEX])
                    except (TypeError, ValueError) as exc:
                        raise VectorRetrievalOperationError(
                            "Vector database returned an invalid chunk index."
                        ) from exc

                    # Defense-in-depth:
                    # verify returned metadata still belongs to the requested scope.
                    if chunk_ws_id != workspace_id:
                        raise VectorRetrievalOperationError(
                            "Vector database returned a record outside the "
                            "requested workspace scope."
                        )

                    if doc_id not in doc_ids:
                        raise VectorRetrievalOperationError(
                            "Vector database returned a record outside the "
                            "requested document scope."
                        )

                    doc_text = (
                        raw_docs[i]
                        if i < len(raw_docs) and raw_docs[i] is not None
                        else ""
                    )

                    dist = (
                        raw_dists[i]
                        if i < len(raw_dists)
                        else None
                    )

                    chunk_meta = RetainedChunkMetadata(
                        chunk_id=chunk_id,
                        document_id=doc_id,
                        workspace_id=chunk_ws_id,
                        chunk_index=chunk_idx,
                        document_type=doc_type,
                    )

                    retrieved_chunks.append(
                        RetrievedChunk(
                            chunk_id=chunk_id,
                            document_id=doc_id,
                            workspace_id=chunk_ws_id,
                            text_content=doc_text,
                            metadata=chunk_meta,
                            distance=dist,
                        )
                    )
                    seen_chunk_ids.add(chunk_id)

            # Aggregate query summary augmentation: fetch chunk_index=0 for each selected document
            query_text = getattr(input_data, "query_text", None)
            if self._is_aggregate_query(query_text):
                logger.info("Aggregate query intent detected. Augmenting context with authoritative summary chunks.")
                for d_id in doc_ids:
                    # Binary $and filter matching workspace_id, document_id, and chunk_index == 0
                    summary_where = {
                        "$and": [
                            {
                                "$and": [
                                    {META_KEY_WORKSPACE_ID: {"$eq": workspace_id}},
                                    {META_KEY_DOCUMENT_ID: {"$eq": d_id}},
                                ]
                            },
                            {META_KEY_CHUNK_INDEX: {"$eq": 0}},
                        ]
                    }

                    try:
                        summary_records = collection.get(
                            where=summary_where,
                            include=["documents", "metadatas"],
                        )
                    except Exception as get_exc:
                        logger.warning("Summary chunk query fallback triggered for doc '%s': %s", d_id, str(get_exc))
                        summary_records = collection.get(
                            where={
                                "$and": [
                                    {META_KEY_WORKSPACE_ID: {"$eq": workspace_id}},
                                    {META_KEY_DOCUMENT_ID: {"$eq": d_id}},
                                ]
                            },
                            include=["documents", "metadatas"],
                        )

                    s_ids = summary_records.get("ids") or []
                    s_docs = summary_records.get("documents") or []
                    s_metas = summary_records.get("metadatas") or []

                    for s_idx in range(len(s_ids)):
                        s_meta = s_metas[s_idx] if s_idx < len(s_metas) else {}
                        if not isinstance(s_meta, dict):
                            continue

                        try:
                            s_chunk_idx = int(s_meta.get(META_KEY_CHUNK_INDEX, -1))
                        except (TypeError, ValueError):
                            continue

                        if s_chunk_idx == 0:
                            s_chunk_id = str(s_meta.get(META_KEY_CHUNK_ID, s_ids[s_idx])).strip()
                            s_doc_id = str(s_meta.get(META_KEY_DOCUMENT_ID, d_id)).strip()
                            s_ws_id = str(s_meta.get(META_KEY_WORKSPACE_ID, workspace_id)).strip()
                            s_doc_type = str(s_meta.get(META_KEY_DOCUMENT_TYPE, "UNKNOWN")).strip()
                            s_text = s_docs[s_idx] if s_idx < len(s_docs) and s_docs[s_idx] is not None else ""

                            # Defense-in-depth scope check
                            if s_ws_id != workspace_id or s_doc_id not in doc_ids:
                                continue

                            if s_chunk_id not in seen_chunk_ids:
                                retained_s_meta = RetainedChunkMetadata(
                                    chunk_id=s_chunk_id,
                                    document_id=s_doc_id,
                                    workspace_id=s_ws_id,
                                    chunk_index=0,
                                    document_type=s_doc_type,
                                )

                                summary_chunk = RetrievedChunk(
                                    chunk_id=s_chunk_id,
                                    document_id=s_doc_id,
                                    workspace_id=s_ws_id,
                                    text_content=s_text,
                                    metadata=retained_s_meta,
                                    distance=None,
                                )
                                retrieved_chunks.insert(0, summary_chunk)
                                seen_chunk_ids.add(s_chunk_id)
                            break

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            result = VectorRetrievalResult(
                workspace_id=workspace_id,
                selected_document_ids=doc_ids,
                retrieved_chunks=retrieved_chunks,
                total_results=len(retrieved_chunks),
                processing_time_ms=round(elapsed_ms, 2),
            )

            logger.info(
                "Successfully retrieved %d chunks for workspace '%s' in %.2fms",
                result.total_results,
                workspace_id,
                result.processing_time_ms,
            )

            return result

        except (
            InvalidRetrievalInputError,
            VectorDatabaseConnectionError,
            VectorRetrievalOperationError,
        ):
            raise

        except Exception as exc:
            error_msg = (
                f"Vector retrieval operation failed for workspace "
                f"'{workspace_id}': {str(exc)}"
            )
            logger.error(error_msg, exc_info=True)
            raise VectorRetrievalOperationError(
                "Vector retrieval operation failed."
            ) from exc

    def _validate_input(
        self,
        input_data: VectorRetrievalInput,
    ) -> None:
        """Validates query payload constraints before invoking database queries."""
        if not input_data:
            raise InvalidRetrievalInputError(
                "Retrieval input cannot be None."
            )

        if (
            not input_data.workspace_id
            or not input_data.workspace_id.strip()
        ):
            raise InvalidRetrievalInputError(
                "Mandatory field 'workspace_id' is missing or empty."
            )

        if (
            not input_data.selected_document_ids
            or len(input_data.selected_document_ids) == 0
        ):
            raise InvalidRetrievalInputError(
                "Explicit 'selected_document_ids' scope must be provided. "
                "Global search is prohibited."
            )

        for idx, doc_id in enumerate(input_data.selected_document_ids):
            if not doc_id or not doc_id.strip():
                raise InvalidRetrievalInputError(
                    f"Selected document ID at index {idx} is empty or blank."
                )

        if (
            not input_data.query_embedding
            or len(input_data.query_embedding) == 0
        ):
            raise InvalidRetrievalInputError(
                "Mandatory field 'query_embedding' is missing or empty."
            )

        if len(input_data.query_embedding) != DEFAULT_VECTOR_DIMENSIONS:
            raise InvalidRetrievalInputError(
                "Query embedding dimension does not match the "
                "application vector dimension."
            )

        if input_data.top_k <= 0:
            raise InvalidRetrievalInputError(
                f"Parameter 'top_k' must be greater than 0, "
                f"got {input_data.top_k}."
            )

        if input_data.top_k > MAX_TOP_K:
            raise InvalidRetrievalInputError(
                f"Parameter 'top_k' exceeds maximum allowed limit "
                f"({MAX_TOP_K}), got {input_data.top_k}."
            )

    def _build_where_filter(
        self,
        workspace_id: str,
        document_ids: List[str],
    ) -> Dict[str, Any]:
        """Constructs ChromaDB filter combining workspace and document constraints."""
        workspace_clause = {
            META_KEY_WORKSPACE_ID: workspace_id
        }

        if len(document_ids) == 1:
            document_clause = {
                META_KEY_DOCUMENT_ID: document_ids[0]
            }
        else:
            document_clause = {
                META_KEY_DOCUMENT_ID: {
                    "$in": document_ids
                }
            }

        return {
            "$and": [
                workspace_clause,
                document_clause,
            ]
        }