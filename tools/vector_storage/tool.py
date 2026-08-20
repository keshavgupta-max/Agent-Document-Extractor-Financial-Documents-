"""Vector Storage Tool implementation inheriting from BaseTool."""

from typing import Type

from pydantic import BaseModel

from core.base_tool import BaseTool
from core.state import AgentState
from core.tool_result import ToolResult
from logger import logger
from tools.vector_storage.exceptions import VectorStorageError
from tools.vector_storage.models import VectorStorageInput
from tools.vector_storage.service import VectorStorageService


class VectorStorageTool(BaseTool):
    """Tool responsible for storing generated document vectors into local ChromaDB with metadata isolation."""

    name: str = "store_vectors"
    description: str = (
        "Persists vector embeddings generated in Phase 11 into local ChromaDB. "
        "Applies deterministic record IDs and stores mandatory workspace and document metadata for isolation."
    )
    input_model: Type[BaseModel] = VectorStorageInput

    async def _run(
        self,
        state: AgentState,
        input_data: BaseModel,
    ) -> ToolResult:
        """Executes vector persistence via VectorStorageService."""

        if not isinstance(input_data, VectorStorageInput):
            return ToolResult(
                success=False,
                error=f"Invalid input model provided to {self.name}. "
                "Expected VectorStorageInput.",
            )

        try:
            service = VectorStorageService()
            result = service.store_embeddings(input_data)

            doc_id = result.document_id

            state.metadata[f"vectors_stored_{doc_id}"] = True
            state.metadata[f"stored_count_{doc_id}"] = result.stored_count

            logger.info(
                "VectorStorageTool successfully executed for document_id: %s | Records: %d",
                doc_id,
                result.stored_count,
            )

            return ToolResult(
                success=True,
                data=result.model_dump(),
                execution_time_ms=result.processing_time_ms,
            )

        except VectorStorageError as vs_err:
            logger.warning(
                "VectorStorageTool error processing document: %s",
                vs_err.message,
            )

            return ToolResult(
                success=False,
                error=f"Vector storage failed: {vs_err.message}",
            )

        except Exception:
            logger.error(
                "Unexpected error in VectorStorageTool",
                exc_info=True,
            )

            return ToolResult(
                success=False,
                error="Internal error during vector storage.",
            )