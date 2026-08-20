"""Classifier Tool implementation inheriting from BaseTool."""

from typing import Type
from pydantic import BaseModel

from core.base_tool import BaseTool
from core.state import AgentState
from core.tool_result import ToolResult
from logger import logger
from tools.classifier.exceptions import ClassifierError
from tools.classifier.models import ClassifierInput
from tools.classifier.service import ClassifierService


class ClassifierTool(BaseTool):
    """Tool responsible for determining business document type using deterministic rules."""

    name: str = "classify_document"
    description: str = (
        "Analyzes text and tabular structures of a ParsedDocument "
        "and classifies it into a standard business document type (e.g., Sales Invoice, GST Return)."
    )
    input_model: Type[BaseModel] = ClassifierInput

    async def _run(self, state: AgentState, input_data: BaseModel) -> ToolResult:
        """Executes document classification logic via ClassifierService."""
        if not isinstance(input_data, ClassifierInput):
            return ToolResult(
                success=False,
                error=f"Invalid input model provided to {self.name}. Expected ClassifierInput.",
            )

        try:
            service = ClassifierService()
            classification = service.classify_document(input_data)

            # Record document classification in active request AgentState
            doc_id = classification.document_id
            state.metadata[f"classified_{doc_id}"] = classification.document_type
            state.metadata[f"classification_confidence_{doc_id}"] = classification.confidence

            logger.info(
                "ClassifierTool successfully executed for document_id: %s | Type: %s",
                doc_id,
                classification.document_type,
            )

            return ToolResult(
                success=True,
                data=classification.model_dump(),
                execution_time_ms=classification.processing_time_ms,
            )

        except ClassifierError as c_err:
            logger.warning("ClassifierTool error processing document: %s", c_err.message)
            return ToolResult(
                success=False,
                error=f"Classification failed: {c_err.message}",
            )
        except Exception as exc:
            logger.error("Unexpected error in ClassifierTool: %s", str(exc), exc_info=True)
            return ToolResult(
                success=False,
                error=f"Internal error during document classification: {str(exc)}",
            )