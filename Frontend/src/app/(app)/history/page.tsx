"use client";

import React, { useState, useEffect, useMemo } from "react";
import { useRouter } from "next/navigation";
import { useWorkspace } from "@/context/WorkspaceContext";
import {
  AnalysisHistoryEntry,
  getWorkspaceHistory,
  clearWorkspaceHistory,
} from "@/lib/history";
import {
  HistoryCard,
  HistoryDetailModal,
  ClearHistoryModal,
  HistoryEmptyState,
} from "@/components/history/HistoryComponents";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import {
  Search,
  Trash2,
  Calendar,
  Info,
} from "lucide-react";

export default function HistoryPage() {
  const router = useRouter();
  const { workspaceId, isInitialized, setSelectedDocumentIds } = useWorkspace();

  const [historyItems, setHistoryItems] = useState<AnalysisHistoryEntry[]>([]);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [selectedEntry, setSelectedEntry] = useState<AnalysisHistoryEntry | null>(null);
  const [clearModalOpen, setClearModalOpen] = useState<boolean>(false);

  // Load local workspace history on mount and on workspace change
  useEffect(() => {
    if (isInitialized) {
      setHistoryItems(getWorkspaceHistory(workspaceId));
    }
  }, [isInitialized, workspaceId]);

  // Filter items by question, answer text, or document IDs
  const filteredItems = useMemo(() => {
    const q = searchQuery.toLowerCase().trim();
    if (!q) return historyItems;

    return historyItems.filter((item) => {
      const matchQuestion = item.question.toLowerCase().includes(q);
      const matchAnswer = item.answer.toLowerCase().includes(q);
      const matchDocId = item.selectedDocumentIds.some((id) => id.toLowerCase().includes(q));
      return matchQuestion || matchAnswer || matchDocId;
    });
  }, [historyItems, searchQuery]);

  // Chronological Grouping (Today, Yesterday, Earlier)
  const groupedItems = useMemo(() => {
    const now = new Date();
    const todayStr = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
    const oneDayMs = 24 * 60 * 60 * 1000;

    const today: AnalysisHistoryEntry[] = [];
    const yesterday: AnalysisHistoryEntry[] = [];
    const earlier: AnalysisHistoryEntry[] = [];

    filteredItems.forEach((item) => {
      const itemTime = new Date(item.timestamp).getTime();
      if (itemTime >= todayStr) {
        today.push(item);
      } else if (itemTime >= todayStr - oneDayMs) {
        yesterday.push(item);
      } else {
        earlier.push(item);
      }
    });

    return { today, yesterday, earlier };
  }, [filteredItems]);

  const handleClearHistoryConfirm = () => {
    clearWorkspaceHistory(workspaceId);
    setHistoryItems([]);
  };

  const handleAskNewWithScope = (docIds: string[]) => {
    setSelectedDocumentIds(docIds);
    router.push("/analyze");
  };

  if (!isInitialized) {
    return (
      <div className="space-y-4 max-w-4xl mx-auto">
        <div className="h-8 w-48 bg-slate-100 rounded animate-pulse" />
        <div className="h-10 w-full bg-slate-100 rounded animate-pulse" />
      </div>
    );
  }

  return (
    <div className="space-y-6 w-full max-w-6xl mx-auto pb-16">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-typography-primary">
            Analysis History
          </h1>
          <p className="text-xs text-typography-secondary">
            Locally saved analysis records and cited evidence for workspace{" "}
            <strong className="font-mono text-typography-primary">{workspaceId}</strong>.
          </p>
        </div>

        {historyItems.length > 0 && (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => setClearModalOpen(true)}
            className="text-xs h-8 text-status-error hover:bg-red-50 hover:text-red-700 self-start sm:self-center"
          >
            <Trash2 className="mr-1.5 h-3.5 w-3.5" />
            <span>Clear History</span>
          </Button>
        )}
      </div>

      {/* Local Storage Scope Notice */}
      <div className="flex items-center space-x-2 rounded border border-border bg-slate-50 p-2.5 text-[11px] text-typography-muted">
        <Info className="h-3.5 w-3.5 text-primary-600 flex-shrink-0" />
        <span>
          History records are stored locally in your browser and isolated strictly to this workspace identifier.
        </span>
      </div>

      {historyItems.length === 0 ? (
        <HistoryEmptyState />
      ) : (
        <div className="space-y-6">
          {/* Search Input */}
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-typography-muted" />
            <Input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search previous queries, answers, or doc IDs..."
              className="pl-9 h-9 text-xs"
            />
          </div>

          {filteredItems.length === 0 ? (
            <div className="rounded border border-dashed border-border p-8 text-center text-xs text-typography-muted">
              No analysis records match your search query.
            </div>
          ) : (
            <div className="space-y-6">
              {/* Group: Today */}
              {groupedItems.today.length > 0 && (
                <div className="space-y-3">
                  <div className="flex items-center space-x-2 text-xs font-semibold text-typography-muted uppercase tracking-wider">
                    <Calendar className="h-3.5 w-3.5" />
                    <span>Today</span>
                  </div>
                  <div className="space-y-3">
                    {groupedItems.today.map((item) => (
                      <HistoryCard
                        key={item.id}
                        entry={item}
                        onViewDetails={(entry) => setSelectedEntry(entry)}
                      />
                    ))}
                  </div>
                </div>
              )}

              {/* Group: Yesterday */}
              {groupedItems.yesterday.length > 0 && (
                <div className="space-y-3">
                  <div className="flex items-center space-x-2 text-xs font-semibold text-typography-muted uppercase tracking-wider">
                    <Calendar className="h-3.5 w-3.5" />
                    <span>Yesterday</span>
                  </div>
                  <div className="space-y-3">
                    {groupedItems.yesterday.map((item) => (
                      <HistoryCard
                        key={item.id}
                        entry={item}
                        onViewDetails={(entry) => setSelectedEntry(entry)}
                      />
                    ))}
                  </div>
                </div>
              )}

              {/* Group: Earlier */}
              {groupedItems.earlier.length > 0 && (
                <div className="space-y-3">
                  <div className="flex items-center space-x-2 text-xs font-semibold text-typography-muted uppercase tracking-wider">
                    <Calendar className="h-3.5 w-3.5" />
                    <span>Earlier</span>
                  </div>
                  <div className="space-y-3">
                    {groupedItems.earlier.map((item) => (
                      <HistoryCard
                        key={item.id}
                        entry={item}
                        onViewDetails={(entry) => setSelectedEntry(entry)}
                      />
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* History Detail Modal */}
      <HistoryDetailModal
        entry={selectedEntry}
        isOpen={Boolean(selectedEntry)}
        onClose={() => setSelectedEntry(null)}
        onAskNewWithScope={handleAskNewWithScope}
      />

      {/* Clear History Confirmation Modal */}
      <ClearHistoryModal
        isOpen={clearModalOpen}
        workspaceId={workspaceId}
        onClose={() => setClearModalOpen(false)}
        onConfirm={handleClearHistoryConfirm}
      />
    </div>
  );
}