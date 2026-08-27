"""Pydantic v2 data models for the Vector Retrieval Engine (Phase 13)."""

from typing import List, Optional
from pydantic import BaseModel, Field

from tools.vector_retrieval.constants import DEFAULT_TOP_K


class RetainedChunkMetadata(BaseModel):
    """Metadata retained alongside each retrieved semantic text chunk."""

    chunk_id: str = Field(..., description="Unique chunk identifier")
    document_id: str = Field(..., description="Parent document UUID")
    workspace_id: str = Field(..., description="Workspace boundary identifier")
    chunk_index: int = Field(..., description="0-based positional index of chunk in document")
    document_type: str = Field(..., description="Business document classification type")


class RetrievedChunk(BaseModel):
    """Represents an individual text chunk retrieved from vector storage."""

    chunk_id: str = Field(..., description="Unique chunk identifier")
    document_id: str = Field(..., description="Parent document UUID")
    workspace_id: str = Field(..., description="Workspace boundary identifier")
    text_content: str = Field(..., description="Raw text snippet stored in vector database")
    metadata: RetainedChunkMetadata = Field(..., description="Retained source metadata")
    distance: Optional[float] = Field(
        default=None, description="Vector distance measure returned by database"
    )


class VectorRetrievalResult(BaseModel):
    """Structured container holding all retrieved semantic chunks for a query."""

    workspace_id: str = Field(..., description="Workspace boundary identifier")
    selected_document_ids: List[str] = Field(
        ..., description="Explicit document scope evaluated"
    )
    retrieved_chunks: List[RetrievedChunk] = Field(
        default_factory=list, description="Ordered list of matching text chunks"
    )
    total_results: int = Field(..., description="Total count of chunks returned")
    processing_time_ms: float = Field(
        default=0.0, description="Retrieval runtime in milliseconds"
    )


class VectorRetrievalInput(BaseModel):
    """Input payload accepted by VectorRetrievalTool."""

    workspace_id: str = Field(..., description="Workspace boundary identifier")
    selected_document_ids: List[str] = Field(
        ..., description="Explicit list of document UUIDs to search within"
    )
    query_embedding: List[float] = Field(
        ..., description="Dense numerical vector generated for the search query"
    )
    top_k: int = Field(
        default=DEFAULT_TOP_K,
        description="Number of top matching chunks to retrieve",
    )
    query_text: Optional[str] = Field(
    default=None,
    description="Optional raw query text for aggregate intent detection",
    )