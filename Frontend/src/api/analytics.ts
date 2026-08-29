import { apiClient } from "./client";
import { FinancialSummaryResponse, TransactionListResponse } from "@/types/api";

export async function getFinancialSummary(
  workspaceId: string,
  documentIds: string[]
): Promise<FinancialSummaryResponse> {
  const params = new URLSearchParams();
  params.append("workspace_id", workspaceId);
  documentIds.forEach((id) => params.append("document_ids", id));

  return apiClient<FinancialSummaryResponse>(`/analytics/summary?${params.toString()}`, {
    method: "GET",
  });
}

export async function getDocumentTransactions(
  workspaceId: string,
  documentId: string,
  limit: number = 100,
  offset: number = 0
): Promise<TransactionListResponse> {
  const params = new URLSearchParams({
    workspace_id: workspaceId,
    document_id: documentId,
    limit: limit.toString(),
    offset: offset.toString(),
  });

  return apiClient<TransactionListResponse>(`/analytics/transactions?${params.toString()}`, {
    method: "GET",
  });
}