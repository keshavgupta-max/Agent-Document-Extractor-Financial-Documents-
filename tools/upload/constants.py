"""Constants and configuration rules for the Secure Upload Tool."""

from typing import Dict, Set

# File Size Limits (10 MB default max upload size)
MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024

# Allowed Extensions
ALLOWED_EXTENSIONS: Set[str] = {
    ".pdf",
    ".doc",
    ".docx",
    ".png",
    ".jpg",
    ".jpeg",
    ".tiff",
    ".bmp",
    ".xlsx",
    ".xls",
    ".csv",
    ".txt",
}

# Allowed MIME Types mapped to their extensions
ALLOWED_MIME_TYPES: Dict[str, Set[str]] = {
    "application/pdf": {".pdf"},
    "application/msword": {".doc"},
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": {".docx"},
    "image/png": {".png"},
    "image/jpeg": {".jpg", ".jpeg"},
    "image/tiff": {".tiff"},
    "image/bmp": {".bmp"},
    "application/vnd.ms-excel": {".xls"},
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {".xlsx"},
    "text/csv": {".csv"},
    "text/plain": {".txt"},
}

# Dangerous / Executable Extensions to explicitly block
DANGEROUS_EXTENSIONS: Set[str] = {
    ".exe", ".bat", ".cmd", ".sh", ".bash", ".php", ".py", ".pl", ".rb",
    ".js", ".vbs", ".jar", ".ps1", ".msi", ".dll", ".so", ".com", ".scr",
    ".phtml", ".phar", ".asp", ".aspx", ".jsp", ".shtml"
}

# Technical File Category Mapping
TECHNICAL_CATEGORY_MAP: Dict[str, str] = {
    ".pdf": "PDF",
    ".doc": "WORD",
    ".docx": "WORD",
    ".png": "IMAGE",
    ".jpg": "IMAGE",
    ".jpeg": "IMAGE",
    ".tiff": "IMAGE",
    ".bmp": "IMAGE",
    ".xlsx": "SPREADSHEET",
    ".xls": "SPREADSHEET",
    ".csv": "SPREADSHEET",
    ".txt": "TEXT",
}

# Upload Status Constants
class UploadStatus:
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

# Processing Status Constants
class ProcessingStatus:
    UNPROCESSED = "UNPROCESSED"
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

# Validation Status Constants
class ValidationStatus:
    VALID = "VALID"
    INVALID = "INVALID"
    SKIPPED = "SKIPPED"