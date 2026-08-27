"""Query Service executing grounded AI question-answering over retrieved vector context."""

import time
from typing import Any, List, Optional
from google import genai
from google.genai import types

from config import settings
from logger import logger
from tools.embedding.models import EmbeddingInput
from tools.embedding.service import EmbeddingService
from tools.embedding_prep.models import PreparedChunk, PreparedDocumentContent
from tools.query.constants import (
    DEFAULT_QUERY_MODEL,
    MAX_QUERY_LENGTH,
    MAX_RELEVANT_DISTANCE_THRESHOLD,
    SYSTEM_INSTRUCTIONS,
)
from tools.query.exceptions import AIProviderError, InvalidQueryInputError, QueryError
from tools.query.models import QueryInput, QueryResult, QuerySourceChunk
from tools.vector_retrieval.models import VectorRetrievalInput
from tools.vector_retrieval.service import VectorRetrievalService


class QueryService:
    """Service responsible for query embedding, vector retrieval, prompt isolation, and AI generation."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = DEFAULT_QUERY_MODEL,
        embedding_service: Optional[EmbeddingService] = None,
        retrieval_service: Optional[VectorRetrievalService] = None,
    ) -> None:
        self._api_key = api_key or getattr(settings, "GEMINI_API_KEY", None)
        self._model_name = model_name
        self._embedding_service = embedding_service or EmbeddingService(api_key=self._api_key)
        self._retrieval_service = retrieval_service or VectorRetrievalService()

        if self._api_key:
            self._client = genai.Client(api_key=self._api_key)
        else:
            self._client = genai.Client()

    def answer_query(self, input_data: QueryInput) -> QueryResult:
        """Executes full Phase 14 AI query workflow.

        Raises:
            InvalidQueryInputError: If inputs fail scope or length validation.
            AIProviderError: If embedding, retrieval, or LLM generation fails.
            QueryError: For general query workflow errors.
        """
        self._validate_input(input_data)

        start_time = time.perf_counter()
        query_embedding_ms = 0.0
        retrieval_ms = 0.0
        context_construction_ms = 0.0
        generation_ms = 0.0
        workspace_id = input_data.workspace_id.strip()
        doc_ids = [d.strip() for d in input_data.selected_document_ids]
        user_query = input_data.query.strip()
        top_k = input_data.top_k
        target_model = input_data.model_name or self._model_name

        try:
            logger.info(
                "Phase 14 AI Query started | Workspace: %s | Docs: %s",
                workspace_id,
                doc_ids,
            )

            # 1. Generate query embedding via existing Phase 11 infrastructure
            query_prep_content = PreparedDocumentContent(
                document_id="query_temp_id",
                workspace_id=workspace_id,
                document_type="QUERY",
                full_semantic_text=user_query,
                chunks=[
                    PreparedChunk(
                        chunk_id="query_chunk_0",
                        document_id="query_temp_id",
                        workspace_id=workspace_id,
                        chunk_index=0,
                        text_content=user_query,
                        metadata={},
                    )
                ],
                metadata={
                    "document_id": "query_temp_id",
                    "workspace_id": workspace_id,
                    "document_type": "QUERY",
                    "total_chunks": 1,
                    "total_characters": len(user_query),
                },
            )

            t_emb_start = time.perf_counter()
            emb_result = self._embedding_service.generate_embeddings(
                EmbeddingInput(prepared_content=query_prep_content)
            )
            query_embedding_ms = (time.perf_counter() - t_emb_start) * 1000.0

            if not emb_result.embeddings:
                raise AIProviderError("Failed to generate embedding vector for user query.")

            query_vector = emb_result.embeddings[0].vector

            # 2. Retrieve scoped chunks via existing Phase 13 infrastructure
            retrieval_input = VectorRetrievalInput(
                workspace_id=workspace_id,
                selected_document_ids=doc_ids,
                query_embedding=query_vector,
                top_k=top_k,
                query_text=input_data.query,
            )
            retrieval_result = self._retrieval_service.retrieve(retrieval_input)
            retrieval_ms = retrieval_result.processing_time_ms

            # Scope verification
            for chunk in retrieval_result.retrieved_chunks:
                if (
                    chunk.workspace_id != workspace_id
                    or chunk.document_id not in doc_ids
                ):
                    raise QueryError(
                        "Vector retrieval returned a chunk outside the requested document scope."
                    )

            # 3. Construct prompt with prompt-injection defense boundary
            t_ctx_start = time.perf_counter()
            context_block, source_chunks = self._format_retrieved_context(
                retrieval_result.retrieved_chunks
            )
            context_construction_ms = (time.perf_counter() - t_ctx_start) * 1000.0

            # Determine if at least one chunk satisfies explicit minimum similarity distance
            has_relevant_chunk = False
            if retrieval_result.retrieved_chunks:
                for chunk in retrieval_result.retrieved_chunks:
                    if chunk.distance is not None and chunk.distance <= MAX_RELEVANT_DISTANCE_THRESHOLD:
                        has_relevant_chunk = True
                        break

            # 4. Generate grounded AI response or early short-circuit
            if not retrieval_result.retrieved_chunks or not has_relevant_chunk:
                ai_answer = (
                    "The available selected documents do not provide enough information to answer this question."
                )
            else:
                t_gen_start = time.perf_counter()
                ai_answer = self._call_ai_provider(
                    user_query=user_query,
                    context_block=context_block,
                    model_name=target_model,
                )
                generation_ms = (time.perf_counter() - t_gen_start) * 1000.0

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            result = QueryResult(
                workspace_id=workspace_id,
                selected_document_ids=doc_ids,
                query=user_query,
                answer=ai_answer,
                source_chunks=source_chunks,
                total_sources_retrieved=len(source_chunks),
                processing_time_ms=round(elapsed_ms, 2),
            )

            logger.info(
                "Phase 14 AI Query completed for workspace '%s' in %.2fms | Sources: %d",
                workspace_id,
                result.processing_time_ms,
                result.total_sources_retrieved,
            )

            logger.info(
                "Query Performance Breakdown | Workspace: %s | Chunks: %d | "
                "Embedding: %.2fms | Retrieval: %.2fms | Context: %.2fms | "
                "Generation: %.2fms | Total: %.2fms",
                workspace_id,
                len(source_chunks),
                query_embedding_ms,
                retrieval_ms,
                context_construction_ms,
                generation_ms,
                result.processing_time_ms,
            )

            return result

        except (InvalidQueryInputError, AIProviderError):
            raise
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            error_msg = f"AI Query execution failed for workspace '{workspace_id}': {str(exc)}"
            logger.error(error_msg, exc_info=True)
            raise QueryError(error_msg) from exc

    def _validate_input(self, input_data: QueryInput) -> None:
        """Strict validation of query parameters."""
        if not input_data:
            raise InvalidQueryInputError("Query input payload cannot be None.")

        if not input_data.workspace_id or not input_data.workspace_id.strip():
            raise InvalidQueryInputError("Mandatory field 'workspace_id' is missing or empty.")

        if not input_data.selected_document_ids or len(input_data.selected_document_ids) == 0:
            raise InvalidQueryInputError(
                "Explicit 'selected_document_ids' scope must be provided. Global search is prohibited."
            )

        for idx, doc_id in enumerate(input_data.selected_document_ids):
            if not doc_id or not doc_id.strip():
                raise InvalidQueryInputError(f"Selected document ID at index {idx} is empty or blank.")

        if not input_data.query or not input_data.query.strip():
            raise InvalidQueryInputError("Mandatory field 'query' is missing or empty.")

        if len(input_data.query.strip()) > MAX_QUERY_LENGTH:
            raise InvalidQueryInputError(
                f"Query length ({len(input_data.query.strip())}) exceeds maximum limit ({MAX_QUERY_LENGTH})."
            )

    def _format_retrieved_context(self, chunks: List[Any]) -> tuple[str, List[QuerySourceChunk]]:
        """Formats retrieved chunks into a secure context payload."""
        formatted_blocks: List[str] = []
        sources: List[QuerySourceChunk] = []

        for idx, chunk in enumerate(chunks, start=1):
            source_item = QuerySourceChunk(
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                workspace_id=chunk.workspace_id,
                chunk_index=chunk.metadata.chunk_index,
                document_type=chunk.metadata.document_type,
                snippet=chunk.text_content,
                distance=chunk.distance,
            )
            sources.append(source_item)

            block = (
                f"--- BEGIN SOURCE EXCERPT #{idx} ---\n"
                f"Document ID: {chunk.document_id}\n"
                f"Document Type: {chunk.metadata.document_type}\n"
                f"Content:\n{chunk.text_content.strip()}\n"
                f"--- END SOURCE EXCERPT #{idx} ---"
            )
            formatted_blocks.append(block)

        unified_context = "\n\n".join(formatted_blocks)
        return unified_context, sources

    def _call_ai_provider(self, user_query: str, context_block: str, model_name: str) -> str:
        """Invokes Google GenAI API with strict system instructions and context separation."""
        try:
            prompt_payload = (
                f"RETRIEVED DOCUMENT CONTEXT:\n"
                f"{context_block}\n\n"
                f"USER QUESTION:\n"
                f"{user_query}"
            )

            config = types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTIONS,
                temperature=0.0,
            )

            response = self._client.models.generate_content(
                model=model_name,
                contents=prompt_payload,
                config=config,
            )

            if not response or not response.text:
                raise AIProviderError("AI provider returned an empty or malformed text response.")

            return response.text.strip()

        except Exception as exc:
            if isinstance(exc, AIProviderError):
                raise
            error_msg = f"Google GenAI generate_content API call failed: {str(exc)}"
            logger.error(error_msg)
            raise AIProviderError(error_msg) from exc