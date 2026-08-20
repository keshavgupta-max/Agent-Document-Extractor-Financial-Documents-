"""Domain-specific exception hierarchy for the Document Classification Engine."""

from exceptions import BaseAgentException


class ClassifierError(BaseAgentException):
    """Base exception for all document classification failures."""

    pass


class InvalidParsedDocumentError(ClassifierError):
    """Raised when an invalid or empty ParsedDocument model is provided for classification."""

    pass


class ClassificationFailedError(ClassifierError):
    """Raised when rule evaluation encounters an unexpected runtime failure."""

    pass