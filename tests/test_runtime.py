"""Phase 15 Runtime Orchestrator Integration Tests."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from core.runtime import AgentRuntime
from core.runtime_models import (
    ExecutionMode,
    IngestionPipelineInput,
    QueryPipelineInput,
)
from core.tool_result import ToolResult


def _create_mock_parsed_document_dict():
    """Returns a valid dictionary structure matching ParsedDocument schema."""
    return {
        "document_id": "test_doc_123",
        "storage_path": "/tmp/test.pdf",
        "file_extension": ".pdf",
        "mime_type": "application/pdf",
        "page_count": 1,
        "pages": [
            {
                "page_number": 1,
                "text": "Sample document text content.",
            }
        ],
        "tables": [],
        "metadata": {},
        "parsing_status": "SUCCESS",
    }


def _create_mock_stage_data(name: str):
    """Generates mock stage outputs matching the actual Pydantic stage schemas."""

    if name == "upload_document":
        return {
            "document_id": "test_doc_123",
            "file_path": "/tmp/test.pdf",
            "storage_path": "/tmp/test.pdf",
            "stored_filename": "test_doc_123.pdf",
            "workspace_id": "ws_test",
            "status": "SUCCESS",
        }

    if name == "parse_document":
        return _create_mock_parsed_document_dict()

    if name == "classify_document":
        return {
            "document_id": "test_doc_123",
            "document_type": "INVOICE",
            "confidence_score": 0.98,
        }

    if name == "extract_structured_data":
        return {
            "document_id": "test_doc_123",
            "header": {},
            "seller": {},
            "buyer": {},
            "line_items": [],
            "taxes": {},
            "payment": {},
            "totals": {},
            "additional_fields": {},
            "metadata": {
                "document_type": "INVOICE",
                "extracted_fields_count": 0,
                "tables_extracted": 0,
                "processing_time_ms": 0.0,
            },
        }

    if name == "validate_document":
        return {
            "document_id": "test_doc_123",
            "document_type": "INVOICE",
            "is_valid": True,
            "status": "VALID",
            "issues": [],
            "error_count": 0,
            "warning_count": 0,
            "processing_time_ms": 10.0,
        }

    if name == "prepare_embedding_content":
        return {
            "document_id": "test_doc_123",
            "workspace_id": "ws_test",
            "document_type": "INVOICE",
            "full_semantic_text": "Sample document text content.",
            "chunks": [],
            "metadata": {
                "document_id": "test_doc_123",
                "workspace_id": "ws_test",
                "document_type": "INVOICE",
                "total_chunks": 0,
                "total_characters": 29,
                "processing_time_ms": 10.0,
            },
        }

    if name == "generate_embeddings":
        return {
            "document_id": "test_doc_123",
            "workspace_id": "ws_test",
            "document_type": "INVOICE",
            "embeddings": [],
            "metadata": {
                "document_id": "test_doc_123",
                "workspace_id": "ws_test",
                "document_type": "INVOICE",
                "embedding_model": "test-model",
                "total_chunks_processed": 0,
                "vector_dimensions": 768,
                "processing_time_ms": 10.0,
            },
        }

    if name == "store_vectors":
        return {
            "document_id": "test_doc_123",
            "workspace_id": "ws_test",
            "status": "SUCCESS",
        }

    return {
        "document_id": "test_doc_123",
        "workspace_id": "ws_test",
        "document_type": "INVOICE",
        "status": "SUCCESS",
    }


@pytest.fixture
def mock_registry():
    """Returns a mock ToolRegistry providing mock tool behavior."""
    registry = MagicMock()

    def get_tool(name: str):
        tool = MagicMock()
        tool.name = name

        res_data = _create_mock_stage_data(name)

        tool.run = AsyncMock(
            return_value=ToolResult(
                success=True,
                data=res_data,
                execution_time_ms=10.0,
            )
        )

        return tool

    registry.get.side_effect = get_tool
    return registry


@pytest.mark.asyncio
async def test_successful_ingestion_pipeline(mock_registry, tmp_path):
    """Test full ingestion pipeline executes all 8 stages successfully."""

    sample_file = tmp_path / "sample.pdf"
    sample_file.write_bytes(b"test document content")

    runtime = AgentRuntime(registry=mock_registry)

    payload = IngestionPipelineInput(
        workspace_id="ws_test",
        file_path=str(sample_file),
        original_filename="sample.pdf",
    )

    result = await runtime.run_ingestion_pipeline(payload)

    assert result.success is True, (
        f"Pipeline failed with error: {result.error_message}"
    )
    assert result.mode == ExecutionMode.DOCUMENT_INGESTION
    assert result.workspace_id == "ws_test"
    assert result.document_id == "test_doc_123"
    assert len(result.stages) == 8
    assert result.failed_stage is None


@pytest.mark.asyncio
async def test_parser_failure_short_circuits_downstream(
    mock_registry,
    tmp_path,
):
    """Test parser stage failure halts execution and skips remaining tools."""

    bad_file = tmp_path / "bad.pdf"
    bad_file.write_bytes(b"invalid test document")

    parser_mock = MagicMock()
    parser_mock.name = "parse_document"
    parser_mock.run = AsyncMock(
        return_value=ToolResult(
            success=False,
            error="PDF Corrupted: Unable to read xref table.",
        )
    )

    def get_tool_with_failing_parser(name: str):
        if name == "parse_document":
            return parser_mock

        tool = MagicMock()
        tool.name = name
        tool.run = AsyncMock(
            return_value=ToolResult(
                success=True,
                data=_create_mock_stage_data(name),
                execution_time_ms=10.0,
            )
        )

        return tool

    mock_registry.get.side_effect = get_tool_with_failing_parser

    runtime = AgentRuntime(registry=mock_registry)

    payload = IngestionPipelineInput(
        workspace_id="ws_test",
        file_path=str(bad_file),
        original_filename="bad.pdf",
    )

    result = await runtime.run_ingestion_pipeline(payload)

    assert result.success is False
    assert result.failed_stage == "parse_document"
    assert len(result.stages) == 2

    executed_names = [s.tool_name for s in result.stages]

    assert "upload_document" in executed_names
    assert "parse_document" in executed_names
    assert "classify_document" not in executed_names


@pytest.mark.asyncio
async def test_validation_failure_stops_embedding_and_storage(
    mock_registry,
    tmp_path,
):
    """Test validation failure prevents embedding prep, embedding, and storage."""

    invoice_file = tmp_path / "invoice.pdf"
    invoice_file.write_bytes(b"test invoice document")

    val_mock = MagicMock()
    val_mock.name = "validate_document"
    val_mock.run = AsyncMock(
        return_value=ToolResult(
            success=True,
            data={
                "is_valid": False,
                "errors": ["Invoice total math mismatch"],
            },
            execution_time_ms=10.0,
        )
    )

    def get_tool_with_invalid_validation(name: str):
        if name == "validate_document":
            return val_mock

        tool = MagicMock()
        tool.name = name
        tool.run = AsyncMock(
            return_value=ToolResult(
                success=True,
                data=_create_mock_stage_data(name),
                execution_time_ms=10.0,
            )
        )

        return tool

    mock_registry.get.side_effect = get_tool_with_invalid_validation

    runtime = AgentRuntime(registry=mock_registry)

    payload = IngestionPipelineInput(
        workspace_id="ws_test",
        file_path=str(invoice_file),
        original_filename="invoice.pdf",
    )

    result = await runtime.run_ingestion_pipeline(payload)

    assert result.success is False
    assert result.failed_stage == "validate_document"
    assert len(result.stages) == 5

    executed_names = [s.tool_name for s in result.stages]

    assert "prepare_embedding_content" not in executed_names
    assert "generate_embeddings" not in executed_names
    assert "store_vectors" not in executed_names


@pytest.mark.asyncio
async def test_query_pipeline_execution(mock_registry):
    """Test query pipeline execution invokes QueryTool directly."""

    query_mock = MagicMock()
    query_mock.name = "query_documents"
    query_mock.run = AsyncMock(
        return_value=ToolResult(
            success=True,
            data={
                "answer": "The invoice total is $500.",
                "source_chunks": [],
            },
            execution_time_ms=45.0,
        )
    )

    mock_registry.get.side_effect = (
        lambda name: query_mock
        if name == "query_documents"
        else MagicMock()
    )

    runtime = AgentRuntime(registry=mock_registry)

    payload = QueryPipelineInput(
        workspace_id="ws_test",
        selected_document_ids=["doc_123"],
        query="What is the invoice total?",
    )

    result = await runtime.run_query_pipeline(payload)

    assert result.success is True
    assert result.mode == ExecutionMode.QUERY
    assert result.workspace_id == "ws_test"
    assert result.final_output["answer"] == "The invoice total is $500."
    assert len(result.stages) == 1
    assert result.stages[0].tool_name == "query_documents"