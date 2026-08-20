"""FastAPI upload router translating HTTP requests into domain upload operations."""

from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from logger import logger
from tools.upload.models import UploadInput


router = APIRouter(prefix="/api/v1", tags=["Upload"])


def get_runtime():
    """Import and return global runtime instance."""
    from app.main import runtime

    return runtime


@router.post("/upload", status_code=status.HTTP_200_OK)
async def upload_document_endpoint(
    file: UploadFile = File(...),
    workspace_id: str = Form(...),
    uploaded_by: str = Form(...),
    tags: Optional[List[str]] = Form(default=None),
    notes: Optional[str] = Form(default=None),
    source: Optional[str] = Form(default=None),
):
    """Translate HTTP upload request into an UploadInput and invoke AgentRuntime."""
    try:
        content = await file.read()

        upload_input = UploadInput(
            filename=file.filename or "unnamed_file",
            content=content,
            mime_type=file.content_type or "application/octet-stream",
            workspace_id=workspace_id,
            uploaded_by=uploaded_by,
            tags=tags or [],
            notes=notes,
            source=source,
        )

        runtime = get_runtime()

        result = await runtime.execute_tool(
            "upload_document",
            upload_input,
        )

        if not result.success:
            logger.warning(
                "Upload tool execution returned failure: %s",
                result.error,
            )

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.error or "Failed to process document upload.",
            )

        return {
            "status": "success",
            "data": result.data,
            "execution_time_ms": result.execution_time_ms,
        }

    except HTTPException:
        raise

    except Exception as exc:
        logger.error(
            "Unhandled error in upload API endpoint: %s",
            str(exc),
            exc_info=True,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred while processing the upload.",
        )