"""Pydantic models for document validation inputs, issues, and output reports."""

from typing import List, Optional
from pydantic import BaseModel, Field

from tools.extractor.models import StructuredBusinessDocument


class ValidationIssue(BaseModel):
    """Represents a specific compliance or mathematical validation finding."""

    rule_id: str = Field(..., description="Unique rule code (e.g., VAL_HDR_001)")
    severity: str = Field(..., description="ERROR, WARNING, or INFO")
    field: Optional[str] = Field(default=None, description="Target field name evaluated")
    message: str = Field(..., description="Human-readable description of issue")


class DocumentValidationResult(BaseModel):
    """Output container produced by the Validation Tool."""

    document_id: str = Field(..., description="Unique document UUID")
    document_type: str = Field(..., description="Business document type")
    is_valid: bool = Field(..., description="True if no ERROR severity issues exist")
    status: str = Field(..., description="VALID, VALID_WITH_WARNINGS, or INVALID")
    issues: List[ValidationIssue] = Field(default_factory=list, description="List of findings")
    error_count: int = Field(default=0, description="Count of ERROR severity findings")
    warning_count: int = Field(default=0, description="Count of WARNING severity findings")
    processing_time_ms: float = Field(default=0.0, description="Validation duration in ms")


class ValidationInput(BaseModel):
    """Input payload accepted by the Validation Tool."""

    structured_document: StructuredBusinessDocument = Field(
        ..., description="Structured business document payload from Extractor Tool"
    )