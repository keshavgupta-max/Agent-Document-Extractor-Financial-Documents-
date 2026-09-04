"""Abstract Base Interface for Storage Providers."""

from abc import ABC, abstractmethod
from typing import Optional

from storage.models import StoragePayload, StorageResult


class BaseStorage(ABC):
    """Abstract interface defining required contract for all storage backends."""

    @abstractmethod
    def save_file(self, payload: StoragePayload) -> StorageResult:
        """Persists binary file payload to storage backend."""
        pass

    @abstractmethod
    def get_file(self, storage_path: str) -> bytes:
        """Retrieves raw file byte contents from storage path."""
        pass

    @abstractmethod
    def delete_file(self, storage_path: str) -> bool:
        """Deletes file from storage path. Returns True if successfully deleted."""
        pass

    @abstractmethod
    def file_exists(self, storage_path: str) -> bool:
        """Checks if file exists at the given storage path."""
        pass

    @abstractmethod
    def get_storage_metadata(self, storage_path: str) -> dict:
        """Retrieves storage-level metadata (e.g., size, modified time)."""
        pass