"""Extractor Tool implementation inheriting from BaseTool."""

from typing import Type
from pydantic import BaseModel

from core.base_tool import BaseTool
from core.state import AgentState
from core.tool_result import ToolResult
from logger import logger
from tools.extractor.exceptions import ExtractorError
from tools.extractor.models import ExtractorInput
from tools.extractor.service import ExtractorService


class ExtractorTool(BaseTool):
    """Tool responsible for extracting normalized structured data from classified documents."""

    name: str = "extract_structured_data"
    description: str = (
        "Extracts structured business fields (headers, parties, line items, taxes, totals) "
        "from a ParsedDocument given its DocumentClassification."
    )
    input_model: Type[BaseModel] = ExtractorInput

    async def _run(self, state: AgentState, input_data: BaseModel) -> ToolResult:
        """Executes structured extraction logic via ExtractorService."""
        if not isinstance(input_data, ExtractorInput):
            return ToolResult(
                success=False,
                error=f"Invalid input model provided to {self.name}. Expected ExtractorInput.",
            )

        try:
            service = ExtractorService()
            structured_doc = service.extract_data(input_data)

            doc_id = structured_doc.document_id
            state.metadata[f"extracted_{doc_id}"] = True

            logger.info(
                "ExtractorTool successfully executed for document_id: %s",
                doc_id,
            )

            return ToolResult(
                success=True,
                data=structured_doc.model_dump(),
                execution_time_ms=structured_doc.metadata.processing_time_ms,
            )

        except ExtractorError as e_err:
            logger.warning("ExtractorTool error processing document: %s", e_err.message)
            return ToolResult(
                success=False,
                error=f"Extraction failed: {e_err.message}",
            )
        except Exception as exc:
            logger.error("Unexpected error in ExtractorTool: %s", str(exc), exc_info=True)
            return ToolResult(
                success=False,
                error=f"Internal error during structured data extraction: {str(exc)}",
            )