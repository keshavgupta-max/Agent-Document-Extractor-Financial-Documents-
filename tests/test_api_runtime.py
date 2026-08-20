"""Phase 16 API Layer & AgentRuntime Integration Tests."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.dependencies import get_runtime
from api.documents import router as documents_router
from api.query import router as query_router
from core.runtime_models import (
    ExecutionMode,
    PipelineExecutionResult,
)


@pytest.fixture
def mock_runtime():
    """Returns a mock AgentRuntime."""
    runtime = MagicMock()
    runtime.run_ingestion_pipeline = AsyncMock()
    runtime.run_query_pipeline = AsyncMock()
    return runtime


@pytest.fixture
def client(mock_runtime):
    """Creates a FastAPI test client with runtime dependency overridden."""
    app = FastAPI()
    app.include_router(documents_router)
    app.include_router(query_router)

    app.dependency_overrides[get_runtime] = lambda: mock_runtime
    return TestClient(app)


def test_valid_ingestion_request_reaches_runtime(client, mock_runtime):
    """Verify valid ingestion request reaches AgentRuntime and returns 200."""
    mock_runtime.run_ingestion_pipeline.return_value = PipelineExecutionResult(
        success=True,
        mode=ExecutionMode.DOCUMENT_INGESTION,
        workspace_id="ws_123",
        document_id="doc_456",
        final_output={"status": "stored"},
        stages=[],
        total_execution_time_ms=120.5,
    )

    response = client.post(
        "/documents/ingest",
        json={
            "workspace_id": "ws_123",
            "file_path": "/tmp/invoice.pdf",
            "original_filename": "invoice.pdf",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["workspace_id"] == "ws_123"
    assert data["document_id"] == "doc_456"
    assert mock_runtime.run_ingestion_pipeline.called


def test_valid_query_request_reaches_runtime(client, mock_runtime):
    """Verify valid query request reaches AgentRuntime and returns 200."""
    mock_runtime.run_query_pipeline.return_value = PipelineExecutionResult(
        success=True,
        mode=ExecutionMode.QUERY,
        workspace_id="ws_123",
        final_output={"answer": "Total is $500."},
        stages=[],
        total_execution_time_ms=45.0,
    )

    response = client.post(
        "/query",
        json={
            "workspace_id": "ws_123",
            "selected_document_ids": ["doc_456"],
            "query": "What is the invoice total?",
            "top_k": 5,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["final_output"]["answer"] == "Total is $500."
    assert mock_runtime.run_query_pipeline.called


def test_ingestion_rejects_empty_workspace_id(client):
    """Verify ingestion rejects empty/whitespace workspace_id with 400 or 422."""
    response = client.post(
        "/documents/ingest",
        json={
            "workspace_id": "   ",
            "file_path": "/tmp/invoice.pdf",
            "original_filename": "invoice.pdf",
        },
    )
    assert response.status_code in (400, 422)


def test_query_rejects_empty_document_scope(client):
    """Verify query rejects empty selected_document_ids list."""
    response = client.post(
        "/query",
        json={
            "workspace_id": "ws_123",
            "selected_document_ids": [],
            "query": "What is the total?",
        },
    )
    assert response.status_code in (400, 422)


def test_query_rejects_empty_query_string(client):
    """Verify query rejects empty query string."""
    response = client.post(
        "/query",
        json={
            "workspace_id": "ws_123",
            "selected_document_ids": ["doc_456"],
            "query": "   ",
        },
    )
    assert response.status_code in (400, 422)


def test_runtime_failure_converted_to_controlled_response(client, mock_runtime):
    """Verify business failures inside pipeline return controlled result payload."""
    mock_runtime.run_ingestion_pipeline.return_value = PipelineExecutionResult(
        success=False,
        mode=ExecutionMode.DOCUMENT_INGESTION,
        workspace_id="ws_123",
        failed_stage="validate_document",
        error_message="Validation constraint failed.",
        stages=[],
        total_execution_time_ms=50.0,
    )

    response = client.post(
        "/documents/ingest",
        json={
            "workspace_id": "ws_123",
            "file_path": "/tmp/invoice.pdf",
            "original_filename": "invoice.pdf",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["failed_stage"] == "validate_document"
    assert "Validation constraint failed." in data["error_message"]


def test_unexpected_exception_masks_internal_details(client, mock_runtime):
    """Verify unexpected internal errors return generic 500 without leaking stack traces/keys."""
    mock_runtime.run_ingestion_pipeline.side_effect = RuntimeError(
        "CRITICAL_INTERNAL_DB_KEY_EXPOSED_12345 /var/chroma/data"
    )

    response = client.post(
        "/documents/ingest",
        json={
            "workspace_id": "ws_123",
            "file_path": "/tmp/invoice.pdf",
            "original_filename": "invoice.pdf",
        },
    )

    assert response.status_code == 500
    data = response.json()
    assert "CRITICAL_INTERNAL_DB_KEY" not in str(data)
    assert "chroma" not in str(data)
    assert data["detail"] == "An unexpected error occurred during document ingestion."