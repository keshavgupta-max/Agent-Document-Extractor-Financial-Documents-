# ==============================================================================
# File: tests/test_documents_delete.py
# ==============================================================================

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


def _seed_test_document(workspace_id: str, document_id: str, chunk_id: str = "chk_0"):
    """Helper to seed a test document into vector storage using canonical models."""
    service = VectorStorageService()
    single_embedding = SingleGeneratedEmbedding(
        chunk_id=chunk_id,
        document_id=document_id,
        workspace_id=workspace_id,
        chunk_index=0,
        text_content="Sample invoice test content for deletion verification.",
        vector=[0.1] * DEFAULT_VECTOR_DIMENSIONS,
        dimensions=DEFAULT_VECTOR_DIMENSIONS,
    )
    metadata = EmbeddingGenerationMetadata(
        document_id=document_id,
        workspace_id=workspace_id,
        document_type="INVOICE",
        embedding_model="test-model",
        total_chunks_processed=1,
        vector_dimensions=DEFAULT_VECTOR_DIMENSIONS,
        processing_time_ms=10.0,
    )
    generated_embeddings = GeneratedDocumentEmbeddings(
        document_id=document_id,
        workspace_id=workspace_id,
        document_type="INVOICE",
        embeddings=[single_embedding],
        metadata=metadata,
    )
    service.store_embeddings(VectorStorageInput(generated_embeddings=generated_embeddings))


def test_delete_document_success_and_isolation():
    """Verify document deletion removes only the target document and is isolated."""
    ws_id = "ws_test_lifecycle"
    doc_a = "doc_test_lifecycle_a"
    doc_b = "doc_test_lifecycle_b"

    # 1. Seed two distinct documents in the same workspace
    _seed_test_document(workspace_id=ws_id, document_id=doc_a, chunk_id="chk_a")
    _seed_test_document(workspace_id=ws_id, document_id=doc_b, chunk_id="chk_b")

    # Verify both are listed
    list_resp = client.get(f"/documents?workspace_id={ws_id}")
    assert list_resp.status_code == 200
    doc_ids = [d["document_id"] for d in list_resp.json()["documents"]]
    assert doc_a in doc_ids
    assert doc_b in doc_ids

    # 2. Delete document A
    del_resp = client.delete(f"/documents/{doc_a}?workspace_id={ws_id}")
    assert del_resp.status_code == 200
    del_data = del_resp.json()
    assert del_data["success"] is True
    assert del_data["document_id"] == doc_a
    assert del_data["workspace_id"] == ws_id
    assert del_data["deleted_chunks"] >= 1

    # 3. Verify document A is gone, but document B remains intact
    list_after = client.get(f"/documents?workspace_id={ws_id}")
    assert list_after.status_code == 200
    docs_after = [d["document_id"] for d in list_after.json()["documents"]]
    assert doc_a not in docs_after
    assert doc_b in docs_after

    # 4. Attempting to delete document A again returns 404
    del_repeat = client.delete(f"/documents/{doc_a}?workspace_id={ws_id}")
    assert del_repeat.status_code == 404

    # Clean up document B
    client.delete(f"/documents/{doc_b}?workspace_id={ws_id}")


def test_delete_document_cross_workspace_forbidden():
    """Verify deleting a document from another workspace is rejected with 404 and leaves the document intact."""
    ws_a = "ws_auth_a"
    ws_b = "ws_auth_b"
    doc_a = "doc_protected_a"

    # 1. Seed a document in workspace A
    _seed_test_document(workspace_id=ws_a, document_id=doc_a, chunk_id="chk_prot_a")

    # 2. Attempt to delete document A using workspace B
    cross_del_resp = client.delete(f"/documents/{doc_a}?workspace_id={ws_b}")
    assert cross_del_resp.status_code == 404
    assert cross_del_resp.json()["detail"] == "Document not found in the specified workspace."

    # 3. Verify document A still exists and is intact in workspace A
    list_resp = client.get(f"/documents?workspace_id={ws_a}")
    assert list_resp.status_code == 200
    doc_ids = [d["document_id"] for d in list_resp.json()["documents"]]
    assert doc_a in doc_ids

    # Cleanup workspace A
    client.delete(f"/documents/{doc_a}?workspace_id={ws_a}")