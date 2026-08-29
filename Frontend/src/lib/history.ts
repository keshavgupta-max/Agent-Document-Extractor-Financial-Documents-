import { QuerySourceChunk } from "@/types/api";

export interface AnalysisHistoryEntry {
  id: string;
  workspaceId: string;
  question: string;
  selectedDocumentIds: string[];
  answer: string;
  timestamp: string;
  sourceChunks: QuerySourceChunk[];
  processingTimeMs: number;
}

const HISTORY_KEY_PREFIX = "findoc_history_";
const MAX_HISTORY_RECORDS = 50;

function getStorageKey(workspaceId: string): string {
  return `${HISTORY_KEY_PREFIX}${workspaceId.trim() || "ws_default"}`;
}

export function getWorkspaceHistory(workspaceId: string): AnalysisHistoryEntry[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(getStorageKey(workspaceId));
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function saveAnalysisHistory(entry: AnalysisHistoryEntry): void {
  if (typeof window === "undefined") return;
  try {
    const existing = getWorkspaceHistory(entry.workspaceId);
    // Prepend new entry and cap at 50 records
    const updated = [entry, ...existing.filter((item) => item.id !== entry.id)].slice(0, MAX_HISTORY_RECORDS);
    localStorage.setItem(getStorageKey(entry.workspaceId), JSON.stringify(updated));
  } catch {
    // Ignore storage quota or access errors gracefully
  }
}

export function clearWorkspaceHistory(workspaceId: string): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.removeItem(getStorageKey(workspaceId));
  } catch {
    // Ignore storage errors
  }
}