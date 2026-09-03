"""Document Ingestion & Management API Router connected to AgentRuntime."""

import uuid
from pathlib import Path
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, Field

from api.dependencies import get_runtime
from core.runtime import CANONICAL_STAGING_ROOT, AgentRuntime
from core.runtime_models import IngestionPipelineInput, PipelineExecutionResult
from logger import logger
from tools.upload.validator import UploadValidationError, UploadValidator
from tools.vector_storage.constants import (
    DEFAULT_COLLECTION_NAME,
    META_KEY_DOCUMENT_ID,
    META_KEY_DOCUMENT_TYPE,
    META_KEY_WORKSPACE_ID,
    META_KEY_ORIGINAL_FILENAME,
)
from tools.vector_storage.service import VectorStorageService

router = APIRouter(prefix="/documents", tags=["Documents"])


class IngestDocumentRequest(BaseModel):
    """Payload schema for pre-staged document ingestion requests."""

    workspace_id: str = Field(..., min_length=1, description="Target workspace ID")
    file_path: str = Field(..., min_length=1, description="Path or reference to document on disk/storage")
    original_filename: str = Field(..., min_length=1, description="Original filename of the document")


class DocumentSummary(BaseModel):
    """Summary record for an indexed document in a workspace."""

    document_id: str = Field(..., description="Document unique identifier")
    workspace_id: str = Field(..., description="Workspace identifier")
    document_type: str = Field(default="UNKNOWN", description="Classified document type")
    original_filename: str = Field(default="Unnamed Document", description="Original uploaded filename")
    total_chunks: int = Field(default=0, description="Total number of vector chunks stored")


class WorkspaceDocumentsResponse(BaseModel):
    """Response payload for document listing query."""

    workspace_id: str = Field(..., description="Queried workspace identifier")
    documents: List[DocumentSummary] = Field(default_factory=list, description="List of unique documents")
    total_documents: int = Field(default=0, description="Total count of unique documents in workspace")


@router.post(
    "/ingest",
    response_model=PipelineExecutionResult,
    status_code=status.HTTP_200_OK,
    summary="Ingest a pre-staged document through the 8-stage Agent pipeline",
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


@router.post(
    "/upload",
    response_model=PipelineExecutionResult,
    status_code=status.HTTP_200_OK,
    summary="Upload and ingest a document via multipart/form-data through the 8-stage pipeline",
)
async def upload_and_ingest_document(
    file: UploadFile = File(...),
    workspace_id: str = Form(...),
    runtime: AgentRuntime = Depends(get_runtime),
) -> PipelineExecutionResult:
    """Validates binary upload, writes to staging, executes pipeline, and guarantees cleanup."""
    clean_workspace_id = workspace_id.strip()
    if not clean_workspace_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="workspace_id cannot be empty or whitespace.",
        )

    content = await file.read()
    raw_filename = file.filename or "unnamed_file"
    raw_mime = file.content_type or "application/octet-stream"

    # Reuse existing UploadValidator to enforce size, extension, and MIME safety
    try:
        clean_filename, file_ext = UploadValidator.validate_upload(
            filename=raw_filename,
            content=content,
            mime_type=raw_mime,
        )
    except UploadValidationError as val_err:
        logger.warning("Upload validation failed: %s", val_err.message)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Upload validation failed: {val_err.message}",
        )

    # Prepare application-controlled temporary file inside canonical staging root
    staging_dir = getattr(runtime, "_staging_root", CANONICAL_STAGING_ROOT).resolve()
    staging_dir.mkdir(parents=True, exist_ok=True)

    temp_id = str(uuid.uuid4())
    temp_staged_path = staging_dir / f"staged_{temp_id}{file_ext}"

    try:
        temp_staged_path.write_bytes(content)

        pipeline_input = IngestionPipelineInput(
            workspace_id=clean_workspace_id,
            file_path=str(temp_staged_path),
            original_filename=clean_filename,
        )

        result = await runtime.run_ingestion_pipeline(pipeline_input)
        return result

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Unexpected failure in /documents/upload: %s", str(exc), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during document upload and ingestion.",
        )
    finally:
        # Guarantee cleanup of temporary staging file
        if temp_staged_path.exists():
            try:
                temp_staged_path.unlink()
                logger.debug("Cleaned up temporary staging file: %s", temp_staged_path)
            except Exception as cleanup_exc:
                logger.warning("Failed to clean up staging file %s: %s", temp_staged_path, str(cleanup_exc))


@router.get(
    "",
    response_model=WorkspaceDocumentsResponse,
    status_code=status.HTTP_200_OK,
    summary="List all unique indexed documents within a workspace",
)
async def list_workspace_documents(
    workspace_id: str = Query(..., min_length=1, description="Workspace identifier to list documents for"),
) -> WorkspaceDocumentsResponse:
    """Queries vector storage metadata to list all unique documents in the specified workspace."""
    clean_workspace_id = workspace_id.strip()
    if not clean_workspace_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="workspace_id query parameter cannot be empty or whitespace.",
        )

    try:
        storage_svc = VectorStorageService()
        client = storage_svc._get_client()

        # Check if collection exists; if not, return empty list cleanly
        try:
            collection = client.get_collection(name=DEFAULT_COLLECTION_NAME)
        except Exception:
            return WorkspaceDocumentsResponse(
                workspace_id=clean_workspace_id,
                documents=[],
                total_documents=0,
            )

        # Retrieve all records filtered by workspace_id
        stored_records = collection.get(
            where={META_KEY_WORKSPACE_ID: clean_workspace_id},
            include=["metadatas"],
        )

        metadatas = stored_records.get("metadatas") or []
        doc_map: Dict[str, Dict[str, any]] = {}

        for meta in metadatas:
            if not isinstance(meta, dict):
                continue

            doc_id = str(meta.get(META_KEY_DOCUMENT_ID, "")).strip()
            if not doc_id:
                continue

            doc_type = str(meta.get(META_KEY_DOCUMENT_TYPE, "UNKNOWN")).strip()
            orig_filename = str(meta.get(META_KEY_ORIGINAL_FILENAME, "Unnamed Document")).strip() or "Unnamed Document"

            if doc_id not in doc_map:
                doc_map[doc_id] = {
                    "document_id": doc_id,
                    "workspace_id": clean_workspace_id,
                    "document_type": doc_type,
                    "original_filename": orig_filename,
                    "total_chunks": 1,
                }
            else:
                doc_map[doc_id]["total_chunks"] += 1

        summaries = [DocumentSummary(**data) for data in doc_map.values()]

        return WorkspaceDocumentsResponse(
            workspace_id=clean_workspace_id,
            documents=summaries,
            total_documents=len(summaries),
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to list documents for workspace '%s': %s", clean_workspace_id, str(exc), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while listing workspace documents.",
        )
    # ==============================================================================
# 2. api/documents.py
# ==============================================================================
# Adding Response Model and DELETE route:

class DocumentDeleteResponse(BaseModel):
    """Response payload for document deletion."""
    success: bool = Field(default=True, description="Deletion success flag")
    document_id: str = Field(..., description="Deleted document unique identifier")
    workspace_id: str = Field(..., description="Workspace identifier")
    deleted_chunks: int = Field(..., description="Total count of vector chunks deleted")
    message: str = Field(default="Document successfully deleted", description="Status message")


@router.delete(
    "/{document_id}",
    response_model=DocumentDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a document and its indexed vectors from a workspace",
)
async def delete_workspace_document(
    document_id: str,
    workspace_id: str = Query(..., min_length=1, description="Workspace identifier owning the document"),
) -> DocumentDeleteResponse:
    """Deletes all vector embeddings associated with the specified document and workspace."""
    clean_workspace_id = workspace_id.strip()
    clean_doc_id = document_id.strip()

    if not clean_workspace_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="workspace_id query parameter cannot be empty or whitespace.",
        )
    if not clean_doc_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="document_id path parameter cannot be empty or whitespace.",
        )

    try:
        storage_svc = VectorStorageService()
        deleted_count = storage_svc.delete_document_vectors(
            workspace_id=clean_workspace_id,
            document_id=clean_doc_id,
        )

        if deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found in the specified workspace.",
            )

        return DocumentDeleteResponse(
            success=True,
            document_id=clean_doc_id,
            workspace_id=clean_workspace_id,
            deleted_chunks=deleted_count,
            message=f"Document '{clean_doc_id}' and {deleted_count} chunk(s) successfully deleted.",
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to delete document '%s' in workspace '%s': %s", clean_doc_id, clean_workspace_id, str(exc), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while deleting the document.",
        )