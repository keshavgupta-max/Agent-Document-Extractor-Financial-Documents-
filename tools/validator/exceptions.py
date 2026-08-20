"""Domain-specific exception hierarchy for the Document Validation Engine."""

from exceptions import BaseAgentException


class ValidatorError(BaseAgentException):
    """Base exception for all document validation failures."""

    pass


class InvalidStructuredDocumentError(ValidatorError):
    """Raised when an invalid or missing StructuredBusinessDocument is provided."""

    pass


class ValidationExecutionError(ValidatorError):
    """Raised when an unhandled runtime error occurs during validation execution."""

    pass