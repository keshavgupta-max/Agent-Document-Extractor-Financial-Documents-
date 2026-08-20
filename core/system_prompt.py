"""System Prompt Loader component."""

from pathlib import Path
from exceptions import SystemPromptLoadError
from logger import logger


class SystemPromptLoader:
    """Handles secure and safe reading of system prompt files from disk."""

    def __init__(self, prompt_path: str) -> None:
        self._prompt_path = Path(prompt_path)

    def load(self) -> str:
        """Reads and returns system prompt text.

        Raises:
            SystemPromptLoadError: If file is missing, unreadable, or empty.
        """
        if not self._prompt_path.exists():
            error_msg = f"System prompt file not found at path: {self._prompt_path}"
            logger.error(error_msg)
            raise SystemPromptLoadError(error_msg)

        try:
            content = self._prompt_path.read_text(encoding="utf-8").strip()
            if not content:
                error_msg = f"System prompt file at {self._prompt_path} is empty."
                logger.error(error_msg)
                raise SystemPromptLoadError(error_msg)
            
            logger.debug("System prompt successfully loaded from %s", self._prompt_path)
            return content
        except Exception as exc:
            if isinstance(exc, SystemPromptLoadError):
                raise
            error_msg = f"Failed to read system prompt file: {str(exc)}"
            logger.error(error_msg)
            raise SystemPromptLoadError(error_msg) from exc