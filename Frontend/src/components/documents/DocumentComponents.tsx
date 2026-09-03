import React, { useState } from "react";
import Link from "next/link";
import { DocumentSummary } from "@/types/api";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import {
  FileText,
  UploadCloud,
  Sparkles,
  AlertCircle,
  Copy,
  Check,
  Trash2,
  Loader2,
} from "lucide-react";

interface DeleteDocumentModalProps {
  document: DocumentSummary | null;
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => Promise<void>;
  isDeleting: boolean;
}

export function DeleteDocumentModal({
  document,
  isOpen,
  onClose,
  onConfirm,
  isDeleting,
}: DeleteDocumentModalProps) {
  if (!document) return null;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Delete Document">
      <div className="space-y-4 text-xs">
        <p className="text-typography-secondary leading-relaxed">
          Are you sure you want to permanently delete document{" "}
          <strong className="text-typography-primary">{document.original_filename || document.document_id}</strong>?
          {document.original_filename && (
            <span className="block font-mono text-[10px] text-typography-muted mt-0.5">
              ID: {document.document_id}
            </span>
          )}
        </p>
        <p className="text-[11px] text-typography-muted">
          This will remove all {document.total_chunks} indexed vector chunk(s) from workspace{" "}
          <strong className="font-mono text-typography-primary">{document.workspace_id}</strong>.
          Its financial metrics will be excluded from the dashboard and grounded queries.
        </p>

        <div className="pt-3 border-t border-border flex justify-end space-x-2">
          <Button variant="ghost" size="sm" onClick={onClose} disabled={isDeleting}>
            Cancel
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={onConfirm}
            disabled={isDeleting}
            className="bg-status-error hover:bg-red-700 text-white"
          >
            {isDeleting ? (
              <>
                <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />
                <span>Deleting...</span>
              </>
            ) : (
              <>
                <Trash2 className="mr-1.5 h-3.5 w-3.5" />
                <span>Delete Document</span>
              </>
            )}
          </Button>
        </div>
      </div>
    </Modal>
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
  const [copied, setCopied] = useState(false);

  if (!document) return null;

  const handleCopyId = () => {
    navigator.clipboard.writeText(document.document_id);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Document Details">
      <div className="space-y-4 text-xs">
        {/* Original Filename Row */}
        {document.original_filename && (
          <div className="space-y-1.5">
            <label className="text-[11px] font-semibold text-typography-muted uppercase tracking-wider">
              Original Filename
            </label>
            <div className="rounded border border-border bg-slate-50 p-2.5 text-typography-primary font-medium font-sans">
              {document.original_filename}
            </div>
          </div>
        )}

        {/* Document ID */}
        <div className="space-y-1.5">
          <label className="text-[11px] font-semibold text-typography-muted uppercase tracking-wider">
            Document Identifier
          </label>
          <div className="flex items-center justify-between rounded border border-border bg-slate-50 p-2.5 font-mono">
            <span className="truncate pr-2 text-typography-primary select-all">
              {document.document_id}
            </span>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={handleCopyId}
              aria-label="Copy Document ID"
              className="h-7 w-7 p-0 flex-shrink-0 text-typography-muted hover:text-typography-primary"
            >
              {copied ? <Check className="h-3.5 w-3.5 text-status-success" /> : <Copy className="h-3.5 w-3.5" />}
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 pt-1">
          <div className="space-y-1">
            <span className="text-[11px] font-semibold text-typography-muted uppercase tracking-wider">
              Workspace ID
            </span>
            <p className="font-mono text-typography-primary bg-slate-50 p-2 rounded border border-border">
              {document.workspace_id}
            </p>
          </div>
          <div className="space-y-1">
            <span className="text-[11px] font-semibold text-typography-muted uppercase tracking-wider">
              Classification Type
            </span>
            <div className="p-1.5">
              <Badge variant="outline" className="text-xs">
                {document.document_type}
              </Badge>
            </div>
          </div>
        </div>

        <div className="space-y-1">
          <span className="text-[11px] font-semibold text-typography-muted uppercase tracking-wider">
            Indexed Storage
          </span>
          <p className="text-typography-secondary">
            Contains <strong className="font-mono text-typography-primary">{document.total_chunks}</strong> vector chunk embeddings stored in local ChromaDB.
          </p>
        </div>

        <div className="pt-3 border-t border-border flex justify-end">
          <Button variant="ghost" size="sm" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    </Modal>
  );
}

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
    <div className="fixed bottom-6 inset-x-4 max-w-xl mx-auto z-40 animate-in slide-in-from-bottom-4 duration-200">
      <div className="flex items-center justify-between rounded-lg border border-primary-500/30 bg-slate-900 px-4 py-3 text-white shadow-elevated">
        <div className="flex items-center space-x-2.5">
          <span className="flex h-5 w-5 items-center justify-center rounded-full bg-primary-600 text-[11px] font-bold">
            {selectedCount}
          </span>
          <span className="text-xs font-medium text-slate-200">
            document{selectedCount > 1 ? "s" : ""} selected (max {maxCount})
          </span>
        </div>

        <div className="flex items-center space-x-2">
          <button
            type="button"
            onClick={onClear}
            className="text-xs text-slate-400 hover:text-white px-2 py-1 transition-colors"
          >
            Clear
          </button>
          <Button
            variant="primary"
            size="sm"
            onClick={onAnalyze}
            className="bg-primary-500 hover:bg-primary-600 text-xs font-semibold h-8"
          >
            <Sparkles className="mr-1.5 h-3.5 w-3.5" />
            <span>Analyze Selected</span>
          </Button>
        </div>
      </div>
    </div>
  );
}

export function DocumentsEmptyState() {
  return (
    <div className="rounded-lg border border-dashed border-border bg-surface p-12 text-center shadow-subtle space-y-4 max-w-lg mx-auto mt-8">
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary-50 text-primary-600 mx-auto">
        <FileText className="h-6 w-6" />
      </div>
      <div className="space-y-1">
        <h3 className="text-base font-bold text-typography-primary">No documents indexed</h3>
        <p className="text-xs text-typography-secondary">
          This workspace does not have any processed financial documents yet. Upload statements or invoices to enable analysis.
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
    <div className="rounded border border-status-error/30 bg-status-errorBg p-4 text-xs text-slate-800 flex items-center justify-between">
      <div className="flex items-center space-x-2">
        <AlertCircle className="h-4 w-4 text-status-error flex-shrink-0" />
        <span>Failed to load workspace documents. Please verify your connection.</span>
      </div>
      <Button variant="outline" size="sm" onClick={onRetry} className="bg-surface text-xs h-7">
        Retry
      </Button>
    </div>
  );
}