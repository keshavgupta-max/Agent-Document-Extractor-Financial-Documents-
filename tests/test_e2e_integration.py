"""Phase 17 Agent 1 End-to-End Integration Tests.

Verifies:
API -> AgentRuntime -> ToolRegistry -> Pipeline Tools
-> PipelineExecutionResult -> API Response.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.dependencies import get_runtime
from api.documents import router as documents_router
from api.query import router as query_router
from core.runtime import AgentRuntime
from core.tool_result import ToolResult


def _create_mock_stage_data(name: str):
    """Generate valid mock data matching existing pipeline models."""

    if name == "upload_document":
        return {
            "document_id": "doc_e2e_101",
            "file_path": "/tmp/sample_contract.pdf",
            "storage_path": "/tmp/sample_contract.pdf",
            "stored_filename": "doc_e2e_101.pdf",
            "workspace_id": "ws_enterprise",
            "status": "SUCCESS",
        }

    if name == "parse_document":
        return {
            "document_id": "doc_e2e_101",
            "storage_path": "/tmp/sample_contract.pdf",
            "file_extension": ".pdf",
            "mime_type": "application/pdf",
            "page_count": 1,
            "pages": [
                {
                    "page_number": 1,
                    "text": "Contract terms and conditions.",
                }
            ],
            "tables": [],
            "metadata": {},
            "parsing_status": "SUCCESS",
        }

    if name == "classify_document":
        return {
            "document_id": "doc_e2e_101",
            "document_type": "CONTRACT",
            "confidence_score": 0.99,
        }

    if name == "extract_structured_data":
        return {
            "document_id": "doc_e2e_101",
            "header": {},
            "seller": {},
            "buyer": {},
            "line_items": [],
            "taxes": {},
            "payment": {},
            "totals": {},
            "additional_fields": {},
            "metadata": {
                "document_type": "CONTRACT",
                "extracted_fields_count": 0,
                "tables_extracted": 0,
                "processing_time_ms": 0.0,
            },
        }

    if name == "validate_document":
        return {
            "document_id": "doc_e2e_101",
            "document_type": "CONTRACT",
            "is_valid": True,
            "status": "VALID",
            "issues": [],
            "error_count": 0,
            "warning_count": 0,
            "processing_time_ms": 0.0,
        }

    if name == "prepare_embedding_content":
        return {
            "document_id": "doc_e2e_101",
            "workspace_id": "ws_enterprise",
            "document_type": "CONTRACT",
            "full_semantic_text": "Contract terms and conditions.",
            "chunks": [],
            "metadata": {
                "document_id": "doc_e2e_101",
                "workspace_id": "ws_enterprise",
                "document_type": "CONTRACT",
                "total_chunks": 0,
                "total_characters": 31,
                "processing_time_ms": 0.0,
            },
        }

    if name == "generate_embeddings":
        return {
            "document_id": "doc_e2e_101",
            "workspace_id": "ws_enterprise",
            "document_type": "CONTRACT",
            "embeddings": [],
            "metadata": {
                "document_id": "doc_e2e_101",
                "workspace_id": "ws_enterprise",
                "document_type": "CONTRACT",
                "embedding_model": "test-model",
                "total_chunks_processed": 0,
                "vector_dimensions": 768,
                "processing_time_ms": 10.0,
            },
        }

    if name == "store_vectors":
        return {
            "document_id": "doc_e2e_101",
            "workspace_id": "ws_enterprise",
            "status": "INDEXED",
        }

    if name == "query_documents":
        return {
            "answer": "The contract total value is $10,000 with Acme Corp.",
            "source_chunks": [],
        }

    return {
        "document_id": "doc_e2e_101",
        "workspace_id": "ws_enterprise",
        "status": "SUCCESS",
    }


@pytest.fixture
def mock_pipeline_tool_registry():
    """Create a mocked registry without instantiating real tools."""

    registry = MagicMock()

    def get_tool(name: str):
        tool = MagicMock()
        tool.name = name
        tool.run = AsyncMock(
            return_value=ToolResult(
                success=True,
                data=_create_mock_stage_data(name),
                execution_time_ms=12.5,
            )
        )
        return tool

    registry.get.side_effect = get_tool
    return registry


@pytest.fixture
def e2e_client(mock_pipeline_tool_registry):
    """Create FastAPI client using AgentRuntime with mocked tools."""

    runtime = AgentRuntime(
        registry=mock_pipeline_tool_registry
    )

    app = FastAPI()
    app.include_router(documents_router)
    app.include_router(query_router)

    app.dependency_overrides[get_runtime] = lambda: runtime

    return TestClient(app)


def test_e2e_full_ingestion_pipeline_success(
    e2e_client,
    tmp_path,
):
    """Verify API request flows through all 8 ingestion stages."""

    sample_file = tmp_path / "sample_contract.pdf"
    sample_file.write_bytes(b"contract test document")

    response = e2e_client.post(
        "/documents/ingest",
        json={
            "workspace_id": "ws_enterprise",
            "file_path": str(sample_file),
            "original_filename": "sample_contract.pdf",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["mode"] == "DOCUMENT_INGESTION"
    assert data["workspace_id"] == "ws_enterprise"
    assert data["document_id"] == "doc_e2e_101"
    assert data["failed_stage"] is None
    assert len(data["stages"]) == 8

    stage_names = [
        stage["tool_name"]
        for stage in data["stages"]
    ]

    assert stage_names == [
        "upload_document",
        "parse_document",
        "classify_document",
        "extract_structured_data",
        "validate_document",
        "prepare_embedding_content",
        "generate_embeddings",
        "store_vectors",
    ]


def test_e2e_ingestion_halts_on_validation_failure(
    mock_pipeline_tool_registry,
    tmp_path,
):
    """Verify validation failure stops downstream stages."""

    sample_file = tmp_path / "sample_contract.pdf"
    sample_file.write_bytes(b"contract test document")

    def get_tool(name: str):
        tool = MagicMock()
        tool.name = name

        if name == "validate_document":
            tool.run = AsyncMock(
                return_value=ToolResult(
                    success=True,
                    data={
                        "document_id": "doc_e2e_101",
                        "document_type": "CONTRACT",
                        "is_valid": False,
                        "status": "INVALID",
                        "issues": [],
                        "error_count": 1,
                        "warning_count": 0,
                        "processing_time_ms": 10.0,
                    },
                )
            )
        else:
            tool.run = AsyncMock(
                return_value=ToolResult(
                    success=True,
                    data=_create_mock_stage_data(name),
                    execution_time_ms=10.0,
                )
            )

        return tool

    mock_pipeline_tool_registry.get.side_effect = get_tool

    runtime = AgentRuntime(
        registry=mock_pipeline_tool_registry
    )

    app = FastAPI()
    app.include_router(documents_router)

    app.dependency_overrides[get_runtime] = lambda: runtime

    client = TestClient(app)

    response = client.post(
        "/documents/ingest",
        json={
            "workspace_id": "ws_enterprise",
            "file_path": str(sample_file),
            "original_filename": "sample_contract.pdf",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is False
    assert data["failed_stage"] == "validate_document"
    assert len(data["stages"]) == 5

    executed_stages = [
        stage["tool_name"]
        for stage in data["stages"]
    ]

    assert "prepare_embedding_content" not in executed_stages
    assert "generate_embeddings" not in executed_stages
    assert "store_vectors" not in executed_stages


def test_e2e_query_pipeline_scope_preservation(e2e_client):
    """Verify query reaches the runtime with explicit document scope."""

    response = e2e_client.post(
        "/query",
        json={
            "workspace_id": "ws_enterprise",
            "selected_document_ids": ["doc_e2e_101"],
            "query": "What is the total contract value?",
            "top_k": 5,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["mode"] == "QUERY"
    assert data["workspace_id"] == "ws_enterprise"
    assert "total value is $10,000" in data["final_output"]["answer"]
    assert len(data["stages"]) == 1
    assert data["stages"][0]["tool_name"] == "query_documents"


def test_e2e_query_pipeline_rejects_missing_document_scope(
    e2e_client,
):
    """Verify queries without explicit document scope are rejected."""

    response = e2e_client.post(
        "/query",
        json={
            "workspace_id": "ws_enterprise",
            "selected_document_ids": [],
            "query": "Global search prompt",
        },
    )

    assert response.status_code in (400, 422)


def test_e2e_sanitized_internal_error_handling(
    mock_pipeline_tool_registry,
    tmp_path,
):
    """Verify internal exceptions are not exposed to API clients."""

    sample_file = tmp_path / "sample.pdf"
    sample_file.write_bytes(b"test document")

    def get_tool(name: str):
        tool = MagicMock()
        tool.name = name

        if name == "upload_document":
            tool.run = AsyncMock(
                side_effect=RuntimeError(
                    "CRITICAL_DB_SECRET_KEY_12345 "
                    "/internal/database/path"
                )
            )
        else:
            tool.run = AsyncMock(
                return_value=ToolResult(
                    success=True,
                    data=_create_mock_stage_data(name),
                    execution_time_ms=10.0,
                )
            )

        return tool

    mock_pipeline_tool_registry.get.side_effect = get_tool

    runtime = AgentRuntime(
        registry=mock_pipeline_tool_registry
    )

    app = FastAPI()
    app.include_router(documents_router)

    app.dependency_overrides[get_runtime] = lambda: runtime

    client = TestClient(app)

    response = client.post(
        "/documents/ingest",
        json={
            "workspace_id": "ws_enterprise",
            "file_path": str(sample_file),
            "original_filename": "sample.pdf",
        },
    )

    assert response.status_code in (200, 500)

    data = response.json()

    assert data["success"] is False
    assert data["mode"] == "DOCUMENT_INGESTION"
    assert data["failed_stage"] is None

    assert "CRITICAL_DB_SECRET_KEY_12345" not in str(data)
    assert "/internal/database/path" not in str(data)