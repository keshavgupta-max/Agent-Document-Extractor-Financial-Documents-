"""Domain-specific exceptions for Embedding Preparation."""

from exceptions import BaseAgentException


class EmbeddingPrepError(BaseAgentException):
    """Base exception for all embedding preparation failures."""

    pass


class InvalidInputForPreparationError(EmbeddingPrepError):
    """Raised when provided input payloads are missing or incomplete."""

    pass


class ChunkingExecutionError(EmbeddingPrepError):
    """Raised when unexpected errors occur during semantic text chunking."""

    pass