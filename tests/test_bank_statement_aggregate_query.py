"""Tests verifying bank statement aggregate queries augment context with Chunk 0 totals."""

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


@pytest.fixture
def multi_chunk_bank_statement(tmp_path: Path):
    """Indexes a large 10-chunk bank statement in ChromaDB."""
    chroma_dir = tmp_path / "chroma_bs_agg_test"
    chroma_dir.mkdir(parents=True, exist_ok=True)

    storage_svc = VectorStorageService()
    storage_svc._persist_dir = chroma_dir
    storage_svc._collection_name = DEFAULT_COLLECTION_NAME

    doc_id = "doc_bs_large_100"
    ws_id = "ws_finance_01"

    # Chunk 0 contains authoritative statement totals
    chunk_0_text = (
        "=== DOCUMENT SUMMARY ===\n"
        "Document ID: doc_bs_large_100\n"
        "Workspace ID: ws_finance_01\n"
        "Document Type: BANK_STATEMENT\n\n"
        "=== ADDITIONAL DETAILS & SUMMARY ===\n"
        "Total Credit Amount: 55000.00\n"
        "Total Debit Amount: 3500.50\n"
        "Total Transactions: 200\n"
        "Opening Balance: 10000.00\n"
        "Closing Balance: 61499.50"
    )

    embeddings = [
        SingleGeneratedEmbedding(
            chunk_id=f"{doc_id}_c0",
            document_id=doc_id,
            workspace_id=ws_id,
            chunk_index=0,
            text_content=chunk_0_text,
            vector=[0.01] * DEFAULT_VECTOR_DIMENSIONS,
            dimensions=DEFAULT_VECTOR_DIMENSIONS,
        )
    ]

    # Add 9 transaction chunks
    for i in range(1, 10):
        embeddings.append(
            SingleGeneratedEmbedding(
                chunk_id=f"{doc_id}_c{i}",
                document_id=doc_id,
                workspace_id=ws_id,
                chunk_index=i,
                text_content=f"2022-01-{10+i:02d} | UPI | Cr | Amount: 1000.00 | Bal: 50000.00",
                vector=[0.80] * DEFAULT_VECTOR_DIMENSIONS,  # farther vector
                dimensions=DEFAULT_VECTOR_DIMENSIONS,
            )
        )

    storage_svc.store_embeddings(
        VectorStorageInput(
            generated_embeddings=GeneratedDocumentEmbeddings(
                document_id=doc_id,
                workspace_id=ws_id,
                document_type="BANK_STATEMENT",
                embeddings=embeddings,
                metadata=EmbeddingGenerationMetadata(
                    document_id=doc_id,
                    workspace_id=ws_id,
                    document_type="BANK_STATEMENT",
                    embedding_model="test-model",
                    total_chunks_processed=len(embeddings),
                    vector_dimensions=DEFAULT_VECTOR_DIMENSIONS,
                ),
            )
        )
    )

    retrieval_svc = VectorRetrievalService(persist_dir=chroma_dir, collection_name=DEFAULT_COLLECTION_NAME)
    return retrieval_svc, ws_id, doc_id


def test_aggregate_query_augments_chunk_0(multi_chunk_bank_statement):
    """Verify aggregate query (total credits) includes Chunk 0 with full totals."""
    retrieval_svc, ws_id, doc_id = multi_chunk_bank_statement

    # Mock embedding service returning vector pointing towards transaction rows
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
                vector=[0.80] * DEFAULT_VECTOR_DIMENSIONS,
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
    query_svc._call_ai_provider = MagicMock(return_value="Total money credited is 55,000.00 INR.")

    res = query_svc.answer_query(
        QueryInput(
            workspace_id=ws_id,
            selected_document_ids=[doc_id],
            query="How much money was credited to the account in total?",
            top_k=3,
        )
    )

    # Verify Chunk 0 was retrieved and passed to AI
    assert query_svc._call_ai_provider.called
    passed_context = query_svc._call_ai_provider.call_args[1]["context_block"]
    assert "Total Credit Amount: 55000.00" in passed_context
    assert res.answer == "Total money credited is 55,000.00 INR."