"""Pydantic data models for the Document Classification Engine."""

from typing import Any, Dict, List
from pydantic import BaseModel, Field

from tools.parser.models import ParsedDocument


class ClassifierInput(BaseModel):
    """Input payload accepted by the Classifier Tool."""

    parsed_document: ParsedDocument = Field(
        ..., description="Parsed document representation containing extracted text and tables"
    )


class DocumentClassification(BaseModel):
    """Standardized output model returned after document classification."""

    document_id: str = Field(..., description="Unique document UUID identifier")
    document_type: str = Field(
        ..., description="Identified business document category (e.g., GST Invoice, Bank Statement)"
    )
    confidence: float = Field(
        ..., description="Rule evaluation confidence score between 0.0 and 1.0"
    )
    matched_rules: List[str] = Field(
        default_factory=list, description="List of rule identifiers or keyword signals matched"
    )
    reason: str = Field(
        ..., description="Human-readable explanation of why this classification was assigned"
    )
    processing_time_ms: float = Field(
        default=0.0, description="Rule evaluation duration in milliseconds"
    )