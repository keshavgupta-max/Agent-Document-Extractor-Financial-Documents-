"""Pydantic models and data structures for the Upload Tool."""

from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class UploadInput(BaseModel):
    """Input payload accepted by the Upload Tool."""

    filename: str = Field(..., description="Original filename provided by client")
    content: bytes = Field(..., description="Raw file byte contents")
    mime_type: str = Field(..., description="MIME type declared or detected")
    workspace_id: str = Field(..., description="Workspace ID where file is being uploaded")
    uploaded_by: str = Field(..., description="User ID or identity of uploader")
    tags: List[str] = Field(default_factory=list, description="Optional metadata tags")
    notes: Optional[str] = Field(default=None, description="Optional upload notes")
    source: Optional[str] = Field(default=None, description="Source origin (e.g., API, Portal)")


class StorageRequest(BaseModel):
    """Prepared request payload to be handed off to Storage Manager."""

    document_id: str = Field(
        ...,
        description="Generated unique document identifier",
    )
    stored_filename: str = Field(
        ...,
        description="Sanitized unique filename on disk/cloud",
    )
    original_filename: str = Field(
        ...,
        description="Original uploaded filename",
    )
    workspace_id: str = Field(
        ...,
        description="Target workspace ID",
    )
    content: bytes = Field(
        ...,
        description="Raw bytes to be persisted",
    )
    mime_type: str = Field(
        ...,
        description="Validated MIME type",
    )

class UploadResult(BaseModel):
    """Standardized output metadata returned after successful upload preparation."""

    document_id: str = Field(..., description="Unique generated document identifier")
    original_filename: str = Field(..., description="Sanitized original filename")
    stored_filename: str = Field(..., description="Secure filename generated for storage")
    file_extension: str = Field(..., description="Lowercase file extension including dot")
    mime_type: str = Field(..., description="Validated MIME type")
    technical_file_category: str = Field(
        ..., description="Technical classification (PDF, WORD, IMAGE, SPREADSHEET, TEXT)"
    )
    file_size: int = Field(..., description="File size in bytes")
    upload_status: str = Field(..., description="Current upload status")
    processing_status: str = Field(..., description="Current processing status")
    validation_status: str = Field(..., description="Current validation status")
    upload_timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="UTC ISO format upload timestamp",
    )