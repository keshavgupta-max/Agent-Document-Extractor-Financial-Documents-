"""Validation Tool implementation inheriting from BaseTool."""

from typing import Type
from pydantic import BaseModel

from core.base_tool import BaseTool
from core.state import AgentState
from core.tool_result import ToolResult
from logger import logger
from tools.validator.exceptions import ValidatorError
from tools.validator.models import ValidationInput
from tools.validator.service import ValidationService


class ValidationTool(BaseTool):
    """Tool responsible for executing mathematical and business compliance checks on structured documents."""

    name: str = "validate_document"
    description: str = (
        "Validates a StructuredBusinessDocument for header completeness, party identifier formats (GSTIN/PAN), "
        "line-item presence, and mathematical consistency (subtotal, tax, grand total)."
    )
    input_model: Type[BaseModel] = ValidationInput

    async def _run(self, state: AgentState, input_data: BaseModel) -> ToolResult:
        """Executes document validation logic via ValidationService."""
        if not isinstance(input_data, ValidationInput):
            return ToolResult(
                success=False,
                error=f"Invalid input model provided to {self.name}. Expected ValidationInput.",
            )

        try:
            service = ValidationService()
            validation_result = service.validate_document(input_data)

            doc_id = validation_result.document_id
            state.metadata[f"validated_{doc_id}"] = validation_result.is_valid
            state.metadata[f"validation_status_{doc_id}"] = validation_result.status

            logger.info(
                "ValidationTool successfully executed for document_id: %s | Status: %s",
                doc_id,
                validation_result.status,
            )

            return ToolResult(
                success=True,
                data=validation_result.model_dump(),
                execution_time_ms=validation_result.processing_time_ms,
            )

        except ValidatorError as v_err:
            logger.warning("ValidationTool error processing document: %s", v_err.message)
            return ToolResult(
                success=False,
                error=f"Validation failed: {v_err.message}",
            )
        except Exception as exc:
            logger.error("Unexpected error in ValidationTool: %s", str(exc), exc_info=True)
            return ToolResult(
                success=False,
                error=f"Internal error during document validation: {str(exc)}",
            )