import React from "react";
import Link from "next/link";
import { DocumentSummary } from "@/types/api";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import {
  FileSpreadsheet,
  Sparkles,
  X,
  UploadCloud,
  AlertCircle,
  Copy,
  Check,
} from "lucide-react";

interface DocumentSelectionBarProps {
  selectedCount: number;
  maxCount: number;
  onClear: () => void;
  onAnalyze: () => void;
}

export function DocumentSelectionBar({
  selectedCount,
  maxCount,
  onClear,
  onAnalyze,
}: DocumentSelectionBarProps) {
  if (selectedCount === 0) return null;

  return (
    <div
      className="fixed bottom-6 inset-x-4 max-w-xl mx-auto z-40 animate-in fade-in slide-in-from-bottom-4 duration-200"
      aria-live="polite"
    >
      <div className="flex items-center justify-between rounded-lg border border-primary-600/30 bg-surface px-4 py-3 shadow-elevated">
        <div className="flex items-center space-x-3">
          <Badge variant="default" className="bg-primary-50 text-primary-700 font-mono text-xs">
            {selectedCount} / {maxCount} selected
          </Badge>
          <span className="text-xs font-medium text-typography-primary hidden sm:inline">
            Ready for grounded AI query
          </span>
        </div>

        <div className="flex items-center space-x-2">
          <Button variant="ghost" size="sm" onClick={onClear} className="text-xs h-8">
            <X className="mr-1 h-3.5 w-3.5" />
            <span>Clear</span>
          </Button>
          <Button variant="primary" size="sm" onClick={onAnalyze} className="text-xs h-8">
            <Sparkles className="mr-1.5 h-3.5 w-3.5" />
            <span>Analyze Selected</span>
          </Button>
        </div>
      </div>
    </div>
  );
}

interface DocumentMetadataModalProps {
  document: DocumentSummary | null;
  isOpen: boolean;
  onClose: () => void;
}

export function DocumentMetadataModal({
  document,
  isOpen,
  onClose,
}: DocumentMetadataModalProps) {
  const [copied, setCopied] = React.useState(false);

  if (!document) return null;

  const handleCopyId = () => {
    navigator.clipboard.writeText(document.document_id);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Document Metadata">
      <div className="space-y-4 text-xs">
        {/* Document ID */}
        <div className="space-y-1">
          <span className="font-semibold text-typography-muted uppercase tracking-wider text-[11px]">
            Document ID
          </span>
          <div className="flex items-center justify-between rounded border border-border bg-slate-50 p-2 font-mono">
            <span className="truncate max-w-[320px] text-typography-primary">{document.document_id}</span>
            <button
              onClick={handleCopyId}
              className="ml-2 text-typography-muted hover:text-typography-primary transition-colors"
              title="Copy ID"
            >
              {copied ? <Check className="h-3.5 w-3.5 text-status-success" /> : <Copy className="h-3.5 w-3.5" />}
            </button>
          </div>
        </div>

        {/* Workspace ID */}
        <div className="space-y-1">
          <span className="font-semibold text-typography-muted uppercase tracking-wider text-[11px]">
            Workspace ID
          </span>
          <div className="rounded border border-border bg-slate-50 p-2 font-mono text-typography-primary">
            {document.workspace_id}
          </div>
        </div>

        {/* Document Type */}
        <div className="space-y-1">
          <span className="font-semibold text-typography-muted uppercase tracking-wider text-[11px]">
            Document Type
          </span>
          <div>
            <Badge
              variant={
                document.document_type === "BANK_STATEMENT"
                  ? "success"
                  : document.document_type === "INVOICE"
                  ? "default"
                  : "outline"
              }
              className="text-xs"
            >
              {document.document_type}
            </Badge>
          </div>
        </div>

        {/* Total Chunks */}
        <div className="space-y-1">
          <span className="font-semibold text-typography-muted uppercase tracking-wider text-[11px]">
            Total Chunks Indexed
          </span>
          <div className="rounded border border-border bg-slate-50 p-2 font-mono text-typography-primary">
            {document.total_chunks} chunk{document.total_chunks !== 1 ? "s" : ""}
          </div>
          <p className="text-[11px] text-typography-muted">
            Number of deterministic chunks indexed in vector storage for grounded query retrieval.
          </p>
        </div>

        <div className="pt-2 flex justify-end">
          <Button variant="outline" size="sm" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    </Modal>
  );
}

export function DocumentsEmptyState() {
  return (
    <div className="rounded-lg border border-dashed border-border bg-surface p-12 text-center shadow-subtle space-y-4 max-w-lg mx-auto my-8">
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary-50 text-primary-600 mx-auto">
        <FileSpreadsheet className="h-6 w-6" />
      </div>
      <div className="space-y-1">
        <h3 className="text-base font-bold text-typography-primary">No documents yet</h3>
        <p className="text-xs text-typography-secondary">
          Upload your financial files to start analyzing invoices and bank statements with grounded AI.
        </p>
      </div>
      <div className="pt-2">
        <Link href="/upload">
          <Button variant="primary" size="md">
            <UploadCloud className="mr-2 h-4 w-4" />
            <span>Upload Document</span>
          </Button>
        </Link>
      </div>
    </div>
  );
}

export function DocumentsErrorState({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="rounded border border-status-error/20 bg-status-errorBg p-4 text-xs text-slate-800 flex items-center justify-between">
      <div className="flex items-center space-x-2">
        <AlertCircle className="h-4 w-4 text-status-error flex-shrink-0" />
        <span>Unable to load documents from the current workspace.</span>
      </div>
      <Button variant="outline" size="sm" onClick={onRetry} className="bg-surface text-xs h-7">
        Retry
      </Button>
    </div>
  );
}