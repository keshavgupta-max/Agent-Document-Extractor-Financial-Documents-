"""Vector Retrieval Tool implementation inheriting from BaseTool."""

from typing import Type
from pydantic import BaseModel

from core.base_tool import BaseTool
from core.state import AgentState
from core.tool_result import ToolResult
from logger import logger
from tools.vector_retrieval.exceptions import VectorRetrievalError
from tools.vector_retrieval.models import VectorRetrievalInput
from tools.vector_retrieval.service import VectorRetrievalService


class VectorRetrievalTool(BaseTool):
    """Tool responsible for retrieving relevant text chunks from local ChromaDB based on query vector and scope."""

    name: str = "retrieve_vectors"
    description: str = (
        "Retrieves semantically relevant text chunks from local ChromaDB for a given query embedding, "
        "strictly restricted to the specified workspace ID and selected document IDs."
    )
    input_model: Type[BaseModel] = VectorRetrievalInput

    async def _run(self, state: AgentState, input_data: BaseModel) -> ToolResult:
        """Executes vector similarity search via VectorRetrievalService."""
        if not isinstance(input_data, VectorRetrievalInput):
            return ToolResult(
                success=False,
                error=f"Invalid input model provided to {self.name}. Expected VectorRetrievalInput.",
            )

        try:
            service = VectorRetrievalService()
            result = service.retrieve(input_data)

            # Minimal metadata state update per project guidelines
            state.metadata["retrieval_count"] = result.total_results
            state.metadata["retrieval_document_scope"] = result.selected_document_ids

            logger.info(
                "VectorRetrievalTool successfully executed for workspace: %s | Count: %d",
                result.workspace_id,
                result.total_results,
            )

            return ToolResult(
                success=True,
                data=result.model_dump(),
                execution_time_ms=result.processing_time_ms,
            )

        except VectorRetrievalError as vr_err:
            logger.warning("VectorRetrievalTool error during retrieval: %s", vr_err.message)
            return ToolResult(
                success=False,
                error=f"Retrieval failed: {vr_err.message}",
            )
        except Exception as exc:
            logger.error("Unexpected error in VectorRetrievalTool", exc_info=True)
            return ToolResult(
                success=False,
                error="Internal error occurred during vector retrieval.",
            )