"""Custom exception hierarchy for Storage Manager operations."""

from exceptions import BaseAgentException


class StorageError(BaseAgentException):
    """Base exception for all storage-related failures."""

    pass


class FileNotFoundStorageError(StorageError):
    """Raised when a requested stored file does not exist."""

    pass


class FileAlreadyExistsError(StorageError):
    """Raised when attempting to save a file that already exists at destination."""

    pass


class PathTraversalError(StorageError):
    """Raised when path resolution attempts to break out of base storage directory."""

    pass


class StorageWriteError(StorageError):
    """Raised when file writing or verification fails on physical media."""

    pass