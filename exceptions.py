"""Custom exception hierarchy for the Agent runtime."""

class BaseAgentException(Exception):
    """Base exception class for all domain errors within the Agent runtime."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ConfigurationError(BaseAgentException):
    """Raised when application or environment configuration fails validation."""
    pass


class WorkingMemoryError(BaseAgentException):
    """Raised when working memory state management fails."""
    pass


class SystemPromptLoadError(BaseAgentException):
    """Raised when reading or validating the system prompt file fails."""
    pass


class AgentRuntimeError(BaseAgentException):
    """Raised when runtime initialization or execution encounters an unrecoverable state."""
    pass