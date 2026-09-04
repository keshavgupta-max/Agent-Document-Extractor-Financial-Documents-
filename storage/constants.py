"""Constants and configuration paths for the Storage Manager."""

from pathlib import Path
from typing import Set

# Base Project Data Directories
BASE_DATA_DIR: Path = Path("data")
TEMP_DIR: Path = BASE_DATA_DIR / "temp"
STORAGE_DIR: Path = BASE_DATA_DIR / "storage"
DOCUMENTS_STORAGE_DIR: Path = STORAGE_DIR / "documents"
CHROMA_DIR: Path = BASE_DATA_DIR / "chroma"
LOGS_DIR: Path = BASE_DATA_DIR / "logs"

# List of required runtime directories to initialize on startup
REQUIRED_RUNTIME_DIRECTORIES: Set[Path] = {
    BASE_DATA_DIR,
    TEMP_DIR,
    STORAGE_DIR,
    DOCUMENTS_STORAGE_DIR,
    CHROMA_DIR,
    LOGS_DIR,
}


class StorageStatus:
    """Storage operation status indicators."""

    STORED = "STORED"
    RETRIEVED = "RETRIEVED"
    DELETED = "DELETED"
    FAILED = "FAILED"