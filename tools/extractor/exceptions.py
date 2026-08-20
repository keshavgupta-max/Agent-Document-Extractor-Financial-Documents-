"""Domain-specific exception hierarchy for the Structured Data Extraction Engine."""

from exceptions import BaseAgentException


class ExtractorError(BaseAgentException):
    """Base exception for all document data extraction failures."""

    pass


class UnsupportedExtractionType(ExtractorError):
    """Raised when an extractor is requested for an unsupported document type."""

    pass


class ExtractorExecutionError(ExtractorError):
    """Raised when a specific extractor encounters an unexpected runtime failure."""

    pass