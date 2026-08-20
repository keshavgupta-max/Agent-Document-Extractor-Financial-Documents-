"""Domain-specific exception hierarchy for the Document Parsing Engine."""

from exceptions import BaseAgentException


class ParserError(BaseAgentException):
    """Base exception for all document parser failures."""

    pass


class UnsupportedDocumentType(ParserError):
    """Raised when an unsupported file extension or format is provided."""

    pass


class DocumentNotFound(ParserError):
    """Raised when the requested document file does not exist at storage location."""

    pass


class CorruptedDocument(ParserError):
    """Raised when a document cannot be read or parsed due to corruption."""

    pass


class EmptyDocument(ParserError):
    """Raised when a document is read successfully but contains zero content."""

    pass


class ParserExecutionError(ParserError):
    """Raised when an internal error occurs during specific parser execution."""

    pass