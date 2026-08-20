"""Parser Tool implementation inheriting from BaseTool."""

from typing import Type
from pydantic import BaseModel

from core.base_tool import BaseTool
from core.state import AgentState
from core.tool_result import ToolResult
from logger import logger
from tools.parser.exceptions import ParserError
from tools.parser.models import ParserInput
from tools.parser.service import ParserService


class ParserTool(BaseTool):
    """Tool responsible for orchestrating document content parsing and text/table extraction."""

    name: str = "parse_document"
    description: str = (
        "Reads stored business documents from storage, parses text, pages, "
        "and tabular structures, and returns a normalized ParsedDocument representation."
    )
    input_model: Type[BaseModel] = ParserInput

    async def _run(self, state: AgentState, input_data: BaseModel) -> ToolResult:
        """Executes document parsing logic via ParserService."""
        if not isinstance(input_data, ParserInput):
            return ToolResult(
                success=False,
                error=f"Invalid input model provided to {self.name}. Expected ParserInput.",
            )

        try:
            service = ParserService()
            parsed_doc = service.parse_document(input_data)

            # Store summary metadata inside active request AgentState if needed
            state.metadata[f"parsed_{parsed_doc.document_id}"] = parsed_doc.parsing_status

            logger.info(
                "ParserTool successfully executed for document_id: %s",
                parsed_doc.document_id,
            )

            return ToolResult(
                success=True,
                data=parsed_doc.model_dump(),
                execution_time_ms=parsed_doc.parsing_time_ms,
            )

        except ParserError as p_err:
            logger.warning("ParserTool error processing document: %s", p_err.message)
            return ToolResult(
                success=False,
                error=f"Parsing failed: {p_err.message}",
            )
        except Exception as exc:
            logger.error("Unexpected error in ParserTool: %s", str(exc), exc_info=True)
            return ToolResult(
                success=False,
                error=f"Internal error during document parsing: {str(exc)}",
            )