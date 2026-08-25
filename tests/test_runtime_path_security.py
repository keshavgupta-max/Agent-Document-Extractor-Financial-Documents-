"""Security regression tests for AgentRuntime ingestion source file containment."""

from pathlib import Path
import pytest
from unittest.mock import AsyncMock, MagicMock

from core.runtime import AgentRuntime
from core.runtime_models import ExecutionMode, IngestionPipelineInput
from core.tool_result import ToolResult


@pytest.fixture
def isolated_security_environment(tmp_path: Path):
    """Sets up an isolated test filesystem with staging, project root, and external directories."""
    project_root = tmp_path / "project_app"
    project_root.mkdir(parents=True, exist_ok=True)

    # 1. Approved staging root
    staging_root = project_root / "data" / "staging"
    staging_root.mkdir(parents=True, exist_ok=True)
    valid_staged_file = staging_root / "incoming_invoice.pdf"
    valid_staged_file.write_bytes(b"%PDF-1.4 valid staged invoice")

    # 2. Canonical document storage (must NOT be accessed as source)
    canonical_storage = project_root / "data" / "storage" / "documents" / "ws_alpha"
    canonical_storage.mkdir(parents=True, exist_ok=True)
    stored_doc = canonical_storage / "persisted_contract.pdf"
    stored_doc.write_bytes(b"%PDF-1.4 already persisted doc")

    # 3. Sensitive application files
    env_file = project_root / ".env"
    env_file.write_bytes(b"SECRET_KEY=super_secret_123")

    config_file = project_root / "config.py"
    config_file.write_bytes(b"# Configuration file content")

    git_dir = project_root / ".git"
    git_dir.mkdir(parents=True, exist_ok=True)
    git_head = git_dir / "HEAD"
    git_head.write_bytes(b"ref: refs/heads/main")

    # 4. Outside system directory
    outside_dir = tmp_path / "outside_system"
    outside_dir.mkdir(parents=True, exist_ok=True)
    outside_file = outside_dir / "system_passwords.txt"
    outside_file.write_bytes(b"root:password123")

    def _create_mock_stage_data(name: str):
        if name == "upload_document":
            return {
                "document_id": "doc_test_100",
                "file_path": str(valid_staged_file),
                "storage_path": str(canonical_storage / "doc_test_100.pdf"),
                "stored_filename": "doc_test_100.pdf",
                "workspace_id": "ws_alpha",
                "status": "SUCCESS",
            }
        if name == "parse_document":
            return {
                "document_id": "doc_test_100",
                "storage_path": str(canonical_storage / "doc_test_100.pdf"),
                "file_extension": ".pdf",
                "mime_type": "application/pdf",
                "page_count": 1,
                "pages": [{"page_number": 1, "text": "Invoice text content."}],
                "tables": [],
                "metadata": {},
                "parsing_status": "SUCCESS",
            }
        if name == "classify_document":
            return {"document_id": "doc_test_100", "document_type": "INVOICE", "confidence_score": 0.99}
        if name == "extract_structured_data":
            return {
                "document_id": "doc_test_100",
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
                "document_id": "doc_test_100",
                "document_type": "INVOICE",
                "is_valid": True,
                "status": "VALID",
                "issues": [],
                "error_count": 0,
                "warning_count": 0,
                "processing_time_ms": 0.0,
            }
        if name == "prepare_embedding_content":
            return {
                "document_id": "doc_test_100",
                "workspace_id": "ws_alpha",
                "document_type": "INVOICE",
                "full_semantic_text": "Invoice text content.",
                "chunks": [],
                "metadata": {
                    "document_id": "doc_test_100",
                    "workspace_id": "ws_alpha",
                    "document_type": "INVOICE",
                    "total_chunks": 0,
                    "total_characters": 21,
                    "processing_time_ms": 0.0,
                },
            }
        if name == "generate_embeddings":
            return {
                "document_id": "doc_test_100",
                "workspace_id": "ws_alpha",
                "document_type": "INVOICE",
                "embeddings": [],
                "metadata": {
                    "document_id": "doc_test_100",
                    "workspace_id": "ws_alpha",
                    "document_type": "INVOICE",
                    "embedding_model": "test-model",
                    "total_chunks_processed": 0,
                    "vector_dimensions": 768,
                    "processing_time_ms": 10.0,
                },
            }
        if name == "store_vectors":
            return {"document_id": "doc_test_100", "workspace_id": "ws_alpha", "status": "INDEXED"}
        return {"document_id": "doc_test_100", "workspace_id": "ws_alpha", "status": "SUCCESS"}

    mock_registry = MagicMock()
    mock_registry.get.side_effect = lambda name: MagicMock(
        name=name,
        run=AsyncMock(
            return_value=ToolResult(
                success=True,
                data=_create_mock_stage_data(name),
                execution_time_ms=5.0,
            )
        ),
    )

    runtime = AgentRuntime(registry=mock_registry, staging_root=staging_root)

    return {
        "runtime": runtime,
        "staging_root": staging_root,
        "valid_staged_file": valid_staged_file,
        "stored_doc": stored_doc,
        "env_file": env_file,
        "config_file": config_file,
        "git_head": git_head,
        "outside_file": outside_file,
    }


@pytest.mark.asyncio
async def test_file_inside_staging_is_accepted(isolated_security_environment):
    """Test 1: File inside approved staging directory is accepted and successfully executed."""
    env = isolated_security_environment
    payload = IngestionPipelineInput(
        workspace_id="ws_alpha",
        file_path=str(env["valid_staged_file"]),
        original_filename="incoming_invoice.pdf",
    )

    result = await env["runtime"].run_ingestion_pipeline(payload)

    # Explicit positive assertions
    assert result.success is True
    assert result.mode == ExecutionMode.DOCUMENT_INGESTION
    assert result.workspace_id == "ws_alpha"
    assert result.document_id == "doc_test_100"
    assert result.failed_stage is None
    assert len(result.stages) == 8
    assert result.stages[0].tool_name == "upload_document"
    assert result.stages[0].success is True


@pytest.mark.asyncio
async def test_file_outside_staging_is_rejected(isolated_security_environment):
    """Test 2: File outside approved staging root is rejected."""
    env = isolated_security_environment
    payload = IngestionPipelineInput(
        workspace_id="ws_alpha",
        file_path=str(env["outside_file"]),
        original_filename="system_passwords.txt",
    )

    result = await env["runtime"].run_ingestion_pipeline(payload)
    assert result.success is False
    assert result.failed_stage == "upload_document"


@pytest.mark.asyncio
async def test_absolute_path_outside_staging_rejected(isolated_security_environment):
    """Test 3: Absolute path outside staging boundary is rejected."""
    env = isolated_security_environment
    payload = IngestionPipelineInput(
        workspace_id="ws_alpha",
        file_path=str(env["outside_file"].resolve()),
        original_filename="system_passwords.txt",
    )

    result = await env["runtime"].run_ingestion_pipeline(payload)
    assert result.success is False
    assert result.failed_stage == "upload_document"


@pytest.mark.asyncio
async def test_dot_dot_traversal_escaping_staging_rejected(isolated_security_environment):
    """Test 4: ../ traversal escaping staging boundary is rejected."""
    env = isolated_security_environment
    traversal_path = str(env["staging_root"] / ".." / ".." / "outside_system" / "system_passwords.txt")

    payload = IngestionPipelineInput(
        workspace_id="ws_alpha",
        file_path=traversal_path,
        original_filename="system_passwords.txt",
    )

    result = await env["runtime"].run_ingestion_pipeline(payload)
    assert result.success is False
    assert result.failed_stage == "upload_document"


@pytest.mark.asyncio
async def test_nested_traversal_escaping_staging_rejected(isolated_security_environment):
    """Test 5: Deeply nested traversal escaping staging boundary is rejected."""
    env = isolated_security_environment
    nested_path = str(
        env["staging_root"] / "subdir" / "nested" / ".." / ".." / ".." / ".." / "outside_system" / "system_passwords.txt"
    )

    payload = IngestionPipelineInput(
        workspace_id="ws_alpha",
        file_path=nested_path,
        original_filename="system_passwords.txt",
    )

    result = await env["runtime"].run_ingestion_pipeline(payload)
    assert result.success is False
    assert result.failed_stage == "upload_document"


@pytest.mark.asyncio
async def test_directory_path_rejected(isolated_security_environment):
    """Test 6: Directory path is rejected."""
    env = isolated_security_environment
    payload = IngestionPipelineInput(
        workspace_id="ws_alpha",
        file_path=str(env["staging_root"]),
        original_filename="staging",
    )

    result = await env["runtime"].run_ingestion_pipeline(payload)
    assert result.success is False
    assert result.failed_stage == "upload_document"


@pytest.mark.asyncio
async def test_nonexistent_path_rejected(isolated_security_environment):
    """Test 7: Nonexistent file returns controlled failure."""
    env = isolated_security_environment
    payload = IngestionPipelineInput(
        workspace_id="ws_alpha",
        file_path=str(env["staging_root"] / "nonexistent_file.pdf"),
        original_filename="nonexistent_file.pdf",
    )

    result = await env["runtime"].run_ingestion_pipeline(payload)
    assert result.success is False
    assert result.failed_stage == "upload_document"


@pytest.mark.asyncio
async def test_config_file_rejected(isolated_security_environment):
    """Test 8: config.py is rejected as a source path."""
    env = isolated_security_environment
    payload = IngestionPipelineInput(
        workspace_id="ws_alpha",
        file_path=str(env["config_file"]),
        original_filename="config.py",
    )

    result = await env["runtime"].run_ingestion_pipeline(payload)
    assert result.success is False
    assert result.failed_stage == "upload_document"


@pytest.mark.asyncio
async def test_env_file_rejected(isolated_security_environment):
    """Test 9: .env file is rejected as a source path."""
    env = isolated_security_environment
    payload = IngestionPipelineInput(
        workspace_id="ws_alpha",
        file_path=str(env["env_file"]),
        original_filename=".env",
    )

    result = await env["runtime"].run_ingestion_pipeline(payload)
    assert result.success is False
    assert result.failed_stage == "upload_document"


@pytest.mark.asyncio
async def test_canonical_storage_file_rejected_as_source(isolated_security_environment):
    """Test 10: Canonical document storage path is rejected as an un-staged source."""
    env = isolated_security_environment
    payload = IngestionPipelineInput(
        workspace_id="ws_alpha",
        file_path=str(env["stored_doc"]),
        original_filename="persisted_contract.pdf",
    )

    result = await env["runtime"].run_ingestion_pipeline(payload)
    assert result.success is False
    assert result.failed_stage == "upload_document"