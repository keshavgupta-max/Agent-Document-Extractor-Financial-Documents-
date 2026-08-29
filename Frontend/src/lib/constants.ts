export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export const DEFAULT_WORKSPACE_ID = "ws_default";
export const WORKSPACE_STORAGE_KEY = "findoc_active_workspace";

export const MAX_SELECTION_DOCUMENTS = 5;
export const MAX_UPLOAD_BATCH_SIZE = 20;
export const MAX_UPLOAD_FILE_SIZE_BYTES = 10 * 1024 * 1024; // 10 MB

export const SUPPORTED_FILE_EXTENSIONS = [".pdf", ".csv", ".xlsx"];
export const SUPPORTED_MIME_TYPES = [
  "application/pdf",
  "text/csv",
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
];

export const INGESTION_STAGES = [
  "upload_document",
  "parse_document",
  "classify_document",
  "extract_structured_data",
  "validate_document",
  "prepare_embedding_content",
  "generate_embeddings",
  "store_vectors",
] as const;