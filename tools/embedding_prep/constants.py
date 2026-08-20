"""Constants and chunking configurations for Embedding Preparation."""

# Chunking Strategy Configuration
DEFAULT_CHUNK_SIZE: int = 1000  # Character count target per chunk
DEFAULT_CHUNK_OVERLAP: int = 150  # Overlap between consecutive chunks
MINIMUM_CHUNK_SIZE: int = 100  # Threshold to prevent tiny orphan chunks

# Section Header Identifiers for Clean Semantic Formatting
SECTION_SUMMARY: str = "DOCUMENT SUMMARY"
SECTION_HEADER: str = "HEADER & IDENTIFIERS"
SECTION_SELLER: str = "SELLER / VENDOR DETAILS"
SECTION_BUYER: str = "BUYER / CUSTOMER DETAILS"
SECTION_LINE_ITEMS: str = "LINE ITEMS & SERVICES"
SECTION_TAXES: str = "TAXES & BREAKDOWN"
SECTION_TOTALS: str = "DOCUMENT TOTALS & CURRENCY"
SECTION_RAW_PAGES: str = "EXTRACTED PAGE TEXT"

# Metadata Keys
META_KEY_WORKSPACE_ID: str = "workspace_id"
META_KEY_DOCUMENT_ID: str = "document_id"
META_KEY_DOCUMENT_TYPE: str = "document_type"
META_KEY_CHUNK_INDEX: str = "chunk_index"
META_KEY_TOTAL_CHUNKS: str = "total_chunks"
META_KEY_IS_VALID: str = "is_valid"