"""Domain-specific exceptions for the Vector Retrieval Engine."""

from exceptions import BaseAgentException


class VectorRetrievalError(BaseAgentException):
    """Base exception for all vector retrieval operational failures."""

    pass


class InvalidRetrievalInputError(VectorRetrievalError):
    """Raised when input parameters (workspace_id, document_ids, embedding) fail validation."""

    pass


class VectorDatabaseConnectionError(VectorRetrievalError):
    """Raised when connection to local ChromaDB fails."""

    pass


class VectorRetrievalOperationError(VectorRetrievalError):
    """Raised when ChromaDB collection query execution encounters a runtime error."""

    pass