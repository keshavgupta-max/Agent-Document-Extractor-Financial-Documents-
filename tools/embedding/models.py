"""Pydantic v2 data models for the Embedding Generation Engine (Phase 11)."""

from typing import List
from pydantic import BaseModel, Field, model_validator

from tools.embedding.constants import DEFAULT_VECTOR_DIMENSIONS
from tools.embedding_prep.models import PreparedDocumentContent


class SingleGeneratedEmbedding(BaseModel):
    """Represents a single vector generated for an isolated semantic text chunk."""

    chunk_id: str = Field(..., description="Unique deterministic identifier for the chunk")
    document_id: str = Field(..., description="Parent document UUID")
    workspace_id: str = Field(..., description="Workspace boundary identifier")
    chunk_index: int = Field(..., description="0-based positional index of chunk in document")
    text_content: str = Field(
        ..., description="Original semantic text content represented by this embedding"
    )
    vector: List[float] = Field(..., description="Dense numerical floating-point embedding vector")
    dimensions: int = Field(
        default=DEFAULT_VECTOR_DIMENSIONS,
        description="Declared vector dimensionality length",
    )

    @model_validator(mode="after")
    def validate_dimension_contract(self) -> "SingleGeneratedEmbedding":
        """Ensures the actual vector length strictly matches the declared dimensions."""
        if len(self.vector) != self.dimensions:
            raise ValueError(
                f"Vector dimension mismatch: vector length is {len(self.vector)}, "
                f"but declared dimensions is {self.dimensions}."
            )
        return self


class EmbeddingGenerationMetadata(BaseModel):
    """Operational metadata regarding the vector embedding generation process."""

    document_id: str = Field(..., description="Parent document UUID")
    workspace_id: str = Field(..., description="Workspace boundary identifier")
    document_type: str = Field(..., description="Business document classification type")
    original_filename: str = Field(
        default="Unnamed Document", description="Original uploaded filename"
    )
    embedding_model: str = Field(..., description="Name/identifier of the embedding provider model used")
    total_chunks_processed: int = Field(..., description="Total count of text chunks converted to vectors")
    vector_dimensions: int = Field(
        default=DEFAULT_VECTOR_DIMENSIONS,
        description="Dimensionality of generated vectors",
    )
    processing_time_ms: float = Field(default=0.0, description="Embedding generation runtime in ms")


class GeneratedDocumentEmbeddings(BaseModel):
    """Container holding all generated embedding vectors and metadata for a single document."""

    document_id: str = Field(..., description="Parent document UUID")
    workspace_id: str = Field(..., description="Workspace boundary identifier")
    original_filename: str = Field(
        default="Unnamed Document", description="Original uploaded filename"
    )
    document_type: str = Field(..., description="Business document classification type")
    embeddings: List[SingleGeneratedEmbedding] = Field(
        default_factory=list, description="Collection of generated chunk vectors"
    )
    metadata: EmbeddingGenerationMetadata = Field(..., description="Execution metadata")


class EmbeddingInput(BaseModel):
    """Input payload accepted by the Embedding Tool, consuming Phase 10 PreparedDocumentContent."""

    prepared_content: PreparedDocumentContent = Field(
        ..., description="Prepared semantic content and text chunks from Phase 10 (Embedding Preparation)"
    )