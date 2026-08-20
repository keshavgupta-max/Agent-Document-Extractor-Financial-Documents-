"""Safe tool execution supervisor."""

import time
from typing import Any, Dict
from pydantic import ValidationError

from core.tool_registry import ToolRegistry
from core.tool_result import ToolResult
from exceptions import BaseAgentException
from logger import logger


class ToolExecutionError(BaseAgentException):
    """Raised when tool execution encounters validation or lookup failure."""
    pass


class ToolExecutor:
    """Handles secure tool invocation, timing, and error handling."""

    def __init__(self, registry: ToolRegistry) -> None:
        self._registry = registry

    async def execute(self, tool_name: str, args: Dict[str, Any]) -> ToolResult:
        """Safely executes a registered tool by name with provided argument payload.

        Returns ToolResult containing success status, payload, or safe error details.
        Never executes unknown code or uses eval().
        """
        tool = self._registry.get(tool_name)
        if not tool:
            logger.warning("Attempted execution of unregistered tool: %s", tool_name)
            return ToolResult(
                success=False,
                error=f"Tool '{tool_name}' is not registered.",
            )

        start_time = time.perf_counter()
        try:
            logger.debug("Executing tool '%s' with arguments keys: %s", tool_name, list(args.keys()))
            result = await tool.run(args)
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            result.execution_time_ms = round(elapsed_ms, 2)
            logger.info("Tool '%s' executed successfully in %.2fms", tool_name, result.execution_time_ms)
            return result

        except ValidationError as val_err:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            error_msg = f"Validation error for tool '{tool_name}': {str(val_err)}"
            logger.error(error_msg)
            return ToolResult(
                success=False,
                error=error_msg,
                execution_time_ms=round(elapsed_ms, 2),
            )

        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            error_msg = f"Runtime failure executing tool '{tool_name}': {str(exc)}"
            logger.error(error_msg, exc_info=True)
            return ToolResult(
                success=False,
                error=f"Tool execution failed safely: {str(exc)}",
                execution_time_ms=round(elapsed_ms, 2),
            )