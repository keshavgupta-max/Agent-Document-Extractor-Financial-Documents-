import { apiClient } from "./client";
import { PipelineExecutionResult, WorkspaceDocumentsResponse } from "@/types/api";

export async function getWorkspaceDocuments(
  workspaceId: string
): Promise<WorkspaceDocumentsResponse> {
  return apiClient<WorkspaceDocumentsResponse>(
    `/documents?workspace_id=${encodeURIComponent(workspaceId)}`,
    { method: "GET" }
  );
}

export async function uploadAndIngestDocument(
  file: File,
  workspaceId: string
): Promise<PipelineExecutionResult> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("workspace_id", workspaceId);

  return apiClient<PipelineExecutionResult>("/documents/upload", {
    method: "POST",
    body: formData,
  });
}