import { apiClient } from "./client";
import { HealthCheckResponse } from "@/types/api";

export async function getBackendHealth(): Promise<HealthCheckResponse> {
  return apiClient<HealthCheckResponse>("/health", { method: "GET" });
}