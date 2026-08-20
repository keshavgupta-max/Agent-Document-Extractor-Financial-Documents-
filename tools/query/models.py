"""Pydantic v2 data models for the AI Query Engine (Phase 14)."""

from typing import List, Optional
from pydantic import BaseModel, Field

from tools.query.constants import DEFAULT_QUERY_MODEL


class QuerySourceChunk(BaseModel):
    """Source context attribution record attached to an AI answer."""

    chunk_id: str = Field(..., description="Unique identifier for the source chunk")
    document_id: str = Field(..., description="Parent document UUID")
    workspace_id: str = Field(..., description="Workspace boundary identifier")
    chunk_index: int = Field(..., description="0-based positional index of chunk in document")
    document_type: str = Field(..., description="Business document classification type")
    snippet: str = Field(..., description="Text content snippet used for grounding")
    distance: Optional[float] = Field(default=None, description="Vector similarity measure")


class QueryResult(BaseModel):
    """Structured output container returned by Phase 14 Query Service."""

    workspace_id: str = Field(..., description="Workspace boundary identifier")
    selected_document_ids: List[str] = Field(..., description="Explicit document scope evaluated")
    query: str = Field(..., description="Original user question")
    answer: str = Field(..., description="Grounded AI response")
    source_chunks: List[QuerySourceChunk] = Field(
        default_factory=list, description="List of retrieved chunks used as context"
    )
    total_sources_retrieved: int = Field(..., description="Count of context chunks retrieved")
    processing_time_ms: float = Field(..., description="Execution runtime in milliseconds")


class QueryInput(BaseModel):
    """Input payload accepted by QueryTool."""

    workspace_id: str = Field(..., description="Workspace boundary identifier")
    selected_document_ids: List[str] = Field(
        ..., description="Explicit list of document UUIDs to search within"
    )
    query: str = Field(..., description="User search query or accounting question")
    top_k: int = Field(default=5, description="Number of top relevant chunks to retrieve")
    model_name: str = Field(
        default=DEFAULT_QUERY_MODEL, description="Target Gemini generation model"
    )