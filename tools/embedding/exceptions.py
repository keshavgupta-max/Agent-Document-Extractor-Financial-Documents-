"""Domain-specific exception hierarchy for the Embedding Generation Engine."""

from exceptions import BaseAgentException


class EmbeddingGenerationError(BaseAgentException):
    """Base exception for all embedding generation failures."""

    pass


class InvalidPreparedContentError(EmbeddingGenerationError):
    """Raised when the input PreparedDocumentContent payload is invalid, empty, or missing chunks."""

    pass


class ProviderAPIError(EmbeddingGenerationError):
    """Raised when the downstream embedding provider API call fails or encounters a network error."""

    pass


class EmbeddingDimensionMismatchError(EmbeddingGenerationError):
    """Raised when generated vectors do not match expected model output dimensions."""

    pass