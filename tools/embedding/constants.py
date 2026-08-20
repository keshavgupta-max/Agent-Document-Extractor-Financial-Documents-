"""Constants and configuration defaults for the Embedding Generation Engine."""

# Configurable Embedding Provider Defaults
DEFAULT_EMBEDDING_MODEL: str = "gemini-embedding-2"
DEFAULT_VECTOR_DIMENSIONS: int = 768

# Batch Processing Configuration
MAX_EMBEDDING_BATCH_SIZE: int = 100  # Maximum text chunks per batch API call

# Metadata Keys
META_KEY_EMBEDDING_MODEL: str = "embedding_model"
META_KEY_VECTOR_DIMENSIONS: str = "vector_dimensions"