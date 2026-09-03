// =============================================================================
// 3. Frontend/src/api/documents.ts
// =============================================================================

import { apiClient, DEFAULT_PIPELINE_TIMEOUT_MS, DEFAULT_READ_TIMEOUT_MS } from "./client";
import { PipelineExecutionResult, WorkspaceDocumentsResponse } from "@/types/api";

export interface DocumentDeleteResponse {
  success: boolean;
  document_id: string;
  workspace_id: string;
  deleted_chunks: number;
  message: string;
}

export async function uploadAndIngestDocument(
  file: File,
  workspaceId: string
): Promise<PipelineExecutionResult> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("workspace_id", workspaceId.trim() || "ws_default");

  return apiClient<PipelineExecutionResult>("/documents/upload", {
    method: "POST",
    body: formData,
    timeoutMs: DEFAULT_PIPELINE_TIMEOUT_MS,
  });
}

export async function getWorkspaceDocuments(
  workspaceId: string
): Promise<WorkspaceDocumentsResponse> {
  const cleanWs = encodeURIComponent(workspaceId.trim() || "ws_default");
  const res = await apiClient<WorkspaceDocumentsResponse>(
    `/documents?workspace_id=${cleanWs}`,
    {
      method: "GET",
      timeoutMs: DEFAULT_READ_TIMEOUT_MS,
    }
  );

  return {
    ...res,
    documents: Array.isArray(res?.documents) ? res.documents : [],
    total_documents: typeof res?.total_documents === "number" ? res.total_documents : (res?.documents?.length || 0),
  };
}

export async function deleteDocument(
  documentId: string,
  workspaceId: string
): Promise<DocumentDeleteResponse> {
  const cleanDocId = encodeURIComponent(documentId.trim());
  const cleanWs = encodeURIComponent(workspaceId.trim() || "ws_default");

  return apiClient<DocumentDeleteResponse>(
    `/documents/${cleanDocId}?workspace_id=${cleanWs}`,
    {
      method: "DELETE",
      timeoutMs: DEFAULT_READ_TIMEOUT_MS,
    }
  );
}