"""Regression tests for Query Service semantic distance guardrail and short-circuiting."""

from unittest.mock import MagicMock
import pytest

from tools.embedding.constants import DEFAULT_VECTOR_DIMENSIONS
from tools.embedding.models import (
    EmbeddingGenerationMetadata,
    GeneratedDocumentEmbeddings,
    SingleGeneratedEmbedding,
)
from tools.query.models import QueryInput
from tools.query.service import QueryService
from tools.vector_retrieval.models import RetainedChunkMetadata, RetrievedChunk, VectorRetrievalResult


@pytest.fixture
def mock_embedding_service():
    service = MagicMock()
    mock_emb = SingleGeneratedEmbedding(
        chunk_id="q0",
        document_id="query_temp_id",
        workspace_id="ws_guard",
        chunk_index=0,
        text_content="dummy",
        vector=[0.01] * DEFAULT_VECTOR_DIMENSIONS,
        dimensions=DEFAULT_VECTOR_DIMENSIONS,
    )
    metadata = EmbeddingGenerationMetadata(
        document_id="query_temp_id",
        workspace_id="ws_guard",
        document_type="QUERY",
        embedding_model="test-embedding-model",
        total_chunks_processed=1,
        vector_dimensions=DEFAULT_VECTOR_DIMENSIONS,
        processing_time_ms=5.0,
    )
    service.generate_embeddings.return_value = GeneratedDocumentEmbeddings(
        document_id="query_temp_id",
        workspace_id="ws_guard",
        document_type="QUERY",
        embeddings=[mock_emb],
        metadata=metadata,
    )
    return service


def test_irrelevant_query_skips_llm_generation(mock_embedding_service):
    """Verify that chunks with distances above the threshold short-circuit without calling Gemini LLM."""
    mock_retrieval_service = MagicMock()

    # Return chunks with distance > 0.85 (irrelevant context)
    irrelevant_chunk = RetrievedChunk(
        chunk_id="chk_irr_1",
        document_id="doc_1",
        workspace_id="ws_guard",
        text_content="Invoice details for widgets",
        metadata=RetainedChunkMetadata(
            chunk_id="chk_irr_1",
            document_id="doc_1",
            workspace_id="ws_guard",
            chunk_index=0,
            document_type="INVOICE",
        ),
        distance=0.92,
    )
    mock_retrieval_service.retrieve.return_value = VectorRetrievalResult(
        workspace_id="ws_guard",
        selected_document_ids=["doc_1"],
        retrieved_chunks=[irrelevant_chunk],
        total_results=1,
        processing_time_ms=5.0,
    )

    query_svc = QueryService(
        embedding_service=mock_embedding_service,
        retrieval_service=mock_retrieval_service,
    )
    query_svc._call_ai_provider = MagicMock()

    payload = QueryInput(
        workspace_id="ws_guard",
        selected_document_ids=["doc_1"],
        query="What is the recipe for baking chocolate cake?",
    )

    result = query_svc.answer_query(payload)

    # LLM must NOT be called
    assert not query_svc._call_ai_provider.called
    assert result.answer == "The available selected documents do not provide enough information to answer this question."


def test_relevant_query_invokes_llm_generation(mock_embedding_service):
    """Verify that chunks within the distance threshold proceed to LLM generation."""
    mock_retrieval_service = MagicMock()

    # Return chunk with distance <= 0.85 (relevant context)
    relevant_chunk = RetrievedChunk(
        chunk_id="chk_rel_1",
        document_id="doc_1",
        workspace_id="ws_guard",
        text_content="Grand Total: 120,360.00 INR",
        metadata=RetainedChunkMetadata(
            chunk_id="chk_rel_1",
            document_id="doc_1",
            workspace_id="ws_guard",
            chunk_index=0,
            document_type="INVOICE",
        ),
        distance=0.15,
    )
    mock_retrieval_service.retrieve.return_value = VectorRetrievalResult(
        workspace_id="ws_guard",
        selected_document_ids=["doc_1"],
        retrieved_chunks=[relevant_chunk],
        total_results=1,
        processing_time_ms=5.0,
    )

    query_svc = QueryService(
        embedding_service=mock_embedding_service,
        retrieval_service=mock_retrieval_service,
    )
    query_svc._call_ai_provider = MagicMock(return_value="The invoice grand total is 120,360.00 INR.")

    payload = QueryInput(
        workspace_id="ws_guard",
        selected_document_ids=["doc_1"],
        query="What is the invoice total?",
    )

    result = query_svc.answer_query(payload)

    # LLM must be called
    assert query_svc._call_ai_provider.called
    assert result.answer == "The invoice grand total is 120,360.00 INR."