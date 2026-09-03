"""Focused regression tests for runtime MIME-type resolution behavior."""

from pathlib import Path
import pytest
from unittest.mock import AsyncMock, MagicMock

from core.runtime import EXTENSION_TO_CANONICAL_MIME, AgentRuntime
from core.runtime_models import IngestionPipelineInput
from core.tool_result import ToolResult


@pytest.mark.parametrize(
    "extension,expected_mime",
    [
        (".csv", "text/csv"),
        (".xls", "application/vnd.ms-excel"),
        (".xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        (".pdf", "application/pdf"),
        (".txt", "text/plain"),
    ],
)
def test_extension_to_canonical_mime_mapping(extension, expected_mime):
    """Verify that canonical MIME types match UploadValidator expectations."""
    assert EXTENSION_TO_CANONICAL_MIME.get(extension) == expected_mime


@pytest.mark.asyncio
async def test_runtime_ingestion_resolves_csv_correctly(tmp_path):
    """Verify that ingestion pipeline passes canonical text/csv for .csv files on all platforms."""
    csv_file = tmp_path / "test_data.csv"
    csv_file.write_text("item,qty,price\nWidget,2,50.00")

    mock_registry = MagicMock()
    captured_upload_input = None

    def get_mock_tool(name: str):
        tool = MagicMock()
        tool.name = name

        async def run_tool(state, input_data):
            nonlocal captured_upload_input
            if name == "upload_document":
                captured_upload_input = input_data
                return ToolResult(
                    success=True,
                    data={
                        "document_id": "doc_csv_1",
                        "storage_path": str(csv_file),
                        "file_extension": ".csv",
                        "mime_type": input_data.mime_type,
                    },
                    execution_time_ms=5.0,
                )
            return ToolResult(success=True, data={"status": "SUCCESS"}, execution_time_ms=5.0)

        tool.run = AsyncMock(side_effect=run_tool)
        return tool

    mock_registry.get.side_effect = get_mock_tool

    runtime = AgentRuntime(registry=mock_registry, staging_root=tmp_path)
    payload = IngestionPipelineInput(
        workspace_id="ws_test",
        file_path=str(csv_file),
        original_filename="test_data.csv",
    )

    await runtime.run_ingestion_pipeline(payload)

    assert captured_upload_input is not None
    assert captured_upload_input.mime_type == "text/csv"


@pytest.mark.asyncio
async def test_runtime_ingestion_unknown_extension_fallback(tmp_path):
    """Verify that genuinely unknown extensions fallback safely without error."""
    unknown_file = tmp_path / "custom_data.xyz123"
    unknown_file.write_bytes(b"binary content")

    mock_registry = MagicMock()
    captured_upload_input = None

    def get_mock_tool(name: str):
        tool = MagicMock()
        tool.name = name

        async def run_tool(state, input_data):
            nonlocal captured_upload_input
            if name == "upload_document":
                captured_upload_input = input_data
                return ToolResult(
                    success=False,
                    error="MIME type validation error",
                    execution_time_ms=5.0,
                )
            return ToolResult(success=True, data={}, execution_time_ms=5.0)

        tool.run = AsyncMock(side_effect=run_tool)
        return tool

    mock_registry.get.side_effect = get_mock_tool

    runtime = AgentRuntime(registry=mock_registry, staging_root=tmp_path)
    payload = IngestionPipelineInput(
        workspace_id="ws_test",
        file_path=str(unknown_file),
        original_filename="custom_data.xyz123",
    )

    result = await runtime.run_ingestion_pipeline(payload)

    assert captured_upload_input is not None
    assert captured_upload_input.mime_type == "application/octet-stream"
    assert result.success is False