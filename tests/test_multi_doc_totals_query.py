"""Tests verifying cross-document multi-document aggregate queries."""

from pathlib import Path
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
from tools.vector_retrieval.service import VectorRetrievalService
from tools.vector_storage.constants import DEFAULT_COLLECTION_NAME
from tools.vector_storage.models import VectorStorageInput
from tools.vector_storage.service import VectorStorageService


def test_three_documents_aggregate_totals_query(tmp_path: Path):
    """Verify aggregate query over 3 selected documents retrieves Chunk 0 for all 3 documents."""
    chroma_dir = tmp_path / "chroma_multi_agg_test"
    chroma_dir.mkdir(parents=True, exist_ok=True)

    storage_svc = VectorStorageService()
    storage_svc._persist_dir = chroma_dir
    storage_svc._collection_name = DEFAULT_COLLECTION_NAME

    ws_id = "ws_group_alpha"

    # Create 3 documents with distinct totals in Chunk 0
    docs_data = [
        ("doc_inv_1", "INVOICE", "Grand Total: 1000.00"),
        ("doc_inv_2", "INVOICE", "Grand Total: 2500.00"),
        ("doc_bs_3", "BANK_STATEMENT", "Total Credit Amount: 5000.00"),
    ]

    for d_id, d_type, total_text in docs_data:
        chunk_0_text = f"=== DOCUMENT SUMMARY ===\nDocument ID: {d_id}\n\n=== TOTALS ===\n{total_text}"
        storage_svc.store_embeddings(
            VectorStorageInput(
                generated_embeddings=GeneratedDocumentEmbeddings(
                    document_id=d_id,
                    workspace_id=ws_id,
                    document_type=d_type,
                    embeddings=[
                        SingleGeneratedEmbedding(
                            chunk_id=f"{d_id}_c0",
                            document_id=d_id,
                            workspace_id=ws_id,
                            chunk_index=0,
                            text_content=chunk_0_text,
                            vector=[0.05] * DEFAULT_VECTOR_DIMENSIONS,
                            dimensions=DEFAULT_VECTOR_DIMENSIONS,
                        )
                    ],
                    metadata=EmbeddingGenerationMetadata(
                        document_id=d_id,
                        workspace_id=ws_id,
                        document_type=d_type,
                        embedding_model="test-model",
                        total_chunks_processed=1,
                        vector_dimensions=DEFAULT_VECTOR_DIMENSIONS,
                    ),
                )
            )
        )

    retrieval_svc = VectorRetrievalService(persist_dir=chroma_dir, collection_name=DEFAULT_COLLECTION_NAME)

    mock_emb_svc = MagicMock()
    mock_emb_svc.generate_embeddings.return_value = GeneratedDocumentEmbeddings(
        document_id="query_temp_id",
        workspace_id=ws_id,
        document_type="QUERY",
        embeddings=[
            SingleGeneratedEmbedding(
                chunk_id="q0",
                document_id="query_temp_id",
                workspace_id=ws_id,
                chunk_index=0,
                text_content="dummy",
                vector=[0.05] * DEFAULT_VECTOR_DIMENSIONS,
                dimensions=DEFAULT_VECTOR_DIMENSIONS,
            )
        ],
        metadata=EmbeddingGenerationMetadata(
            document_id="query_temp_id",
            workspace_id=ws_id,
            document_type="QUERY",
            embedding_model="test-model",
            total_chunks_processed=1,
            vector_dimensions=DEFAULT_VECTOR_DIMENSIONS,
        ),
    )

    query_svc = QueryService(embedding_service=mock_emb_svc, retrieval_service=retrieval_svc)
    query_svc._call_ai_provider = MagicMock(return_value="The combined total is 8,500.00.")

    res = query_svc.answer_query(
        QueryInput(
            workspace_id=ws_id,
            selected_document_ids=["doc_inv_1", "doc_inv_2", "doc_bs_3"],
            query="What is the combined total amount across all 3 documents?",
            top_k=5,
        )
    )

    assert query_svc._call_ai_provider.called
    passed_context = query_svc._call_ai_provider.call_args[1]["context_block"]
    assert "Grand Total: 1000.00" in passed_context
    assert "Grand Total: 2500.00" in passed_context
    assert "Total Credit Amount: 5000.00" in passed_context
    assert res.answer == "The combined total is 8,500.00."