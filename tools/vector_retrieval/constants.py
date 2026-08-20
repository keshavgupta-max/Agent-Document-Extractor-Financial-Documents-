"""Constants and configuration defaults for the Vector Retrieval Engine."""

from pathlib import Path

# Application-controlled ChromaDB Storage Location & Collection (Shared with Phase 12)
DEFAULT_CHROMA_STORAGE_DIR: Path = Path("database") / "chroma"
DEFAULT_COLLECTION_NAME: str = "business_documents"

# Search Parameters
DEFAULT_TOP_K: int = 5
MAX_TOP_K: int = 50

# Metadata Filtering Keys
META_KEY_WORKSPACE_ID: str = "workspace_id"
META_KEY_DOCUMENT_ID: str = "document_id"
META_KEY_DOCUMENT_TYPE: str = "document_type"
META_KEY_CHUNK_ID: str = "chunk_id"
META_KEY_CHUNK_INDEX: str = "chunk_index"