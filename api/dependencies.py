"""API Dependency Providers for Phase 16 Runtime Integration."""

from functools import lru_cache
from core.runtime import AgentRuntime
from core.tool_registry import ToolRegistry


@lru_cache()
def get_tool_registry() -> ToolRegistry:
    """Returns a shared instance of ToolRegistry."""
    return ToolRegistry()


@lru_cache()
def get_runtime() -> AgentRuntime:
    """Provides a singleton instance of AgentRuntime."""
    registry = get_tool_registry()
    return AgentRuntime(registry=registry)