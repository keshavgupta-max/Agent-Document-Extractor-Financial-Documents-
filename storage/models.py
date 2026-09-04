"""Strongly typed data models for Storage Manager inputs and outputs."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field


class StoragePayload(BaseModel):
    """Payload provided to Storage Manager to initiate file persistence."""

    document_id: str = Field(..., description="Unique document UUID identifier")
    stored_filename: str = Field(..., description="Secure filename generated for storage")
    original_filename: str = Field(..., description="Sanitized original filename")
    workspace_id: str = Field(..., description="Target workspace scope identifier")
    content: bytes = Field(..., description="Raw binary content to persist")
    mime_type: str = Field(..., description="Validated MIME type of file")


class StorageResult(BaseModel):
    """Result returned by Storage Manager after successful file persistence."""

    document_id: str = Field(..., description="Unique document UUID identifier")
    stored_filename: str = Field(..., description="Secure filename used on disk/cloud")
    original_filename: str = Field(..., description="Sanitized original filename")
    storage_path: str = Field(..., description="Full canonical path or URI of stored file")
    workspace_id: str = Field(..., description="Workspace identifier")
    file_size: int = Field(..., description="Exact size of written file in bytes")
    mime_type: str = Field(..., description="Validated MIME type")
    storage_status: str = Field(..., description="Status of storage operation")
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="UTC ISO timestamp of storage completion",
    )