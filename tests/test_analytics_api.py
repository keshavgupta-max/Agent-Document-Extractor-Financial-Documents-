"""Tests for deterministic financial analytics API endpoints."""

from pathlib import Path
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.analytics import router as analytics_router
from tools.embedding.constants import DEFAULT_VECTOR_DIMENSIONS
from tools.embedding.models import (
    EmbeddingGenerationMetadata,
    GeneratedDocumentEmbeddings,
    SingleGeneratedEmbedding,
)
from tools.vector_storage.constants import DEFAULT_COLLECTION_NAME
from tools.vector_storage.models import VectorStorageInput
from tools.vector_storage.service import VectorStorageService


@pytest.fixture
def analytics_test_env(tmp_path: Path, monkeypatch):
    """Sets up an isolated ChromaDB populated with bank statements and invoices."""
    chroma_dir = tmp_path / "chroma_analytics_test"
    chroma_dir.mkdir(parents=True, exist_ok=True)

    storage_svc = VectorStorageService()
    storage_svc._persist_dir = chroma_dir
    storage_svc._collection_name = DEFAULT_COLLECTION_NAME

    ws_id = "ws_analytics_alpha"
    foreign_ws = "ws_analytics_beta"

    # 1. Bank Statement Doc (ws_analytics_alpha) with simulated 150-char chunk overlap
    bs_chunk_0 = (
        "=== DOCUMENT SUMMARY ===\n"
        "Document ID: doc_bs_01\n"
        "Workspace ID: ws_analytics_alpha\n"
        "Document Type: BANK_STATEMENT\n\n"
        "=== ADDITIONAL DETAILS & SUMMARY ===\n"
        "Total Credit Amount: 50000.00\n"
        "Total Debit Amount: 20000.00\n"
        "Total Transactions: 2\n"
        "Opening Balance: 10000.00\n"
        "Closing Balance: 40000.00"
    )
    # Chunk 1 contains Item 1 and Item 2
    bs_chunk_1 = (
        "=== LINE ITEMS & SERVICES ===\n"
        "Item 1: Date: 2022-01-10 | Type: Cr | Amount: 50000.00 | Balance: 60000.00 | Description: Client Payment\n"
        "Item 2: Date: 2022-01-12 | Type: Db | Amount: 20000.00 | Balance: 40000.00 | Description: Vendor Payout"
    )
    # Chunk 2 overlaps Item 2 due to 150-char boundary overlap
    bs_chunk_2 = (
        "Item 2: Date: 2022-01-12 | Type: Db | Amount: 20000.00 | Balance: 40000.00 | Description: Vendor Payout\n"
        "=== EXTRACTED PAGE TEXT ===\n"
        "Raw statement lines here"
    )

    storage_svc.store_embeddings(
        VectorStorageInput(
            generated_embeddings=GeneratedDocumentEmbeddings(
                document_id="doc_bs_01",
                workspace_id=ws_id,
                document_type="BANK_STATEMENT",
                embeddings=[
                    SingleGeneratedEmbedding(
                        chunk_id="doc_bs_01_c0",
                        document_id="doc_bs_01",
                        workspace_id=ws_id,
                        chunk_index=0,
                        text_content=bs_chunk_0,
                        vector=[0.01] * DEFAULT_VECTOR_DIMENSIONS,
                        dimensions=DEFAULT_VECTOR_DIMENSIONS,
                    ),
                    SingleGeneratedEmbedding(
                        chunk_id="doc_bs_01_c1",
                        document_id="doc_bs_01",
                        workspace_id=ws_id,
                        chunk_index=1,
                        text_content=bs_chunk_1,
                        vector=[0.01] * DEFAULT_VECTOR_DIMENSIONS,
                        dimensions=DEFAULT_VECTOR_DIMENSIONS,
                    ),
                    SingleGeneratedEmbedding(
                        chunk_id="doc_bs_01_c2",
                        document_id="doc_bs_01",
                        workspace_id=ws_id,
                        chunk_index=2,
                        text_content=bs_chunk_2,
                        vector=[0.01] * DEFAULT_VECTOR_DIMENSIONS,
                        dimensions=DEFAULT_VECTOR_DIMENSIONS,
                    ),
                ],
                metadata=EmbeddingGenerationMetadata(
                    document_id="doc_bs_01",
                    workspace_id=ws_id,
                    document_type="BANK_STATEMENT",
                    embedding_model="test-model",
                    total_chunks_processed=3,
                    vector_dimensions=DEFAULT_VECTOR_DIMENSIONS,
                ),
            )
        )
    )

    # 2. Invoice Doc (ws_analytics_alpha)
    inv_chunk_0 = (
        "=== DOCUMENT SUMMARY ===\n"
        "Document ID: doc_inv_02\n"
        "Workspace ID: ws_analytics_alpha\n"
        "Document Type: INVOICE\n\n"
        "=== TOTALS ===\n"
        "Subtotal: 8000.00\n"
        "Tax Amount: 1440.00\n"
        "Grand Total: 9440.00\n"
        "Currency: USD"
    )
    storage_svc.store_embeddings(
        VectorStorageInput(
            generated_embeddings=GeneratedDocumentEmbeddings(
                document_id="doc_inv_02",
                workspace_id=ws_id,
                document_type="INVOICE",
                embeddings=[
                    SingleGeneratedEmbedding(
                        chunk_id="doc_inv_02_c0",
                        document_id="doc_inv_02",
                        workspace_id=ws_id,
                        chunk_index=0,
                        text_content=inv_chunk_0,
                        vector=[0.02] * DEFAULT_VECTOR_DIMENSIONS,
                        dimensions=DEFAULT_VECTOR_DIMENSIONS,
                    )
                ],
                metadata=EmbeddingGenerationMetadata(
                    document_id="doc_inv_02",
                    workspace_id=ws_id,
                    document_type="INVOICE",
                    embedding_model="test-model",
                    total_chunks_processed=1,
                    vector_dimensions=DEFAULT_VECTOR_DIMENSIONS,
                ),
            )
        )
    )

    # 3. Foreign Doc (ws_analytics_beta)
    foreign_chunk_0 = (
        "=== DOCUMENT SUMMARY ===\n"
        "Document ID: doc_foreign_03\n"
        "Workspace ID: ws_analytics_beta\n"
        "Document Type: BANK_STATEMENT\n\n"
        "=== ADDITIONAL DETAILS & SUMMARY ===\n"
        "Total Credit Amount: 999999.00\n"
        "Total Debit Amount: 0.00"
    )
    storage_svc.store_embeddings(
        VectorStorageInput(
            generated_embeddings=GeneratedDocumentEmbeddings(
                document_id="doc_foreign_03",
                workspace_id=foreign_ws,
                document_type="BANK_STATEMENT",
                embeddings=[
                    SingleGeneratedEmbedding(
                        chunk_id="doc_foreign_03_c0",
                        document_id="doc_foreign_03",
                        workspace_id=foreign_ws,
                        chunk_index=0,
                        text_content=foreign_chunk_0,
                        vector=[0.03] * DEFAULT_VECTOR_DIMENSIONS,
                        dimensions=DEFAULT_VECTOR_DIMENSIONS,
                    )
                ],
                metadata=EmbeddingGenerationMetadata(
                    document_id="doc_foreign_03",
                    workspace_id=foreign_ws,
                    document_type="BANK_STATEMENT",
                    embedding_model="test-model",
                    total_chunks_processed=1,
                    vector_dimensions=DEFAULT_VECTOR_DIMENSIONS,
                ),
            )
        )
    )

    app = FastAPI()
    app.include_router(analytics_router)

    monkeypatch.setattr(
        "api.analytics.VectorRetrievalService._get_client",
        lambda self: storage_svc._get_client(),
    )

    client = TestClient(app)
    return client, ws_id, foreign_ws


def test_analytics_summary_bank_statement(analytics_test_env):
    """Verify deterministic credit, debit, net cash flow, and balances."""
    client, ws_id, _ = analytics_test_env

    response = client.get(
        "/analytics/summary",
        params={"workspace_id": ws_id, "document_ids": ["doc_bs_01"]},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["workspace_id"] == ws_id
    assert data["total_credit_amount"] == 50000.00
    assert data["total_debit_amount"] == 20000.00
    assert data["net_cash_flow"] == 30000.00
    assert data["total_transactions"] == 2
    assert data["opening_balance"] == 10000.00
    assert data["closing_balance"] == 40000.00
    assert data["documents_analyzed"] == 1


def test_analytics_summary_invoice_totals(analytics_test_env):
    """Verify deterministic invoice subtotal, tax, grand total, and currency."""
    client, ws_id, _ = analytics_test_env

    response = client.get(
        "/analytics/summary",
        params={"workspace_id": ws_id, "document_ids": ["doc_inv_02"]},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["invoice_subtotal"] == 8000.00
    assert data["invoice_tax"] == 1440.00
    assert data["invoice_grand_total"] == 9440.00
    assert data["currency"] == "USD"
    assert data["documents_analyzed"] == 1


def test_analytics_summary_workspace_isolation(analytics_test_env):
    """Verify summary ignores documents from foreign workspace."""
    client, ws_id, foreign_ws = analytics_test_env

    response = client.get(
        "/analytics/summary",
        params={"workspace_id": ws_id, "document_ids": ["doc_foreign_03"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["documents_analyzed"] == 0
    assert data["total_credit_amount"] is None


def test_analytics_transactions_deduplication_and_pagination(analytics_test_env):
    """Verify chunk-overlap duplicate Item 2 in chunk 2 is ignored, preserving exact total count."""
    client, ws_id, _ = analytics_test_env

    # Fetch with limit covering all transactions
    response = client.get(
        "/analytics/transactions",
        params={"workspace_id": ws_id, "document_id": "doc_bs_01", "limit": 10, "offset": 0},
    )
    assert response.status_code == 200
    data = response.json()

    # Total unique transactions must be 2, not 3 (Item 2 duplicated across chunk 1 & 2)
    assert data["total_transactions"] == 2
    assert len(data["transactions"]) == 2

    t1 = data["transactions"][0]
    assert t1["item_number"] == 1
    assert t1["date"] == "2022-01-10"
    assert t1["transaction_type"] == "CR"
    assert t1["credit_amount"] == 50000.00
    assert t1["balance"] == 60000.00

    t2 = data["transactions"][1]
    assert t2["item_number"] == 2
    assert t2["date"] == "2022-01-12"
    assert t2["transaction_type"] == "DB"
    assert t2["debit_amount"] == 20000.00
    assert t2["balance"] == 40000.00


def test_analytics_transactions_foreign_document_rejected(analytics_test_env):
    """Verify 404 when document does not belong to workspace."""
    client, ws_id, _ = analytics_test_env

    response = client.get(
        "/analytics/transactions",
        params={"workspace_id": ws_id, "document_id": "doc_foreign_03"},
    )
    assert response.status_code == 404