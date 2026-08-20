"""Constants and type mappings for the Document Parsing Engine."""

from typing import Dict, Set

# Supported File Extensions mapped to Parser Type
PARSER_EXTENSION_MAP: Dict[str, str] = {
    ".pdf": "PDF",
    ".docx": "DOCX",
    ".doc": "DOCX",
    ".xlsx": "EXCEL",
    ".xls": "EXCEL",
    ".csv": "CSV",
    ".txt": "TXT",
    ".png": "IMAGE",
    ".jpg": "IMAGE",
    ".jpeg": "IMAGE",
}

SUPPORTED_PARSER_EXTENSIONS: Set[str] = set(PARSER_EXTENSION_MAP.keys())


class ParsingStatus:
    """Parsing process status values."""

    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"