"""Document Ingestion API Router connected to AgentRuntime."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from core.runtime import AgentRuntime
from core.runtime_models import IngestionPipelineInput, PipelineExecutionResult
from api.dependencies import get_runtime
from logger import logger

router = APIRouter(prefix="/documents", tags=["Documents"])


class IngestDocumentRequest(BaseModel):
    """Payload schema for document ingestion requests."""

    workspace_id: str = Field(..., min_length=1, description="Target workspace ID")
    file_path: str = Field(..., min_length=1, description="Path or reference to document on disk/storage")
    original_filename: str = Field(..., min_length=1, description="Original filename of the document")


@router.post(
    "/ingest",
    response_model=PipelineExecutionResult,
    status_code=status.HTTP_200_OK,
    summary="Ingest a document through the 8-stage Agent pipeline",
)
async def ingest_document(
    request: IngestDocumentRequest,
    runtime: AgentRuntime = Depends(get_runtime),
) -> PipelineExecutionResult:
    """Validates request and delegates sequential execution to AgentRuntime."""
    workspace_id = request.workspace_id.strip()
    if not workspace_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="workspace_id cannot be empty or whitespace.",
        )

    try:
        pipeline_input = IngestionPipelineInput(
            workspace_id=workspace_id,
            file_path=request.file_path.strip(),
            original_filename=request.original_filename.strip(),
        )
        result = await runtime.run_ingestion_pipeline(pipeline_input)

        if not result.success:
            logger.warning(
                "Ingestion pipeline returned failure for workspace '%s': %s",
                workspace_id,
                result.error_message,
            )
            # Return result structure for controlled business/validation failure
            return result

        return result

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Unhandled error during document ingestion: %s", str(exc), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during document ingestion.",
        )