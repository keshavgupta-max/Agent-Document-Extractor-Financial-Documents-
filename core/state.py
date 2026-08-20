"""Strongly typed execution state model shared across Runtime and all tools."""

import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ExecutionTrace(BaseModel):
    """Lightweight audit trace for tracking individual execution steps/tool calls."""

    tool_name: str = Field(..., description="Name of the executed tool or action")
    start_time: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when step execution started",
    )
    end_time: Optional[datetime] = Field(
        default=None, description="UTC timestamp when step execution completed"
    )
    status: str = Field(
        default="RUNNING", description="Status of execution step (e.g., RUNNING, SUCCESS, FAILED)"
    )
    message: Optional[str] = Field(
        default=None, description="Optional diagnostic message or brief execution detail"
    )


class ToolHistoryEntry(BaseModel):
    """Historical record of tool invocation within the current request scope."""

    tool_name: str = Field(..., description="Name of the invoked tool")
    input_args: Dict[str, str] = Field(
        default_factory=dict, description="Safe stringified map of inputs passed to the tool"
    )
    success: bool = Field(..., description="Whether tool execution succeeded")
    error: Optional[str] = Field(
        default=None, description="Error message if execution failed"
    )
    execution_time_ms: float = Field(
        default=0.0, description="Duration of tool execution in milliseconds"
    )


class AgentState(BaseModel):
    """Ephemeral, strongly typed state container for a single request lifecycle.

    Created by Runtime on request start and destroyed when request finishes.
    Holds zero database state, vector store state, or permanent history.
    """

    request_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique request correlation identifier",
    )
    user_id: Optional[str] = Field(
        default=None, description="Identifier of the requesting user"
    )
    workspace_id: Optional[str] = Field(
        default=None, description="Identifier of the workspace or organization scope"
    )
    current_query: Optional[str] = Field(
        default=None, description="Active user prompt or query under processing"
    )
    selected_documents: List[str] = Field(
        default_factory=list,
        description="List of document IDs or paths explicitly selected for scope",
    )
    uploaded_documents: List[str] = Field(
        default_factory=list,
        description="List of newly uploaded document references in request",
    )
    retrieved_chunks: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Extracted textual or vector context chunks relevant to query",
    )
    structured_data: Dict[str, str] = Field(
        default_factory=dict,
        description="Extracted key-value facts or structured domain outputs",
    )
    metadata: Dict[str, str] = Field(
        default_factory=dict,
        description="Arbitrary safe metadata attached to request lifecycle",
    )
    tool_history: List[ToolHistoryEntry] = Field(
        default_factory=list,
        description="Ordered sequence of tool calls performed during request",
    )
    execution_trace: List[ExecutionTrace] = Field(
        default_factory=list,
        description="Chronological log of step-level traces for execution visibility",
    )
    response: Optional[str] = Field(
        default=None, description="Final generated response payload for caller"
    )
    errors: List[str] = Field(
        default_factory=list,
        description="Collected non-fatal or fatal error messages during execution",
    )
    start_time: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp marking request start time",
    )