import React, { useRef } from "react";
import { formatBytes } from "@/lib/utils";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import {
  UploadCloud,
  FileText,
  CheckCircle2,
  X,
  RotateCcw,
  Loader2,
} from "lucide-react";

export type UploadFileStatus = "idle" | "uploading" | "ready" | "failed" | "rejected";

export interface QueuedUploadItem {
  id: string;
  file: File;
  status: UploadFileStatus;
  errorMessage?: string;
  documentId?: string;
  totalTimeMs?: number;
  stagesCompleted?: number;
  lockedWorkspaceId?: string;
}

interface UploadDropZoneProps {
  onFilesSelected: (files: FileList | File[]) => void;
  disabled?: boolean;
  maxFiles: number;
}

export function UploadDropZone({ onFilesSelected, disabled = false, maxFiles }: UploadDropZoneProps) {
  const [isDragOver, setIsDragOver] = React.useState(false);
  const inputRef = useRef<HTMLInputElement | null>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    if (!disabled) setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (disabled || !e.dataTransfer.files) return;
    onFilesSelected(e.dataTransfer.files);
  };

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={`relative flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 text-center transition-colors ${
        isDragOver
          ? "border-primary-600 bg-primary-50/50"
          : "border-border bg-surface hover:border-slate-400"
      } ${disabled ? "opacity-50 pointer-events-none" : ""}`}
    >
      <input
        ref={inputRef}
        type="file"
        multiple
        accept=".pdf,.csv,.xlsx"
        className="sr-only"
        id="file-upload-input"
        onChange={(e) => {
          if (e.target.files) onFilesSelected(e.target.files);
        }}
        disabled={disabled}
      />

      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary-50 text-primary-600 mb-3">
        <UploadCloud className="h-6 w-6" />
      </div>

      <h3 className="text-sm font-semibold text-typography-primary">
        Drag & drop financial documents here
      </h3>
      <p className="mt-1 text-xs text-typography-muted">
        or browse your computer (Max {maxFiles} files per batch)
      </p>

      <div className="mt-4 flex items-center space-x-2">
        <label htmlFor="file-upload-input">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => inputRef.current?.click()}
            disabled={disabled}
            className="cursor-pointer"
          >
            Browse Files
          </Button>
        </label>
      </div>

      <div className="mt-4 flex items-center space-x-2 text-[11px] text-typography-muted">
        <span>Supported:</span>
        <span className="font-semibold text-typography-secondary">PDF • CSV • XLSX</span>
        <span>• Up to 10 MB per file</span>
      </div>
    </div>
  );
}

interface UploadQueueItemProps {
  item: QueuedUploadItem;
  onRemove: (id: string) => void;
  onRetry: (id: string) => void;
  disabled?: boolean;
}

export function UploadQueueItem({ item, onRemove, onRetry, disabled = false }: UploadQueueItemProps) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between rounded border border-border bg-surface p-3.5 gap-3 shadow-subtle">
      <div className="flex items-center space-x-3 truncate">
        <div className="flex h-8 w-8 items-center justify-center rounded bg-slate-50 text-typography-muted flex-shrink-0">
          <FileText className="h-4 w-4" />
        </div>
        <div className="truncate text-left">
          <p className="text-xs font-semibold text-typography-primary truncate max-w-[240px] sm:max-w-md">
            {item.file.name}
          </p>
          <p className="text-[11px] text-typography-muted font-mono">
            {formatBytes(item.file.size)}
            {item.documentId && <span className="ml-2 text-primary-700">ID: {item.documentId.slice(0, 8)}...</span>}
            {item.totalTimeMs && <span className="ml-2 text-typography-muted">({(item.totalTimeMs / 1000).toFixed(2)}s)</span>}
          </p>
        </div>
      </div>

      {/* Status & Actions */}
      <div className="flex items-center space-x-3 self-end sm:self-center">
        {item.status === "idle" && (
          <Badge variant="outline" className="text-[10px]">
            Ready to upload
          </Badge>
        )}

        {item.status === "uploading" && (
          <div className="flex items-center space-x-1.5 text-xs text-primary-700 font-medium bg-primary-50 px-2.5 py-1 rounded">
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
            <span>Processing...</span>
          </div>
        )}

        {item.status === "ready" && (
          <div className="flex items-center space-x-1 text-xs text-status-success font-medium bg-status-successBg px-2 py-0.5 rounded">
            <CheckCircle2 className="h-3.5 w-3.5" />
            <span>Ready</span>
          </div>
        )}

        {item.status === "failed" && (
          <div className="flex items-center space-x-2">
            <Badge variant="error" className="text-[10px]">
              Failed
            </Badge>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onRetry(item.id)}
              disabled={disabled}
              className="h-7 px-2 text-xs"
              title="Retry ingestion"
            >
              <RotateCcw className="h-3 w-3 mr-1" />
              Retry
            </Button>
          </div>
        )}

        {item.status === "rejected" && (
          <div className="flex items-center space-x-1">
            <Badge variant="error" className="text-[10px]" title={item.errorMessage}>
              Rejected
            </Badge>
          </div>
        )}

        {item.status !== "uploading" && (
          <button
            type="button"
            onClick={() => onRemove(item.id)}
            disabled={disabled}
            className="text-slate-400 hover:text-slate-600 transition-colors p-1"
            title="Remove from queue"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Sanitized Error message if failed/rejected */}
      {(item.status === "failed" || item.status === "rejected") && item.errorMessage && (
        <div className="w-full text-left sm:hidden text-[11px] text-status-error">
          {item.errorMessage}
        </div>
      )}
    </div>
  );
}
