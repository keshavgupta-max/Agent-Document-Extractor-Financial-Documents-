/**
 * Exact TypeScript bindings mirroring backend Pydantic models.
 */

export type DocumentType = "INVOICE" | "BANK_STATEMENT" | "UNKNOWN";

export type ExecutionMode = "DOCUMENT_INGESTION" | "QUERY";

export interface StageResult {
  tool_name: string;
  success: boolean;
  execution_time_ms: number;
  error: string | null;
}

export interface PipelineExecutionResult<T = Record<string, unknown>> {
  success: boolean;
  mode: ExecutionMode;
  workspace_id: string;
  document_id?: string | null;
  final_output?: T | null;
  failed_stage?: string | null;
  stages: StageResult[];
  total_execution_time_ms: number;
  error_message?: string | null;
}

export interface DocumentSummary {
  document_id: string;
  workspace_id: string;
  document_type: DocumentType;
  total_chunks: number;
  original_filename?: string;
}

export interface WorkspaceDocumentsResponse {
  workspace_id: string;
  documents: DocumentSummary[];
  total_documents: number;
}

export interface QuerySourceChunk {
  chunk_id: string;
  document_id: string;
  workspace_id: string;
  chunk_index: number;
  document_type: string;
  snippet: string;
  distance: number | null;
}

export interface QueryResult {
  workspace_id: string;
  selected_document_ids: string[];
  query: string;
  answer: string;
  source_chunks: QuerySourceChunk[];
  total_sources_retrieved: number;
  processing_time_ms: number;
}

export interface FinancialSummaryResponse {
  workspace_id: string;
  document_ids: string[];
  total_credit_amount: number | null;
  total_debit_amount: number | null;
  net_cash_flow: number | null;
  total_transactions: number;
  opening_balance: number | null;
  closing_balance: number | null;
  invoice_subtotal: number | null;
  invoice_tax: number | null;
  invoice_grand_total: number | null;
  currency: string;
  documents_analyzed: number;
}

export interface TransactionItem {
  item_number: number;
  date: string | null;
  description: string | null;
  transaction_type: "CR" | "DB" | "CREDIT" | "DEBIT" | null;
  amount: number | null;
  credit_amount: number | null;
  debit_amount: number | null;
  balance: number | null;
  raw_text: string;
}

export interface TransactionListResponse {
  workspace_id: string;
  document_id: string;
  total_transactions: number;
  limit: number;
  offset: number;
  transactions: TransactionItem[];
}

export interface HealthCheckResponse {
  status: "healthy" | string;
}