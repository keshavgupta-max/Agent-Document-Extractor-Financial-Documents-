"""Embedding Prep Tool implementation inheriting from BaseTool."""

from typing import Type
from pydantic import BaseModel

from core.base_tool import BaseTool
from core.state import AgentState
from core.tool_result import ToolResult
from logger import logger
from tools.embedding_prep.exceptions import EmbeddingPrepError
from tools.embedding_prep.models import EmbeddingPrepInput
from tools.embedding_prep.service import EmbeddingPrepService


class EmbeddingPrepTool(BaseTool):
    """Tool responsible for chunking and formatting structured documents for future embedding generation."""

    name: str = "prepare_embedding_content"
    description: str = (
        "Converts validated structured business document data and parsed text into "
        "clean semantic content blocks, generating deterministic chunks and isolation metadata."
    )
    input_model: Type[BaseModel] = EmbeddingPrepInput

    async def _run(self, state: AgentState, input_data: BaseModel) -> ToolResult:
        """Executes embedding preparation logic via EmbeddingPrepService."""
        if not isinstance(input_data, EmbeddingPrepInput):
            return ToolResult(
                success=False,
                error=f"Invalid input model provided to {self.name}. Expected EmbeddingPrepInput.",
            )

        try:
            service = EmbeddingPrepService()
            prepared_content = service.prepare_document(input_data)

            doc_id = prepared_content.document_id
            state.metadata[f"embedding_prep_completed_{doc_id}"] = True
            state.metadata[f"total_chunks_{doc_id}"] = prepared_content.metadata.total_chunks

            logger.info(
                "EmbeddingPrepTool executed successfully for document_id: %s | Chunks: %d",
                doc_id,
                prepared_content.metadata.total_chunks,
            )

            return ToolResult(
                success=True,
                data=prepared_content.model_dump(),
                execution_time_ms=prepared_content.metadata.processing_time_ms,
            )

        except EmbeddingPrepError as ep_err:
            logger.warning("EmbeddingPrepTool error processing document: %s", ep_err.message)
            return ToolResult(
                success=False,
                error=f"Embedding preparation failed: {ep_err.message}",
            )
        except Exception as exc:
            logger.error("Unexpected error in EmbeddingPrepTool: %s", str(exc), exc_info=True)
            return ToolResult(
                success=False,
                error=f"Internal error during embedding preparation: {str(exc)}",
            )