"""Service responsible for generating embedding vectors using Google GenAI SDK."""

import random
import re
import time
from typing import List, Optional
from google import genai
from google.genai import types

from config import settings
from logger import logger
from tools.embedding.constants import (
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_VECTOR_DIMENSIONS,
    EMBEDDING_RETRY_BASE_DELAY_SECONDS,
    EMBEDDING_RETRY_MAX_DELAY_SECONDS,
    MAX_EMBEDDING_BATCH_SIZE,
    MAX_EMBEDDING_RETRIES,
)
from tools.embedding.exceptions import (
    EmbeddingGenerationError,
    InvalidPreparedContentError,
    ProviderAPIError,
)
from tools.embedding.models import (
    EmbeddingGenerationMetadata,
    EmbeddingInput,
    GeneratedDocumentEmbeddings,
    SingleGeneratedEmbedding,
)
from tools.embedding.utils import truncate_text_for_embedding, validate_vector_dimensions


class EmbeddingService:
    """Service that converts prepared text chunks into dense numerical embedding vectors."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = DEFAULT_EMBEDDING_MODEL,
        vector_dimensions: int = DEFAULT_VECTOR_DIMENSIONS,
        max_retries: int = MAX_EMBEDDING_RETRIES,
        base_delay: float = EMBEDDING_RETRY_BASE_DELAY_SECONDS,
        max_delay: float = EMBEDDING_RETRY_MAX_DELAY_SECONDS,
    ) -> None:
        self._api_key = api_key or getattr(settings, "GEMINI_API_KEY", None)
        self._model_name = model_name
        self._vector_dimensions = vector_dimensions
        self._max_retries = max_retries
        self._base_delay = base_delay
        self._max_delay = max_delay

        if self._api_key:
            self._client = genai.Client(api_key=self._api_key)
        else:
            self._client = genai.Client()

    def generate_embeddings(self, input_data: EmbeddingInput) -> GeneratedDocumentEmbeddings:
        """Calls the Google GenAI embedding provider to vectorize chunks in batched requests.

        Raises:
            InvalidPreparedContentError: If input prepared content contains no chunks.
            ProviderAPIError: If the embedding API call fails or yields invalid output.
            EmbeddingGenerationError: If an unexpected error occurs during vector generation.
        """
        prep_content = input_data.prepared_content
        if not prep_content or not prep_content.chunks:
            error_msg = (
                f"No chunks available for embedding generation in document "
                f"'{prep_content.document_id if prep_content else 'UNKNOWN'}'."
            )
            logger.error(error_msg)
            raise InvalidPreparedContentError(error_msg)

        start_time = time.perf_counter()
        doc_id = prep_content.document_id
        workspace_id = prep_content.workspace_id
        doc_type = prep_content.document_type
        chunks = prep_content.chunks

        try:
            logger.info(
                "Starting batch embedding generation for doc_id: %s | Workspace: %s | Chunks: %d | Model: %s",
                doc_id,
                workspace_id,
                len(chunks),
                self._model_name,
            )

            generated_embeddings: List[SingleGeneratedEmbedding] = []

            # Batch process chunks to maximize API efficiency while preserving strict chunk mapping
            for i in range(0, len(chunks), MAX_EMBEDDING_BATCH_SIZE):
                batch_chunks = chunks[i : i + MAX_EMBEDDING_BATCH_SIZE]
                cleaned_texts = [
                    truncate_text_for_embedding(chunk.text_content) for chunk in batch_chunks
                ]

                # Make batch API call guaranteeing deterministic 1-to-1 vector ordering
                vectors = self._call_provider_api_batch(cleaned_texts)

                if len(vectors) != len(batch_chunks):
                    raise ProviderAPIError(
                        f"Mismatch between input batch size ({len(batch_chunks)}) "
                        f"and returned vectors ({len(vectors)})."
                    )

                # Deterministically map vectors back to source chunks in exact positional order
                for chunk, vector in zip(batch_chunks, vectors):
                    validate_vector_dimensions(vector, self._vector_dimensions)

                    single_emb = SingleGeneratedEmbedding(
                        chunk_id=chunk.chunk_id,
                        document_id=doc_id,
                        workspace_id=workspace_id,
                        chunk_index=chunk.chunk_index,
                        text_content=chunk.text_content,
                        vector=vector,
                        dimensions=len(vector),
                    )
                    generated_embeddings.append(single_emb)

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            metadata = EmbeddingGenerationMetadata(
                document_id=doc_id,
                workspace_id=workspace_id,
                document_type=doc_type,
                embedding_model=self._model_name,
                total_chunks_processed=len(generated_embeddings),
                vector_dimensions=self._vector_dimensions,
                processing_time_ms=round(elapsed_ms, 2),
            )

            result = GeneratedDocumentEmbeddings(
                document_id=doc_id,
                workspace_id=workspace_id,
                document_type=doc_type,
                embeddings=generated_embeddings,
                metadata=metadata,
            )

            logger.info(
                "Successfully generated embeddings for doc_id: %s in %.2fms | Vectors: %d",
                doc_id,
                metadata.processing_time_ms,
                len(generated_embeddings),
            )

            return result

        except (InvalidPreparedContentError, ProviderAPIError):
            raise
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            error_msg = f"Failed to generate embeddings for document '{doc_id}': {str(exc)}"
            logger.error(error_msg, exc_info=True)
            raise EmbeddingGenerationError(error_msg) from exc

    def _call_provider_api_batch(self, texts: List[str]) -> List[List[float]]:
        """Calls client.models.embed_content using types.Content wrappers per text to guarantee true batching and independent 1-to-1 vector generation.
           Applies exponential backoff with jitter on HTTP 429 / RESOURCE_EXHAUSTED errors.
        """
        content_objects = [
            types.Content(parts=[types.Part.from_text(text=t)]) for t in texts
        ]

        config = types.EmbedContentConfig(
            output_dimensionality=self._vector_dimensions,
        )

        for attempt in range(self._max_retries + 1):
            try:
                response = self._client.models.embed_content(
                    model=self._model_name,
                    contents=content_objects,
                    config=config,
                )

                if not response or not hasattr(response, "embeddings") or not response.embeddings:
                    raise ProviderAPIError("Provider returned an empty or malformed embeddings response.")

                if len(response.embeddings) != len(content_objects):
                    raise ProviderAPIError(
                        f"Provider returned {len(response.embeddings)} embeddings, but "
                        f"{len(content_objects)} content objects were sent."
                    )

                extracted_vectors: List[List[float]] = []
                for emb_item in response.embeddings:
                    if hasattr(emb_item, "values") and emb_item.values is not None:
                        extracted_vectors.append(list(emb_item.values))
                    else:
                        raise ProviderAPIError("Embedding item missing 'values' array in response.")

                return extracted_vectors

            except Exception as exc:
                if isinstance(exc, ProviderAPIError):
                    raise

                if self._is_rate_limit_error(exc) and attempt < self._max_retries:
                    retry_delay = self._calculate_retry_delay(exc, attempt)
                    logger.warning(
                        "Encountered rate limit (429/RESOURCE_EXHAUSTED) during embedding generation. "
                        "Backing off for %.2fs before retry (Attempt %d/%d)...",
                        retry_delay,
                        attempt + 1,
                        self._max_retries,
                    )
                    time.sleep(retry_delay)
                    continue

                error_msg = f"Google GenAI embedding API call failed: {str(exc)}"
                logger.error(error_msg)
                raise ProviderAPIError(error_msg) from exc

    def _is_rate_limit_error(self, exc: Exception) -> bool:
        """Determines if an exception corresponds to an explicit 429 / rate limit / quota exhaustion."""
        err_msg = str(exc).lower()
        return (
            "429" in err_msg
            or "resource_exhausted" in err_msg
            or "quota exceeded" in err_msg
            or "rate limit" in err_msg
            or getattr(exc, "code", None) == 429
            or getattr(exc, "status_code", None) == 429
        )

    def _calculate_retry_delay(self, exc: Exception, attempt: int) -> float:
        """Calculates backoff delay preferring provider retry-after metadata when available, falling back to exponential backoff with full jitter."""
        # Check for explicit retry-after metadata or response headers
        retry_after = getattr(exc, "retry_after", None)
        if retry_after is not None:
            try:
                delay = float(retry_after)
                if delay > 0:
                    return min(delay, self._max_delay)
            except (ValueError, TypeError):
                pass

        # Check for retry-after embedded in error message strings
        err_msg = str(exc)
        match = re.search(r"retry in (\d+(?:\.\d+)?)s", err_msg, re.IGNORECASE) or re.search(
            r"retry-after:\s*(\d+(?:\.\d+)?)", err_msg, re.IGNORECASE
        )
        if match:
            try:
                delay = float(match.group(1))
                if delay > 0:
                    return min(delay, self._max_delay)
            except (ValueError, TypeError):
                pass

        # Exponential backoff with full jitter: Uniform(0, min(max_delay, base_delay * 2^attempt))
        exponential_cap = min(self._max_delay, self._base_delay * (2 ** attempt))
        delay = random.uniform(self._base_delay / 2.0, exponential_cap)
        return max(0.5, delay)