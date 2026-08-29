import { apiClient } from "./client";
import { PipelineExecutionResult, QueryResult } from "@/types/api";

export interface QueryPayload {
  workspace_id: string;
  selected_document_ids: string[];
  query: string;
  top_k?: number;
}

export async function executeGroundedQuery(
  payload: QueryPayload
): Promise<PipelineExecutionResult<QueryResult>> {
  return apiClient<PipelineExecutionResult<QueryResult>>("/query", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}