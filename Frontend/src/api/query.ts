import { apiClient, DEFAULT_PIPELINE_TIMEOUT_MS } from "./client";
import { PipelineExecutionResult, QueryResult } from "@/types/api";

interface QueryRequest {
  workspace_id: string;
  selected_document_ids: string[];
  query: string;
  top_k: number;
}

export async function executeGroundedQuery(
  payload: QueryRequest
): Promise<PipelineExecutionResult<QueryResult>> {
  return apiClient<PipelineExecutionResult<QueryResult>>("/query", {
    method: "POST",
    body: JSON.stringify(payload),
    timeoutMs: DEFAULT_PIPELINE_TIMEOUT_MS,
  });
}