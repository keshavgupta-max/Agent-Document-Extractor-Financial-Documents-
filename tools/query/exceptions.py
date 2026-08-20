"""Domain-specific exceptions for the AI Query Engine."""

from exceptions import BaseAgentException


class QueryError(BaseAgentException):
    """Base exception for all query engine operational failures."""

    pass


class InvalidQueryInputError(QueryError):
    """Raised when query inputs fail validation (e.g., empty query, missing document IDs)."""

    pass


class AIProviderError(QueryError):
    """Raised when the downstream AI generation provider API fails or returns an empty answer."""

    pass


class GroundingError(QueryError):
    """Raised when answer generation fails due to context or grounding constraints."""

    pass