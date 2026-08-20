"""Pydantic v2 data models for Embedding Preparation stage."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from tools.extractor.models import StructuredBusinessDocument
from tools.parser.models import ParsedDocument


class PreparedChunk(BaseModel):
    """Represents an isolated, semantically formatted chunk ready for vectorization."""

    chunk_id: str = Field(..., description="Unique deterministic identifier for the chunk")
    document_id: str = Field(..., description="Parent document UUID")
    workspace_id: str = Field(..., description="Workspace boundary identifier")
    chunk_index: int = Field(..., description="0-based positional index of chunk in document")
    text_content: str = Field(..., description="Semantic text string ready for embedding")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Filterable vector metadata (workspace_id, document_id, document_type, etc.)",
    )


class EmbeddingPrepMetadata(BaseModel):
    """Metadata describing the preparation result."""

    document_id: str = Field(..., description="Parent document UUID")
    workspace_id: str = Field(..., description="Workspace boundary identifier")
    document_type: str = Field(..., description="Business classification type")
    total_chunks: int = Field(..., description="Total number of chunks generated")
    total_characters: int = Field(..., description="Total character count of formatted content")
    processing_time_ms: float = Field(default=0.0, description="Execution duration in ms")


class PreparedDocumentContent(BaseModel):
    """Complete output payload containing chunks and preparation metadata."""

    document_id: str = Field(..., description="Parent document UUID")
    workspace_id: str = Field(..., description="Workspace boundary identifier")
    document_type: str = Field(..., description="Business classification type")
    full_semantic_text: str = Field(..., description="Aggregated semantic text representation")
    chunks: List[PreparedChunk] = Field(default_factory=list, description="List of text chunks")
    metadata: EmbeddingPrepMetadata = Field(..., description="Execution metadata")


class EmbeddingPrepInput(BaseModel):
    """Input payload accepted by the Embedding Prep Tool."""

    workspace_id: str = Field(..., description="Workspace boundary identifier")
    structured_document: StructuredBusinessDocument = Field(
        ..., description="Structured extracted document payload"
    )
    parsed_document: Optional[ParsedDocument] = Field(
        default=None, description="Optional original parsed document for supplementary raw text"
    )
    is_valid: bool = Field(
        default=True, description="Validation status flag from Validation Engine"
    )