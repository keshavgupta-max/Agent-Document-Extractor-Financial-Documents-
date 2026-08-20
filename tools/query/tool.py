"""Query Tool implementation inheriting from BaseTool."""

from typing import Type
from pydantic import BaseModel

from core.base_tool import BaseTool
from core.state import AgentState
from core.tool_result import ToolResult
from logger import logger
from tools.query.exceptions import QueryError
from tools.query.models import QueryInput
from tools.query.service import QueryService


class QueryTool(BaseTool):
    """Tool responsible for grounded AI question-answering over selected business documents."""

    name: str = "query_documents"
    description: str = (
        "Answers user questions using Google GenAI, grounded strictly in text chunks "
        "retrieved from explicitly selected document IDs within a specific workspace."
    )
    input_model: Type[BaseModel] = QueryInput

    async def _run(self, state: AgentState, input_data: BaseModel) -> ToolResult:
        """Executes grounded query answering via QueryService."""
        if not isinstance(input_data, QueryInput):
            return ToolResult(
                success=False,
                error=f"Invalid input model provided to {self.name}. Expected QueryInput.",
            )

        try:
            service = QueryService()
            result = service.answer_query(input_data)

            # Minimal non-sensitive metadata update
            state.metadata["last_query_workspace"] = result.workspace_id
            state.metadata["last_query_sources_count"] = result.total_sources_retrieved

            logger.info(
                "QueryTool executed successfully for workspace: %s | Sources: %d",
                result.workspace_id,
                result.total_sources_retrieved,
            )

            return ToolResult(
                success=True,
                data=result.model_dump(),
                execution_time_ms=result.processing_time_ms,
            )

        except QueryError as q_err:
            logger.warning("QueryTool domain error: %s", q_err.message)
            return ToolResult(
                success=False,
                error=f"Query execution failed: {q_err.message}",
            )
        except Exception as exc:
            logger.error("Unexpected error in QueryTool", exc_info=True)
            return ToolResult(
                success=False,
                error="Internal error occurred during AI query processing.",
            )