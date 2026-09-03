"""Regression tests verifying original_filename persistence in vector metadata and workspace listing."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from tools.embedding.constants import DEFAULT_VECTOR_DIMENSIONS
from tools.embedding.models import (
    EmbeddingGenerationMetadata,
    GeneratedDocumentEmbeddings,
    SingleGeneratedEmbedding,
)
from tools.vector_storage.constants import META_KEY_ORIGINAL_FILENAME
from tools.vector_storage.models import VectorStorageInput
from tools.vector_storage.service import VectorStorageService

client = TestClient(app)


def _seed_document_with_filename(
    workspace_id: str,
    document_id: str,
    original_filename: str,
    chunk_id: str = "chk_0",
):
    """Helper to seed a document with original_filename metadata into ChromaDB."""
    service = VectorStorageService()
    single_embedding = SingleGeneratedEmbedding(
        chunk_id=chunk_id,
        document_id=document_id,
        workspace_id=workspace_id,
        chunk_index=0,
        text_content="Sample statement text for filename verification.",
        vector=[0.05] * DEFAULT_VECTOR_DIMENSIONS,
        dimensions=DEFAULT_VECTOR_DIMENSIONS,
    )
    metadata = EmbeddingGenerationMetadata(
        document_id=document_id,
        workspace_id=workspace_id,
        document_type="BANK_STATEMENT",
        original_filename=original_filename,
        embedding_model="test-model",
        total_chunks_processed=1,
        vector_dimensions=DEFAULT_VECTOR_DIMENSIONS,
        processing_time_ms=5.0,
    )
    generated_embeddings = GeneratedDocumentEmbeddings(
        document_id=document_id,
        workspace_id=workspace_id,
        document_type="BANK_STATEMENT",
        original_filename=original_filename,
        embeddings=[single_embedding],
        metadata=metadata,
    )
    service.store_embeddings(VectorStorageInput(generated_embeddings=generated_embeddings))


def test_document_filename_persistence_and_listing():
    """Verify that original_filename is persisted in Chroma metadata and returned by GET /documents."""
    ws_id = "ws_test_filename"
    doc_id = "doc_filename_101"
    filename = "may_salary_statement.csv"

    # 1. Seed document with filename
    _seed_document_with_filename(
        workspace_id=ws_id,
        document_id=doc_id,
        original_filename=filename,
        chunk_id="chk_fn_1",
    )

    # 2. Call GET /documents
    response = client.get(f"/documents?workspace_id={ws_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["total_documents"] >= 1

    matched_doc = next((d for d in data["documents"] if d["document_id"] == doc_id), None)
    assert matched_doc is not None
    assert matched_doc["original_filename"] == filename
    assert matched_doc["document_type"] == "BANK_STATEMENT"
    assert matched_doc["total_chunks"] >= 1

    # Clean up
    del_resp = client.delete(f"/documents/{doc_id}?workspace_id={ws_id}")
    assert del_resp.status_code == 200


def test_document_filename_fallback_for_legacy_records():
    """Verify that legacy vector records without original_filename fall back safely to 'Unnamed Document'."""
    ws_id = "ws_test_legacy_fn"
    doc_id = "doc_legacy_102"

    # 1. Seed document using default fallback (no custom filename passed)
    service = VectorStorageService()
    single_embedding = SingleGeneratedEmbedding(
        chunk_id="chk_leg_1",
        document_id=doc_id,
        workspace_id=ws_id,
        chunk_index=0,
        text_content="Legacy invoice record without explicit filename.",
        vector=[0.05] * DEFAULT_VECTOR_DIMENSIONS,
        dimensions=DEFAULT_VECTOR_DIMENSIONS,
    )
    metadata = EmbeddingGenerationMetadata(
        document_id=doc_id,
        workspace_id=ws_id,
        document_type="INVOICE",
        embedding_model="test-model",
        total_chunks_processed=1,
        vector_dimensions=DEFAULT_VECTOR_DIMENSIONS,
        processing_time_ms=5.0,
    )
    generated_embeddings = GeneratedDocumentEmbeddings(
        document_id=doc_id,
        workspace_id=ws_id,
        document_type="INVOICE",
        embeddings=[single_embedding],
        metadata=metadata,
    )
    service.store_embeddings(VectorStorageInput(generated_embeddings=generated_embeddings))

    # 2. Call GET /documents and assert graceful fallback
    response = client.get(f"/documents?workspace_id={ws_id}")
    assert response.status_code == 200
    data = response.json()

    matched_doc = next((d for d in data["documents"] if d["document_id"] == doc_id), None)
    assert matched_doc is not None
    assert matched_doc["original_filename"] == "Unnamed Document"

    # Clean up
    client.delete(f"/documents/{doc_id}?workspace_id={ws_id}")


def test_document_filename_workspace_isolation():
    """Verify that filenames and documents remain strictly isolated across different workspaces."""
    ws_a = "ws_iso_a"
    ws_b = "ws_iso_b"
    doc_a = "doc_iso_a"
    filename_a = "workspace_a_exclusive.pdf"

    _seed_document_with_filename(workspace_id=ws_a, document_id=doc_a, original_filename=filename_a)

    # Workspace A sees its document and filename
    resp_a = client.get(f"/documents?workspace_id={ws_a}")
    assert resp_a.status_code == 200
    doc_ids_a = [d["document_id"] for d in resp_a.json()["documents"]]
    assert doc_a in doc_ids_a

    # Workspace B does not see Workspace A's document
    resp_b = client.get(f"/documents?workspace_id={ws_b}")
    assert resp_b.status_code == 200
    doc_ids_b = [d["document_id"] for d in resp_b.json()["documents"]]
    assert doc_a not in doc_ids_b

    # Clean up
    client.delete(f"/documents/{doc_a}?workspace_id={ws_a}")