"""Integration tests for /documents/upload and /documents listing endpoints."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.dependencies import get_runtime
from api.documents import router as documents_router
from core.runtime import AgentRuntime
from core.runtime_models import ExecutionMode, PipelineExecutionResult
from core.tool_result import ToolResult
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
def mock_runtime():
    runtime = MagicMock(spec=AgentRuntime)
    runtime._staging_root = Path("data/staging")
    runtime.run_ingestion_pipeline = AsyncMock()
    return runtime


@pytest.fixture
def client(mock_runtime):
    app = FastAPI()
    app.include_router(documents_router)
    app.dependency_overrides[get_runtime] = lambda: mock_runtime
    return TestClient(app)


def test_multipart_upload_success_and_cleanup(client, mock_runtime, tmp_path):
    """Verify multipart upload runs 8-stage pipeline and cleans up temporary staging file."""
    mock_runtime._staging_root = tmp_path

    # Simulate pipeline execution
    async def mock_run(payload):
        # Assert temporary staged file exists while pipeline is executing
        staged_path = Path(payload.file_path)
        assert staged_path.exists()
        assert staged_path.read_bytes() == b"%PDF-1.4 sample invoice"
        return PipelineExecutionResult(
            success=True,
            mode=ExecutionMode.DOCUMENT_INGESTION,
            workspace_id=payload.workspace_id,
            document_id="doc_mp_123",
            final_output={"stored_count": 2},
            stages=[],
            total_execution_time_ms=50.0,
        )

    mock_runtime.run_ingestion_pipeline.side_effect = mock_run

    response = client.post(
        "/documents/upload",
        data={"workspace_id": "ws_upload_test"},
        files={"file": ("invoice.pdf", b"%PDF-1.4 sample invoice", "application/pdf")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["workspace_id"] == "ws_upload_test"
    assert data["document_id"] == "doc_mp_123"

    # Verify staging cleanup: no staged files remain in staging dir
    staged_files = list(tmp_path.glob("staged_*"))
    assert len(staged_files) == 0


def test_multipart_upload_rejects_disallowed_extension(client):
    """Verify upload validator blocks dangerous/unsupported extensions."""
    response = client.post(
        "/documents/upload",
        data={"workspace_id": "ws_upload_test"},
        files={"file": ("malicious.exe", b"binary executable", "application/octet-stream")},
    )
    assert response.status_code == 400
    assert "Unsupported file extension" in response.json()["detail"] or "Forbidden" in response.json()["detail"]


def test_workspace_document_listing_isolation(tmp_path, monkeypatch):
    """Verify GET /documents returns only documents belonging to requested workspace."""
    chroma_dir = tmp_path / "chroma_listing_test"
    chroma_dir.mkdir(parents=True, exist_ok=True)

    storage_svc = VectorStorageService()
    storage_svc._persist_dir = chroma_dir
    storage_svc._collection_name = DEFAULT_COLLECTION_NAME

    def _create_mock_payload(ws_id, doc_id, doc_type, num_chunks=2):
        embs = []
        for i in range(num_chunks):
            embs.append(
                SingleGeneratedEmbedding(
                    chunk_id=f"{doc_id}_{i}",
                    document_id=doc_id,
                    workspace_id=ws_id,
                    chunk_index=i,
                    text_content=f"Chunk {i}",
                    vector=[0.01] * DEFAULT_VECTOR_DIMENSIONS,
                    dimensions=DEFAULT_VECTOR_DIMENSIONS,
                )
            )
        return GeneratedDocumentEmbeddings(
            document_id=doc_id,
            workspace_id=ws_id,
            document_type=doc_type,
            embeddings=embs,
            metadata=EmbeddingGenerationMetadata(
                document_id=doc_id,
                workspace_id=ws_id,
                document_type=doc_type,
                embedding_model="test-model",
                total_chunks_processed=num_chunks,
                vector_dimensions=DEFAULT_VECTOR_DIMENSIONS,
            ),
        )

    # Populate WS_1 with 2 documents (Invoice + Bank Statement)
    storage_svc.store_embeddings(
        VectorStorageInput(generated_embeddings=_create_mock_payload("ws_1", "doc_inv_1", "INVOICE", 2))
    )
    storage_svc.store_embeddings(
        VectorStorageInput(generated_embeddings=_create_mock_payload("ws_1", "doc_bank_1", "BANK_STATEMENT", 3))
    )
    # Populate WS_2 with 1 document
    storage_svc.store_embeddings(
        VectorStorageInput(generated_embeddings=_create_mock_payload("ws_2", "doc_inv_2", "INVOICE", 1))
    )

    app = FastAPI()
    app.include_router(documents_router)

    # Monkeypatch VectorStorageService inside api.documents to use the test isolated Chroma directory
    monkeypatch.setattr(
        "api.documents.VectorStorageService",
        lambda: storage_svc,
    )
    client = TestClient(app)

    # Query ws_1
    res1 = client.get("/documents?workspace_id=ws_1")
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["workspace_id"] == "ws_1"
    assert data1["total_documents"] == 2
    doc_ids_ws1 = {d["document_id"] for d in data1["documents"]}
    assert doc_ids_ws1 == {"doc_inv_1", "doc_bank_1"}

    # Query ws_2
    res2 = client.get("/documents?workspace_id=ws_2")
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["workspace_id"] == "ws_2"
    assert data2["total_documents"] == 1
    assert data2["documents"][0]["document_id"] == "doc_inv_2"

    # Query non-existent ws_empty
    res3 = client.get("/documents?workspace_id=ws_empty")
    assert res3.status_code == 200
    data3 = res3.json()
    assert data3["workspace_id"] == "ws_empty"
    assert data3["total_documents"] == 0
    assert data3["documents"] == []