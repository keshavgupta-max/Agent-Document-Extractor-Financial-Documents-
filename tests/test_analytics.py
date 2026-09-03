"""Tests for deterministic financial analytics summary and transaction parsing."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from tools.embedding.constants import DEFAULT_VECTOR_DIMENSIONS
from tools.embedding.models import (
    EmbeddingGenerationMetadata,
    GeneratedDocumentEmbeddings,
    SingleGeneratedEmbedding,
)
from tools.vector_storage.models import VectorStorageInput
from tools.vector_storage.service import VectorStorageService

client = TestClient(app)


def test_transaction_parser_formats_and_fallback():
    """Verify that Item #1, Item 1, Transaction #1, and fallback formats are parsed correctly."""
    ws_id = "ws_test_parser"
    doc_id = "doc_parser_101"

    service = VectorStorageService()
    # Chunk 0 with Summary metadata
    chunk_0 = SingleGeneratedEmbedding(
        chunk_id="chk_p0",
        document_id=doc_id,
        workspace_id=ws_id,
        chunk_index=0,
        text_content=(
            "=== DOCUMENT SUMMARY ===\n"
            "Document Type: BANK_STATEMENT\n"
            "Total Credit Amount: 15000.00\n"
            "Total Debit Amount: 5000.00\n"
            "Currency: INR\n"
            "=== LINE ITEMS ===\n"
            "Item #1: Date: 2024-01-01 | Type: CR | Amount: 10000.00 | Balance: 10000.00 | Description: Salary\n"
            "Item 2: Date: 2024-01-02 | Type: DB | Amount: 2000.00 | Balance: 8000.00 | Description: Rent\n"
            "Transaction #3: Date: 2024-01-03 | Type: CR | Amount: 5000.00 | Balance: 13000.00 | Description: Bonus\n"
            "Transaction: Date: 2024-01-04 | Type: DB | Amount: 3000.00 | Balance: 10000.00 | Description: Grocery\n"
        ),
        vector=[0.1] * DEFAULT_VECTOR_DIMENSIONS,
        dimensions=DEFAULT_VECTOR_DIMENSIONS,
    )

    metadata = EmbeddingGenerationMetadata(
        document_id=doc_id,
        workspace_id=ws_id,
        document_type="BANK_STATEMENT",
        embedding_model="test-model",
        total_chunks_processed=1,
        vector_dimensions=DEFAULT_VECTOR_DIMENSIONS,
        processing_time_ms=5.0,
    )

    gen_embeddings = GeneratedDocumentEmbeddings(
        document_id=doc_id,
        workspace_id=ws_id,
        document_type="BANK_STATEMENT",
        embeddings=[chunk_0],
        metadata=metadata,
    )

    service.store_embeddings(VectorStorageInput(generated_embeddings=gen_embeddings))

    # Test GET /analytics/transactions
    response = client.get(f"/analytics/transactions?workspace_id={ws_id}&document_id={doc_id}")
    assert response.status_code == 200
    data = response.json()

    transactions = data["transactions"]
    assert len(transactions) == 4

    # Verify Item #1
    assert transactions[0]["item_number"] == 1
    assert transactions[0]["amount"] == 10000.00
    assert transactions[0]["transaction_type"] == "CR"

    # Verify Item 2
    assert transactions[1]["item_number"] == 2
    assert transactions[1]["amount"] == 2000.00

    # Verify Transaction #3
    assert transactions[2]["item_number"] == 3
    assert transactions[2]["amount"] == 5000.00

    # Verify Fallback (Transaction without explicit number gets sequence number 4)
    assert transactions[3]["item_number"] == 4
    assert transactions[3]["amount"] == 3000.00

    # Cleanup
    client.delete(f"/documents/{doc_id}?workspace_id={ws_id}")