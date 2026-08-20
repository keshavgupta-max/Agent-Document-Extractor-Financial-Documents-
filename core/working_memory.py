"""Ephemeral Working Memory definition for per-request state tracking."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class WorkingMemory(BaseModel):
    """Temporary in-memory container holding state for a single execution lifecycle.

    Does not connect to databases, persist state across requests, or handle vector storage.
    """

    current_user: Optional[Dict[str, Any]] = Field(
        default=None, description="Metadata and identity of the requesting user"
    )
    selected_documents: List[str] = Field(
        default_factory=list, description="IDs or paths of documents selected for current scope"
    )
    retrieved_chunks: List[Dict[str, Any]] = Field(
        default_factory=list, description="Document context chunks extracted for answer context"
    )
    current_query: Optional[str] = Field(
        default=None, description="Active user prompt or query under evaluation"
    )
    temporary_context: Dict[str, Any] = Field(
        default_factory=dict, description="Scratchpad for runtime calculations and metadata"
    )
    execution_state: str = Field(
        default="IDLE", description="Current execution state marker (e.g., IDLE, READY)"
    )

    def reset(self) -> None:
        """Reset working memory fields to default clean state."""
        self.current_user = None
        self.selected_documents.clear()
        self.retrieved_chunks.clear()
        self.current_query = None
        self.temporary_context.clear()
        self.execution_state = "IDLE"