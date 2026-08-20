"""Security and integrity validator for document uploads."""

import os
import re
from pathlib import Path
from typing import Optional, Tuple

from tools.upload.constants import (
    ALLOWED_EXTENSIONS,
    ALLOWED_MIME_TYPES,
    DANGEROUS_EXTENSIONS,
    MAX_UPLOAD_SIZE_BYTES,
)


class UploadValidationError(Exception):
    """Custom exception raised when upload validation fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class UploadValidator:
    """Performs strict security checks on raw uploads."""

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Removes directory paths, null bytes, and unsafe characters from a filename."""
        # Strip directory paths to prevent path traversal
        clean_name = os.path.basename(filename)
        # Remove null bytes
        clean_name = clean_name.replace("\x00", "")
        # Allow alphanumeric, dots, dashes, underscores
        clean_name = re.sub(r"[^a-zA-Z0-9._-]", "_", clean_name)
        # Prevent hidden dotfiles
        clean_name = clean_name.lstrip(".")
        return clean_name or "unnamed_file"

    @classmethod
    def validate_upload(
        cls, filename: str, content: bytes, mime_type: str
    ) -> Tuple[str, str]:
        """Validates file size, extension, MIME type, and checks for dangerous signatures.

        Returns:
            Tuple[str, str]: Cleaned original filename and normalized lowercase extension.

        Raises:
            UploadValidationError: If any validation rule fails.
        """
        # 1. Empty Content Check
        if not content or len(content) == 0:
            raise UploadValidationError("Uploaded file is empty.")

        # 2. Maximum Size Check
        if len(content) > MAX_UPLOAD_SIZE_BYTES:
            max_mb = MAX_UPLOAD_SIZE_BYTES / (1024 * 1024)
            raise UploadValidationError(
                f"File size exceeds maximum allowed limit of {max_mb:.1f} MB."
            )

        # 3. Filename Sanitization & Path Traversal Guard
        clean_filename = cls.sanitize_filename(filename)
        ext = Path(clean_filename).suffix.lower()

        if not ext:
            raise UploadValidationError("File missing extension.")

        # 4. Double Extension & Executable Check
        suffixes = [s.lower() for s in Path(clean_filename).suffixes]
        for s in suffixes:
            if s in DANGEROUS_EXTENSIONS:
                raise UploadValidationError(f"Forbidden dangerous extension detected: '{s}'")

        # 5. Extension Allowed List Check
        if ext not in ALLOWED_EXTENSIONS:
            raise UploadValidationError(f"Unsupported file extension: '{ext}'")

        # 6. MIME Type Allowed List Check
        clean_mime = mime_type.strip().lower()
        if clean_mime not in ALLOWED_MIME_TYPES:
            raise UploadValidationError(f"Unsupported MIME type: '{clean_mime}'")

        # 7. Extension and MIME Type Match Check
        allowed_exts_for_mime = ALLOWED_MIME_TYPES[clean_mime]
        if ext not in allowed_exts_for_mime:
            raise UploadValidationError(
                f"MIME type '{clean_mime}' does not match file extension '{ext}'."
            )

        return clean_filename, ext