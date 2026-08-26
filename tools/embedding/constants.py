"""Constants and configuration defaults for the Embedding Generation Engine."""

# Configurable Embedding Provider Defaults
DEFAULT_EMBEDDING_MODEL: str = "gemini-embedding-2"
DEFAULT_VECTOR_DIMENSIONS: int = 768

# Batch Processing Configuration
MAX_EMBEDDING_BATCH_SIZE: int = 100  # Maximum text chunks per batch API call

# Rate Limit & 429 Retry Configuration
MAX_EMBEDDING_RETRIES: int = 3
EMBEDDING_RETRY_BASE_DELAY_SECONDS: float = 2.0
EMBEDDING_RETRY_MAX_DELAY_SECONDS: float = 30.0

# Metadata Keys
META_KEY_EMBEDDING_MODEL: str = "embedding_model"
META_KEY_VECTOR_DIMENSIONS: str = "vector_dimensions"