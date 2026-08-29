import Link from "next/link";
import ReactMarkdown from "react-markdown";
import { AnalysisHistoryEntry } from "@/lib/history";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Modal } from "@/components/ui/Modal";
import { SourceChunksList } from "@/components/analyze/AnalyzeComponents";
import {
  History,
  Clock,
  Sparkles,
  ArrowRight,
} from "lucide-react";

interface HistoryCardProps {
  entry: AnalysisHistoryEntry;
  onViewDetails: (entry: AnalysisHistoryEntry) => void;
}

export function HistoryCard({ entry, onViewDetails }: HistoryCardProps) {
  const formattedDate = new Date(entry.timestamp).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <Card
      onClick={() => onViewDetails(entry)}
      className="border-border bg-surface shadow-card hover:border-slate-300 transition-colors cursor-pointer p-4 space-y-3"
    >
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-border/60 pb-2.5">
        <div className="flex items-center space-x-2 truncate">
          <Sparkles className="h-4 w-4 text-primary-600 flex-shrink-0" />
          <h3 className="text-xs font-bold text-typography-primary truncate max-w-md">
            &quot;{entry.question}&quot;
          </h3>
        </div>

        <div className="flex items-center space-x-2 text-[11px] text-typography-muted font-mono self-start sm:self-center">
          <Clock className="h-3 w-3" />
          <span>{formattedDate}</span>
        </div>
      </div>

      {/* Answer Preview Excerpt */}
      <p className="text-xs text-typography-secondary line-clamp-2 leading-relaxed">
        {entry.answer}
      </p>

      {/* Footer Details */}
      <div className="flex flex-wrap items-center justify-between gap-2 pt-1">
        <div className="flex items-center space-x-1.5 font-mono text-[11px] text-typography-muted">
          <span>Scope:</span>
          <Badge variant="outline" className="text-[10px] bg-slate-50">
            {entry.selectedDocumentIds.length} doc{entry.selectedDocumentIds.length !== 1 ? "s" : ""}
          </Badge>
          <span className="text-typography-muted">•</span>
          <span>{entry.sourceChunks.length} source{entry.sourceChunks.length !== 1 ? "s" : ""}</span>
        </div>

        <span className="text-xs font-semibold text-primary-600 flex items-center hover:text-primary-700">
          <span>View Details</span>
          <ArrowRight className="ml-1 h-3.5 w-3.5" />
        </span>
      </div>
    </Card>
  );
}

interface HistoryDetailModalProps {
  entry: AnalysisHistoryEntry | null;
  isOpen: boolean;
  onClose: () => void;
  onAskNewWithScope: (docIds: string[]) => void;
}

export function HistoryDetailModal({
  entry,
  isOpen,
  onClose,
  onAskNewWithScope,
}: HistoryDetailModalProps) {
  if (!entry) return null;

  const formattedDate = new Date(entry.timestamp).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Analysis Record" >
      <div className="space-y-5 text-xs">
        {/* Metadata Header */}
        <div className="rounded border border-border bg-slate-50 p-3 space-y-1.5 font-mono">
          <div className="flex flex-wrap justify-between items-center text-[11px] text-typography-muted gap-2">
            <span>Timestamp: <strong className="text-typography-primary">{formattedDate}</strong></span>
            <span>Latency: <strong className="text-typography-primary">{(entry.processingTimeMs / 1000).toFixed(2)}s</strong></span>
          </div>
          <div className="text-[11px] text-typography-secondary pt-1 border-t border-border/60">
            <span>Scoped Documents: </span>
            <span className="text-typography-primary font-medium">
              {entry.selectedDocumentIds.join(", ")}
            </span>
          </div>
        </div>

        {/* Question */}
        <div className="space-y-1">
          <span className="font-semibold text-typography-muted uppercase tracking-wider text-[11px]">
            Inquiry Question
          </span>
          <p className="text-sm font-semibold text-typography-primary">
            &quot;{entry.question}&quot;
          </p>
        </div>

        {/* Stored Grounded Answer Markdown */}
        <div className="space-y-1.5">
          <span className="font-semibold text-typography-muted uppercase tracking-wider text-[11px]">
            Grounded Answer
          </span>
          <div className="rounded border border-border bg-surface p-4 text-typography-primary prose prose-sm max-w-none leading-relaxed">
            <ReactMarkdown>{entry.answer}</ReactMarkdown>
          </div>
        </div>

        {/* Cited Evidence Sources */}
        <SourceChunksList chunks={entry.sourceChunks || []} />

        {/* Action Controls */}
        <div className="pt-3 border-t border-border flex flex-col sm:flex-row items-center justify-between gap-3">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => {
              onAskNewWithScope(entry.selectedDocumentIds);
              onClose();
            }}
            className="w-full sm:w-auto text-xs h-8 text-primary-700 bg-primary-50 hover:bg-primary-100 border-primary-200"
          >
            <Sparkles className="mr-1.5 h-3.5 w-3.5 text-primary-600" />
            <span>Ask New Question with this Scope</span>
          </Button>

          <Button variant="ghost" size="sm" onClick={onClose} className="w-full sm:w-auto text-xs h-8">
            Close
          </Button>
        </div>
      </div>
    </Modal>
  );
}

interface ClearHistoryModalProps {
  isOpen: boolean;
  workspaceId: string;
  onClose: () => void;
  onConfirm: () => void;
}

export function ClearHistoryModal({
  isOpen,
  workspaceId,
  onClose,
  onConfirm,
}: ClearHistoryModalProps) {
  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Clear Analysis History">
      <div className="space-y-4 text-xs">
        <p className="text-typography-secondary leading-relaxed">
          Are you sure you want to clear all locally saved analysis history for workspace{" "}
          <strong className="font-mono text-typography-primary">{workspaceId}</strong>?
        </p>
        <p className="text-typography-muted text-[11px]">
          This only removes cached question and answer records in this browser. Ingested documents and backend data remain untouched.
        </p>

        <div className="pt-3 border-t border-border flex justify-end space-x-2">
          <Button variant="ghost" size="sm" onClick={onClose}>
            Cancel
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => {
              onConfirm();
              onClose();
            }}
            className="bg-status-error hover:bg-red-700 text-white"
          >
            Clear Workspace History
          </Button>
        </div>
      </div>
    </Modal>
  );
}

export function HistoryEmptyState() {
  return (
    <div className="rounded-lg border border-dashed border-border bg-surface p-12 text-center shadow-subtle space-y-4 max-w-lg mx-auto my-8">
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary-50 text-primary-600 mx-auto">
        <History className="h-6 w-6" />
      </div>
      <div className="space-y-1">
        <h3 className="text-base font-bold text-typography-primary">No analysis history yet</h3>
        <p className="text-xs text-typography-secondary">
          Questions asked in the Analyze view are saved locally to this workspace for quick reference and evidence review.
        </p>
      </div>
      <div className="pt-2">
        <Link href="/analyze">
          <Button variant="primary" size="md">
            <Sparkles className="mr-2 h-4 w-4" />
            <span>Analyze Documents</span>
          </Button>
        </Link>
      </div>
    </div>
  );
}