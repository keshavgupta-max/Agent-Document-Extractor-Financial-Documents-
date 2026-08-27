"""Document Grounded Query API Router connected to AgentRuntime."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from api.dependencies import get_runtime
from core.runtime import AgentRuntime
from core.runtime_models import PipelineExecutionResult, QueryPipelineInput
from logger import logger

router = APIRouter(prefix="/query", tags=["Query"])


class QueryDocumentRequest(BaseModel):
    """Payload schema for grounded query requests."""

    workspace_id: str = Field(..., min_length=1, description="Target workspace ID")
    selected_document_ids: List[str] = Field(
        ...,
        min_length=1,
        max_length=5,
        description="Explicit list of 1 to 5 document IDs to restrict querying scope",
    )
    query: str = Field(..., min_length=1, description="User query prompt")
    top_k: Optional[int] = Field(default=5, ge=1, le=20, description="Top-k chunks to retrieve")


@router.post(
    "",
    response_model=PipelineExecutionResult,
    status_code=status.HTTP_200_OK,
    summary="Execute grounded query over explicitly scoped documents",
)
async def query_documents(
    request: QueryDocumentRequest,
    runtime: AgentRuntime = Depends(get_runtime),
) -> PipelineExecutionResult:
    """Validates request boundaries and invokes AgentRuntime query pipeline."""
    workspace_id = request.workspace_id.strip()
    if not workspace_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="workspace_id cannot be empty or whitespace.",
        )

    # Filter out empty or whitespace document IDs
    valid_doc_ids = [doc_id.strip() for doc_id in request.selected_document_ids if doc_id.strip()]
    if not valid_doc_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="selected_document_ids must contain at least one valid non-empty document ID.",
        )

    if len(valid_doc_ids) > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="selected_document_ids cannot exceed 5 documents per query.",
        )

    clean_query = request.query.strip()
    if not clean_query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="query cannot be empty or whitespace.",
        )

    try:
        pipeline_input = QueryPipelineInput(
            workspace_id=workspace_id,
            selected_document_ids=valid_doc_ids,
            query=clean_query,
            top_k=request.top_k or 5,
        )
        result = await runtime.run_query_pipeline(pipeline_input)

        if not result.success:
            logger.warning(
                "Query pipeline returned failure for workspace '%s': %s",
                workspace_id,
                result.error_message,
            )
            return result

        return result

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Unhandled error during grounded querying: %s", str(exc), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during query processing.",
        )