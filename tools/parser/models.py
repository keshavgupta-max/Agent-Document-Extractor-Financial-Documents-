"""Pydantic data models for the Document Parsing Engine."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PageContent(BaseModel):
    """Represents extracted text content for a single document page or section."""

    page_number: int = Field(..., description="1-based page index")
    text: str = Field(default="", description="Extracted plain text content")


class TableContent(BaseModel):
    """Represents extracted tabular data from a document."""

    table_index: int = Field(..., description="0-based index of table in document")
    page_number: Optional[int] = Field(
        default=None, description="Page number where table is located, if available"
    )
    headers: List[str] = Field(
        default_factory=list, description="Extracted column headers"
    )
    rows: List[List[str]] = Field(
        default_factory=list, description="Extracted table rows as string matrices"
    )


class ImageMetadata(BaseModel):
    """Represents metadata extracted from image files (no OCR)."""

    width: int = Field(..., description="Image width in pixels")
    height: int = Field(..., description="Image height in pixels")
    format: str = Field(..., description="Image format (e.g., PNG, JPEG)")
    size_bytes: int = Field(..., description="File size in bytes")


class ParserInput(BaseModel):
    """Input parameters passed to the Parser Tool."""

    document_id: str = Field(..., description="Unique document UUID identifier")
    storage_path: str = Field(
        ..., description="Full canonical file path on storage media"
    )
    file_extension: str = Field(
        ..., description="File extension including leading dot (e.g., .pdf)"
    )
    mime_type: Optional[str] = Field(
        default=None, description="Optional validated MIME type"
    )


class ParsedDocument(BaseModel):
    """Normalized internal representation of a parsed document."""

    document_id: str = Field(..., description="Unique document UUID identifier")
    storage_path: str = Field(..., description="Storage path of parsed file")
    file_extension: str = Field(..., description="Normalized file extension")
    mime_type: str = Field(default="application/octet-stream", description="MIME type")
    page_count: int = Field(default=0, description="Total number of pages or sections")
    pages: List[PageContent] = Field(
        default_factory=list, description="List of page content objects"
    )
    tables: List[TableContent] = Field(
        default_factory=list, description="List of extracted table objects"
    )
    image_metadata: Optional[ImageMetadata] = Field(
        default=None, description="Image metadata if file is an image"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Basic document properties (e.g., author, title)"
    )
    parsing_status: str = Field(..., description="Status of parsing operation")
    parsing_time_ms: float = Field(
        default=0.0, description="Execution duration in milliseconds"
    )