"""Local file system implementation of BaseStorage."""

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

from logger import logger
from storage.base_storage import BaseStorage
from storage.constants import DOCUMENTS_STORAGE_DIR, REQUIRED_RUNTIME_DIRECTORIES, StorageStatus
from storage.exceptions import (
    FileAlreadyExistsError,
    FileNotFoundStorageError,
    PathTraversalError,
    StorageError,
    StorageWriteError,
)
from storage.models import StoragePayload, StorageResult


class LocalStorage(BaseStorage):
    """Concrete storage manager executing file persistence on local file system."""

    def __init__(self, base_dir: Optional[Path] = None) -> None:
        self._base_documents_dir = (base_dir or DOCUMENTS_STORAGE_DIR).resolve()
        self.ensure_runtime_directories()

    @staticmethod
    def ensure_runtime_directories() -> None:
        """Creates required system runtime directories if they do not exist."""
        for directory in REQUIRED_RUNTIME_DIRECTORIES:
            resolved_dir = directory.resolve()
            if not resolved_dir.exists():
                resolved_dir.mkdir(parents=True, exist_ok=True)
                logger.info("Created runtime directory: %s", resolved_dir)

    def _resolve_safe_path(self, target_path_str: str) -> Path:
        """Resolves target path and ensures it remains inside base storage directory.

        Raises:
            PathTraversalError: If target path escapes base directory boundary.
        """
        target_path = Path(target_path_str).resolve()
        if not str(target_path).startswith(str(self._base_documents_dir)):
            error_msg = f"Path traversal attack detected: '{target_path_str}'"
            logger.error(error_msg)
            raise PathTraversalError(error_msg)
        return target_path

    def _generate_destination_path(self, workspace_id: str, stored_filename: str) -> Path:
        """Generates path formatted as: data/storage/documents/workspace_id/YYYY/MM/stored_filename"""
        now = datetime.now(timezone.utc)
        year_str = now.strftime("%Y")
        month_str = now.strftime("%m")

        target_dir = self._base_documents_dir / workspace_id / year_str / month_str
        target_dir.mkdir(parents=True, exist_ok=True)

        full_path = (target_dir / stored_filename).resolve()
        return self._resolve_safe_path(str(full_path))

    def save_file(self, payload: StoragePayload) -> StorageResult:
        """Saves file binary content securely to disk and verifies write integrity."""
        destination_path = self._generate_destination_path(
            workspace_id=payload.workspace_id,
            stored_filename=payload.stored_filename,
        )

        if destination_path.exists():
            error_msg = f"File already exists at storage destination: '{destination_path}'"
            logger.error(error_msg)
            raise FileAlreadyExistsError(error_msg)

        try:
            # Atomic write simulation using temporary file in target directory
            temp_file = destination_path.with_suffix(f"{destination_path.suffix}.tmp")
            temp_file.write_bytes(payload.content)

            # Atomic rename to target file destination
            temp_file.replace(destination_path)

            # Verification of write
            actual_size = destination_path.stat().st_size
            expected_size = len(payload.content)

            if actual_size != expected_size:
                destination_path.unlink(missing_ok=True)
                error_msg = f"File size verification failed. Expected: {expected_size}, Got: {actual_size}"
                logger.error(error_msg)
                raise StorageWriteError(error_msg)

            logger.info("Successfully persisted file to local storage: %s", destination_path)

            return StorageResult(
                document_id=payload.document_id,
                stored_filename=payload.stored_filename,
                original_filename=payload.original_filename,
                storage_path=str(destination_path),
                workspace_id=payload.workspace_id,
                file_size=actual_size,
                mime_type=payload.mime_type,
                storage_status=StorageStatus.STORED,
            )

        except Exception as exc:
            if isinstance(exc, StorageError):
                raise
            error_msg = f"Failed to save file to local storage: {str(exc)}"
            logger.error(error_msg, exc_info=True)
            raise StorageWriteError(error_msg) from exc

    def get_file(self, storage_path: str) -> bytes:
        """Reads raw binary file content from local disk storage."""
        safe_path = self._resolve_safe_path(storage_path)
        if not safe_path.is_file():
            error_msg = f"Stored file not found: '{storage_path}'"
            logger.warning(error_msg)
            raise FileNotFoundStorageError(error_msg)

        try:
            return safe_path.read_bytes()
        except Exception as exc:
            error_msg = f"Failed to read file from storage path '{storage_path}': {str(exc)}"
            logger.error(error_msg)
            raise StorageError(error_msg) from exc

    def delete_file(self, storage_path: str) -> bool:
        """Deletes file from local disk storage."""
        safe_path = self._resolve_safe_path(storage_path)
        if not safe_path.is_file():
            logger.warning("Attempted to delete non-existent file: %s", storage_path)
            return False

        try:
            safe_path.unlink()
            logger.info("Successfully deleted stored file: %s", storage_path)
            return True
        except Exception as exc:
            error_msg = f"Failed to delete file from storage path '{storage_path}': {str(exc)}"
            logger.error(error_msg)
            raise StorageError(error_msg) from exc

    def file_exists(self, storage_path: str) -> bool:
        """Checks if a file exists on local storage safely."""
        try:
            safe_path = self._resolve_safe_path(storage_path)
            return safe_path.is_file()
        except StorageError:
            return False

    def get_storage_metadata(self, storage_path: str) -> dict:
        """Retrieves size and modified timestamp metadata for stored file."""
        safe_path = self._resolve_safe_path(storage_path)
        if not safe_path.is_file():
            raise FileNotFoundStorageError(f"Stored file not found: '{storage_path}'")

        stat_info = safe_path.stat()
        return {
            "storage_path": str(safe_path),
            "size_bytes": stat_info.st_size,
            "created_timestamp": stat_info.st_ctime,
            "modified_timestamp": stat_info.st_mtime,
        }