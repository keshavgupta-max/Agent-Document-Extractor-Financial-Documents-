"""Secure Upload Tool implementation."""

from typing import Type

from pydantic import BaseModel

from core.base_tool import BaseTool
from core.state import AgentState
from core.tool_result import ToolResult
from logger import logger
from storage.local_storage import LocalStorage
from storage.models import StoragePayload
from tools.upload.models import UploadInput
from tools.upload.service import UploadService
from tools.upload.validator import UploadValidationError


class UploadTool(BaseTool):
    """Tool responsible for validating and persisting document uploads."""

    name: str = "upload_document"

    description: str = (
        "Validates incoming files, generates secure document identifiers, "
        "and persists uploaded files."
    )

    input_model: Type[BaseModel] = UploadInput

    async def _run(
        self,
        state: AgentState,
        input_data: BaseModel,
    ) -> ToolResult:
        """Validate, prepare, and persist the uploaded document."""

        if not isinstance(input_data, UploadInput):
            return ToolResult(
                success=False,
                error=(
                    f"Invalid input model provided to '{self.name}'. "
                    "Expected UploadInput."
                ),
            )

        try:
            service = UploadService()

            upload_result, storage_request = service.prepare_upload(
                input_data
            )

            storage_payload = StoragePayload(
                document_id=storage_request.document_id,
                stored_filename=storage_request.stored_filename,
                original_filename=storage_request.original_filename,
                workspace_id=storage_request.workspace_id,
                content=storage_request.content,
                mime_type=storage_request.mime_type,
            )

            storage = LocalStorage()

            storage_result = storage.save_file(storage_payload)

            result_data = {
                **upload_result.model_dump(),
                **storage_result.model_dump(),
            }

            logger.info(
                "Successfully uploaded document '%s' to '%s'.",
                upload_result.document_id,
                storage_result.storage_path,
            )

            return ToolResult(
                success=True,
                data=result_data,
                execution_time_ms=0.0,
                metadata={
                    "storage_status": storage_result.storage_status,
                },
            )

        except UploadValidationError as exc:
            logger.warning(
                "Upload validation failed: %s",
                exc.message,
            )

            return ToolResult(
                success=False,
                error=f"Upload validation failed: {exc.message}",
            )

        except Exception:
            logger.error(
                "Unexpected error while processing upload.",
                exc_info=True,
            )

            return ToolResult(
                success=False,
                error="Internal error processing uploaded document.",
            )