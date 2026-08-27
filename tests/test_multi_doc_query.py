"""Integration tests verifying multi-document query scopes (1 to 5 documents)."""

from pathlib import Path
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from api.query import router as query_router
from fastapi import FastAPI
from tools.embedding.constants import DEFAULT_VECTOR_DIMENSIONS
from tools.embedding.models import (
    EmbeddingGenerationMetadata,
    GeneratedDocumentEmbeddings,
    SingleGeneratedEmbedding,
)
from tools.query.models import QueryInput
from tools.query.service import QueryService
from tools.vector_retrieval.models import VectorRetrievalInput
from tools.vector_retrieval.service import VectorRetrievalService
from tools.vector_storage.constants import DEFAULT_COLLECTION_NAME
from tools.vector_storage.models import VectorStorageInput
from tools.vector_storage.service import VectorStorageService


@pytest.fixture
def multi_doc_storage(tmp_path: Path):
    """Sets up an isolated Chroma database populated with 3 documents in ws_alpha and 1 in ws_beta."""
    chroma_dir = tmp_path / "chroma_multi_doc_test"
    chroma_dir.mkdir(parents=True, exist_ok=True)

    storage_svc = VectorStorageService()
    storage_svc._persist_dir = chroma_dir
    storage_svc._collection_name = DEFAULT_COLLECTION_NAME

    def _create_mock_doc(ws_id, doc_id, doc_type, text_content):
        return GeneratedDocumentEmbeddings(
            document_id=doc_id,
            workspace_id=ws_id,
            document_type=doc_type,
            embeddings=[
                SingleGeneratedEmbedding(
                    chunk_id=f"{doc_id}_c0",
                    document_id=doc_id,
                    workspace_id=ws_id,
                    chunk_index=0,
                    text_content=text_content,
                    vector=[0.05] * DEFAULT_VECTOR_DIMENSIONS,
                    dimensions=DEFAULT_VECTOR_DIMENSIONS,
                )
            ],
            metadata=EmbeddingGenerationMetadata(
                document_id=doc_id,
                workspace_id=ws_id,
                document_type=doc_type,
                embedding_model="test-model",
                total_chunks_processed=1,
                vector_dimensions=DEFAULT_VECTOR_DIMENSIONS,
            ),
        )

    # ws_alpha docs
    storage_svc.store_embeddings(
        VectorStorageInput(generated_embeddings=_create_mock_doc("ws_alpha", "doc_inv_101", "INVOICE", "Invoice 101 Total $500"))
    )
    storage_svc.store_embeddings(
        VectorStorageInput(generated_embeddings=_create_mock_doc("ws_alpha", "doc_inv_102", "INVOICE", "Invoice 102 Total $700"))
    )
    storage_svc.store_embeddings(
        VectorStorageInput(generated_embeddings=_create_mock_doc("ws_alpha", "doc_bank_103", "BANK_STATEMENT", "Bank Statement 103 Total Credits $5000"))
    )
    # ws_beta doc
    storage_svc.store_embeddings(
        VectorStorageInput(generated_embeddings=_create_mock_doc("ws_beta", "doc_foreign_201", "INVOICE", "Foreign Invoice Total $9000"))
    )

    retrieval_svc = VectorRetrievalService(persist_dir=chroma_dir, collection_name=DEFAULT_COLLECTION_NAME)
    return retrieval_svc


def test_three_document_cross_query_scope(multi_doc_storage):
    """Verify vector retrieval retrieves chunks across 3 selected documents in the same workspace."""
    query_vector = [0.05] * DEFAULT_VECTOR_DIMENSIONS
    retrieval_input = VectorRetrievalInput(
        workspace_id="ws_alpha",
        selected_document_ids=["doc_inv_101", "doc_inv_102", "doc_bank_103"],
        query_embedding=query_vector,
        top_k=5,
    )

    res = multi_doc_storage.retrieve(retrieval_input)
    assert res.total_results == 3
    retrieved_doc_ids = {c.document_id for c in res.retrieved_chunks}
    assert retrieved_doc_ids == {"doc_inv_101", "doc_inv_102", "doc_bank_103"}


def test_foreign_workspace_excluded_in_multi_document_query(multi_doc_storage):
    """Verify querying foreign workspace document ID returns zero results for that foreign ID."""
    query_vector = [0.05] * DEFAULT_VECTOR_DIMENSIONS
    retrieval_input = VectorRetrievalInput(
        workspace_id="ws_alpha",
        selected_document_ids=["doc_inv_101", "doc_foreign_201"],
        query_embedding=query_vector,
        top_k=5,
    )

    res = multi_doc_storage.retrieve(retrieval_input)
    assert res.total_results == 1
    assert res.retrieved_chunks[0].document_id == "doc_inv_101"


def test_api_rejects_more_than_five_selected_documents():
    """Verify /query endpoint rejects requests with > 5 selected documents with 400/422."""
    app = FastAPI()
    app.include_router(query_router)
    client = TestClient(app)

    response = client.post(
        "/query",
        json={
            "workspace_id": "ws_alpha",
            "selected_document_ids": ["d1", "d2", "d3", "d4", "d5", "d6"],
            "query": "What is the total across all documents?",
            "top_k": 5,
        },
    )
    assert response.status_code in (400, 422)