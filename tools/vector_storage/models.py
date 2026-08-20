"""Pydantic v2 data models for the Vector Storage Engine (Phase 12)."""

from typing import List
from pydantic import BaseModel, Field

from tools.embedding.models import GeneratedDocumentEmbeddings
from tools.vector_storage.constants import DEFAULT_COLLECTION_NAME


class VectorStorageResult(BaseModel):
    """Output summary payload produced after persisting document vectors."""

    document_id: str = Field(..., description="Parent document UUID")
    workspace_id: str = Field(..., description="Workspace boundary identifier")
    stored_count: int = Field(..., description="Total number of vectors successfully upserted")
    record_ids: List[str] = Field(
        default_factory=list, description="List of deterministic vector record IDs created or updated"
    )
    collection_name: str = Field(
        default=DEFAULT_COLLECTION_NAME, description="Target ChromaDB collection name"
    )
    processing_time_ms: float = Field(
        default=0.0, description="Persistence execution runtime in milliseconds"
    )


class VectorStorageInput(BaseModel):
    """Input payload accepted by VectorStorageTool, wrapping Phase 11 GeneratedDocumentEmbeddings.
    
    The input model deliberately exposes ONLY the Phase 11 generated embeddings payload.
    It does NOT allow user/request input to specify storage directories or collection names.
    """

    generated_embeddings: GeneratedDocumentEmbeddings = Field(
        ..., description="Generated vector embeddings payload from Phase 11 (Embedding Generation)"
    )