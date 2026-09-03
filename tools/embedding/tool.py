"""Embedding Generation Tool implementation inheriting from BaseTool."""

from typing import Type
from pydantic import BaseModel

from core.base_tool import BaseTool
from core.state import AgentState
from core.tool_result import ToolResult
from logger import logger
from tools.embedding.exceptions import EmbeddingGenerationError
from tools.embedding.models import EmbeddingInput
from tools.embedding.service import EmbeddingService


class EmbeddingTool(BaseTool):
    """Tool responsible for converting prepared semantic text chunks into vector embeddings."""

    name: str = "generate_embeddings"
    description: str = (
        "Converts prepared text chunks from Phase 10 into dense floating-point vector embeddings "
        "using the configured gemini-embedding-2 model while preserving workspace, document, and chunk identity."
    )
    input_model: Type[BaseModel] = EmbeddingInput

    async def _run(self, state: AgentState, input_data: BaseModel) -> ToolResult:
        """Executes vector embedding generation via EmbeddingService."""
        if not isinstance(input_data, EmbeddingInput):
            return ToolResult(
                success=False,
                error=f"Invalid input model provided to {self.name}. Expected EmbeddingInput.",
            )

        try:
            service = EmbeddingService()
            result = service.generate_embeddings(input_data)

            doc_id = result.document_id
            orig_name = state.metadata.get(f"filename_{doc_id}", "Unnamed Document")
            result.original_filename = orig_name
            result.metadata.original_filename = orig_name
            state.metadata[f"embeddings_generated_{doc_id}"] = True
            state.metadata[f"vector_count_{doc_id}"] = len(result.embeddings)

            logger.info(
                "EmbeddingTool successfully executed for document_id: %s | Vectors: %d",
                doc_id,
                len(result.embeddings),
            )

            return ToolResult(
                success=True,
                data=result.model_dump(),
                execution_time_ms=result.metadata.processing_time_ms,
            )

        except EmbeddingGenerationError as eg_err:
            logger.warning("EmbeddingTool error processing document: %s", eg_err.message)
            return ToolResult(
                success=False,
                error=f"Embedding generation failed: {eg_err.message}",
            )
        except Exception as exc:
            logger.error("Unexpected error in EmbeddingTool: %s", str(exc), exc_info=True)
            return ToolResult(
                success=False,
                error=f"Internal error during embedding generation: {str(exc)}",
            )