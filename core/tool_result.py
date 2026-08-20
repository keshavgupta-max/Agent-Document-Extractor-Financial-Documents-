"""Standardized result wrapper for tool execution outputs."""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    """Standardized result returned by all tools in the system."""

    success: bool = Field(
        ..., description="Indicates whether the tool executed successfully"
    )
    data: Optional[Any] = Field(
        default=None, description="Payload returned by the tool on success"
    )
    error: Optional[str] = Field(
        default=None, description="Human-readable error message if execution failed"
    )
    execution_time_ms: float = Field(
        default=0.0, description="Execution duration in milliseconds"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional context or execution metrics"
    )