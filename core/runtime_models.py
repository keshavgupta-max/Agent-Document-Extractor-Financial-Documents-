"""Pydantic v2 schemas for Phase 15 Execution Runtime payloads and execution results."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ExecutionMode(str, Enum):
    """Supported pipeline execution modes."""

    DOCUMENT_INGESTION = "DOCUMENT_INGESTION"
    QUERY = "QUERY"


class IngestionPipelineInput(BaseModel):
    """Input payload to trigger a full document ingestion pipeline execution."""

    workspace_id: str = Field(..., description="Target workspace boundary identifier")
    file_path: str = Field(..., description="Path to the document file to ingest")
    original_filename: str = Field(..., description="Original name of the uploaded file")


class QueryPipelineInput(BaseModel):
    """Input payload to trigger a grounded query pipeline execution."""

    workspace_id: str = Field(..., description="Target workspace boundary identifier")
    selected_document_ids: List[str] = Field(
        ..., description="Explicit document UUID scope to retrieve context from"
    )
    query: str = Field(..., description="User query or accounting question")
    top_k: int = Field(default=5, description="Number of top context chunks to retrieve")


class PipelineStageExecution(BaseModel):
    """Audit record for an individual tool stage execution in the pipeline."""

    tool_name: str = Field(..., description="Name of the tool executed")
    success: bool = Field(..., description="Whether the stage completed successfully")
    execution_time_ms: float = Field(default=0.0, description="Stage execution time in ms")
    error: Optional[str] = Field(default=None, description="Sanitized failure message if applicable")


class PipelineExecutionResult(BaseModel):
    """Final aggregated result returned after running the pipeline orchestrator."""

    success: bool = Field(..., description="Overall pipeline execution status")
    mode: ExecutionMode = Field(..., description="Mode executed (INGESTION or QUERY)")
    workspace_id: str = Field(..., description="Workspace ID for execution context")
    document_id: Optional[str] = Field(default=None, description="Document ID processed if ingestion")
    final_output: Optional[Dict[str, Any]] = Field(
        default=None, description="Output payload from the final successful stage"
    )
    failed_stage: Optional[str] = Field(default=None, description="Name of the stage that failed, if any")
    stages: List[PipelineStageExecution] = Field(
        default_factory=list, description="Step-by-step audit records for executed tools"
    )
    total_execution_time_ms: float = Field(
        default=0.0, description="Total pipeline execution time in ms"
    )
    error_message: Optional[str] = Field(
        default=None, description="Top-level sanitized failure description"
    )