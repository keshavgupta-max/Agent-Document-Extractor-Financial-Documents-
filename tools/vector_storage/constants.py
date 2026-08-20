"""Constants and default configurations for the Vector Storage Engine."""

from pathlib import Path

# Local ChromaDB Persistence Path
DEFAULT_CHROMA_STORAGE_DIR: Path = Path("database") / "chroma"

# Default Application Collection
DEFAULT_COLLECTION_NAME: str = "business_documents"

# ID Construction Delimiter
ID_SEPARATOR: str = ":"

# Metadata Keys
META_KEY_WORKSPACE_ID: str = "workspace_id"
META_KEY_DOCUMENT_ID: str = "document_id"
META_KEY_DOCUMENT_TYPE: str = "document_type"
META_KEY_CHUNK_ID: str = "chunk_id"
META_KEY_CHUNK_INDEX: str = "chunk_index"
META_KEY_EMBEDDING_MODEL: str = "embedding_model"
META_KEY_VECTOR_DIMENSIONS: str = "vector_dimensions"