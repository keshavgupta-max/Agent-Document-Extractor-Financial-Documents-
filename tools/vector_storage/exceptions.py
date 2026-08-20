"""Domain-specific exception hierarchy for Vector Storage."""

from exceptions import BaseAgentException


class VectorStorageError(BaseAgentException):
    """Base exception for all vector storage operational failures."""

    pass


class VectorDatabaseConnectionError(VectorStorageError):
    """Raised when local ChromaDB initialization or directory access fails."""

    pass


class VectorStorageOperationError(VectorStorageError):
    """Raised when an upsert or vector indexing operation fails inside ChromaDB."""

    pass


class InvalidVectorDataError(VectorStorageError):
    """Raised when input vector payloads or metadata are invalid or corrupted."""

    pass