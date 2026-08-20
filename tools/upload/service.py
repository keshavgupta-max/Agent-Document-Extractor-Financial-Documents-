"""Business logic service for processing document uploads."""

import uuid
from pathlib import Path
from typing import Tuple

from logger import logger
from tools.upload.constants import (
    ProcessingStatus,
    TECHNICAL_CATEGORY_MAP,
    UploadStatus,
    ValidationStatus,
)
from tools.upload.models import StorageRequest, UploadInput, UploadResult
from tools.upload.validator import UploadValidationError, UploadValidator


class UploadService:
    """Handles business preparation for secure document uploads."""

    def __init__(self) -> None:
        self._validator = UploadValidator()

    def determine_technical_category(self, extension: str) -> str:
        """Maps file extension to technical file category."""
        return TECHNICAL_CATEGORY_MAP.get(extension.lower(), "UNKNOWN")

    def prepare_upload(self, input_data: UploadInput) -> Tuple[UploadResult, StorageRequest]:
        """Validates input, assigns identifiers, determines category, and builds storage payload.

        Raises:
            UploadValidationError: If file validation fails.
        """
        # Validate file parameters
        clean_filename, file_ext = self._validator.validate_upload(
            filename=input_data.filename,
            content=input_data.content,
            mime_type=input_data.mime_type,
        )

        # Generate unique IDs and secure filenames
        document_id = str(uuid.uuid4())
        stored_filename = f"{document_id}{file_ext}"
        category = self.determine_technical_category(file_ext)
        file_size = len(input_data.content)

        logger.info(
            "Upload prepared successfully. Doc ID: %s | Original: %s | Category: %s | Size: %d bytes",
            document_id,
            clean_filename,
            category,
            file_size,
        )

        # Build output metadata model
        upload_result = UploadResult(
            document_id=document_id,
            original_filename=clean_filename,
            stored_filename=stored_filename,
            file_extension=file_ext,
            mime_type=input_data.mime_type.strip().lower(),
            technical_file_category=category,
            file_size=file_size,
            upload_status=UploadStatus.SUCCESS,
            processing_status=ProcessingStatus.UNPROCESSED,
            validation_status=ValidationStatus.VALID,
        )

        # Build storage request payload for Phase 5 Storage Manager
        storage_request = StorageRequest(
            document_id=document_id,
            stored_filename=stored_filename,
            workspace_id=input_data.workspace_id,
            content=input_data.content,
            mime_type=upload_result.mime_type,
            original_filename=upload_result.original_filename
        )

        return upload_result, storage_request