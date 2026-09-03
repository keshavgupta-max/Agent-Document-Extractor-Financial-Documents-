"use client";

import React, { useState, useRef } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { useWorkspace } from "@/context/WorkspaceContext";
import { uploadAndIngestDocument } from "@/api/documents";
import {
  MAX_UPLOAD_BATCH_SIZE,
  MAX_UPLOAD_FILE_SIZE_BYTES,
  SUPPORTED_FILE_EXTENSIONS,
} from "@/lib/constants";
import {
  UploadDropZone,
  UploadQueueItem,
  QueuedUploadItem,
} from "@/components/upload/UploadComponents";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import {
  UploadCloud,
  CheckCircle2,
  AlertCircle,
  FileText,
  Sparkles,
  ArrowRight,
  ShieldAlert,
  X,
} from "lucide-react";

export default function UploadPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { workspaceId, setSelectedDocumentIds } = useWorkspace();

  const [queue, setQueue] = useState<QueuedUploadItem[]>([]);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [activeBatchWorkspace, setActiveBatchWorkspace] = useState<string | null>(null);
  const [batchNotice, setBatchNotice] = useState<string | null>(null);

  // Reference to abort/lock safety
  const isUploadingRef = useRef<boolean>(false);
  isUploadingRef.current = isUploading;

  // 1. Pre-flight Validation & Batch Add
  const handleFilesSelected = (selectedFiles: FileList | File[]) => {
    setBatchNotice(null);
    const filesArray = Array.from(selectedFiles);

    if (queue.length + filesArray.length > MAX_UPLOAD_BATCH_SIZE) {
      setBatchNotice(`Batch limited to ${MAX_UPLOAD_BATCH_SIZE} files. Excess files were omitted.`);
    }

    const availableSlots = Math.max(0, MAX_UPLOAD_BATCH_SIZE - queue.length);
    const filesToProcess = filesArray.slice(0, availableSlots);

    const newItems: QueuedUploadItem[] = filesToProcess.map((file) => {
      const ext = "." + file.name.split(".").pop()?.toLowerCase();
      const isExtSupported = SUPPORTED_FILE_EXTENSIONS.includes(ext);
      const isSizeValid = file.size <= MAX_UPLOAD_FILE_SIZE_BYTES;

      let status: "idle" | "rejected" = "idle";
      let errorMessage: string | undefined;

      if (!isExtSupported) {
        status = "rejected";
        errorMessage = "Unsupported file type. Only PDF, CSV, and XLSX are accepted.";
      } else if (!isSizeValid) {
        status = "rejected";
        errorMessage = "File exceeds maximum size limit of 10 MB.";
      }

      return {
        id: `${file.name}-${file.size}-${file.lastModified}-${Math.random()}`,
        file,
        status,
        errorMessage,
      };
    });

    setQueue((prev) => [...prev, ...newItems]);
  };

  const handleRemoveItem = (id: string) => {
    if (isUploading) return;
    setQueue((prev) => prev.filter((item) => item.id !== id));
  };

  const handleRetryItem = (id: string) => {
    setQueue((prev) =>
      prev.map((item) =>
        item.id === id ? { ...item, status: "idle", errorMessage: undefined } : item
      )
    );
  };

  const handleClearFinished = () => {
    if (isUploading) return;
    setQueue((prev) => prev.filter((item) => item.status === "failed" || item.status === "rejected"));
  };

  // 2. Controlled Concurrency Batch Upload Execution
  const handleStartUpload = async () => {
    const itemsToUpload = queue.filter((item) => item.status === "idle");
    if (itemsToUpload.length === 0 || isUploading) return;

    // Capture workspace for entire batch
    const lockedWorkspace = workspaceId;
    setActiveBatchWorkspace(lockedWorkspace);
    setIsUploading(true);

    const CONCURRENCY = 2;
    const workingQueue = [...itemsToUpload];

    const processItem = async (item: QueuedUploadItem) => {
      // Mark file as uploading
      setQueue((prev) =>
        prev.map((q) => (q.id === item.id ? { ...q, status: "uploading", lockedWorkspaceId: lockedWorkspace } : q))
      );

      try {
        const result = await uploadAndIngestDocument(item.file, lockedWorkspace);

        if (result.success && result.document_id) {
          setQueue((prev) =>
            prev.map((q) =>
              q.id === item.id
                ? {
                    ...q,
                    status: "ready",
                    documentId: result.document_id || undefined,
                    totalTimeMs: result.total_execution_time_ms,
                  }
                : q
            )
          );
        } else {
          setQueue((prev) =>
            prev.map((q) =>
              q.id === item.id
                ? {
                    ...q,
                    status: "failed",
                    errorMessage: result.error_message || "Document ingestion failed.",
                  }
                : q
            )
          );
        }
      } catch (err: unknown) {
        const errorText = err instanceof Error ? err.message : "Network error during upload.";
        setQueue((prev) =>
          prev.map((q) =>
            q.id === item.id
              ? {
                  ...q,
                  status: "failed",
                  errorMessage: errorText,
                }
              : q
          )
        );
      }
    };

    // Concurrency pool runner
    const runWorker = async () => {
      while (workingQueue.length > 0) {
        const nextItem = workingQueue.shift();
        if (nextItem) {
          await processItem(nextItem);
        }
      }
    };

    const workers = Array.from({ length: Math.min(CONCURRENCY, itemsToUpload.length) }, () => runWorker());
    await Promise.all(workers);

    setIsUploading(false);
    setActiveBatchWorkspace(null);

    // Invalidate React Query document caches for the active workspace
    queryClient.invalidateQueries({ queryKey: ["documents", lockedWorkspace] });
    queryClient.invalidateQueries({ queryKey: ["analytics-summary", lockedWorkspace] });
  };

  // Completed successful document IDs for navigation
  const successfulDocIds = queue
    .filter((item) => item.status === "ready" && item.documentId)
    .map((item) => item.documentId as string);

  const failedCount = queue.filter((item) => item.status === "failed").length;
  const readyCount = successfulDocIds.length;
  const idleCount = queue.filter((item) => item.status === "idle").length;

  const handleNavigateToAnalyze = () => {
    if (successfulDocIds.length > 0) {
      setSelectedDocumentIds(successfulDocIds.slice(0, 5));
      router.push("/analyze");
    }
  };

  return (
    <div className="space-y-6 w-full max-w-6xl mx-auto pb-16">
      {/* Top Header */}
      <div className="border-b border-border pb-4">
        <h1 className="text-xl font-bold tracking-tight text-typography-primary">
          Upload & Ingest Documents
        </h1>
        <p className="text-xs text-typography-secondary">
          Upload financial files (PDF, CSV, XLSX) into workspace{" "}
          <strong className="font-mono text-typography-primary">{workspaceId}</strong>.
        </p>
      </div>

      {/* Batch Notice / Limit Alert */}
      {batchNotice && (
        <div className="rounded border border-status-warning/30 bg-status-warningBg p-3 text-xs text-amber-900 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <AlertCircle className="h-4 w-4 text-status-warning flex-shrink-0" />
            <span>{batchNotice}</span>
          </div>
          <button onClick={() => setBatchNotice(null)} className="text-amber-700 hover:text-amber-900">
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      )}

      {/* Active Upload Workspace Guard Notice */}
      {isUploading && activeBatchWorkspace && (
        <div className="rounded border border-primary-200 bg-primary-50/60 p-3 text-xs text-primary-800 flex items-center space-x-2">
          <ShieldAlert className="h-4 w-4 text-primary-600 flex-shrink-0" />
          <span>
            Upload active in workspace <strong className="font-mono">{activeBatchWorkspace}</strong>. Workspace navigation is locked until uploads complete.
          </span>
        </div>
      )}

      {/* 1. Drop Zone */}
      <UploadDropZone
        onFilesSelected={handleFilesSelected}
        disabled={isUploading || queue.length >= MAX_UPLOAD_BATCH_SIZE}
        maxFiles={MAX_UPLOAD_BATCH_SIZE}
      />

      {/* 2. Upload Queue */}
      {queue.length > 0 && (
        <Card className="border-border bg-surface shadow-card">
          <CardHeader className="pb-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <CardTitle className="text-sm font-semibold text-typography-primary">
                Selected Batch ({queue.length} / {MAX_UPLOAD_BATCH_SIZE})
              </CardTitle>
              <CardDescription className="text-xs text-typography-muted">
                {readyCount} ready • {failedCount} failed • {idleCount} pending
              </CardDescription>
            </div>

            {/* Batch Level Controls */}
            <div className="flex items-center space-x-2">
              {idleCount > 0 && (
                <Button
                  variant="primary"
                  size="sm"
                  onClick={handleStartUpload}
                  disabled={isUploading}
                  className="h-8 text-xs"
                >
                  <UploadCloud className="mr-1.5 h-3.5 w-3.5" />
                  <span>{isUploading ? "Processing Batch..." : `Upload (${idleCount})`}</span>
                </Button>
              )}

              {readyCount > 0 && !isUploading && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleClearFinished}
                  className="h-8 text-xs text-typography-muted hover:text-typography-primary"
                >
                  Clear Completed
                </Button>
              )}
            </div>
          </CardHeader>

          <CardContent className="space-y-2.5">
            {queue.map((item) => (
              <UploadQueueItem
                key={item.id}
                item={item}
                onRemove={handleRemoveItem}
                onRetry={handleRetryItem}
                disabled={isUploading}
              />
            ))}
          </CardContent>
        </Card>
      )}

      {/* 3. Navigation Actions after Success */}
      {readyCount > 0 && (
        <Card className="border-border bg-slate-50/70 p-4 shadow-subtle flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center space-x-2 text-xs">
            <CheckCircle2 className="h-4 w-4 text-status-success flex-shrink-0" />
            <span className="text-typography-primary font-medium">
              {readyCount} document{readyCount !== 1 ? "s" : ""} successfully ingested into workspace.
            </span>
          </div>

          <div className="flex items-center space-x-2 w-full sm:w-auto">
            <Link href="/documents" className="w-full sm:w-auto">
              <Button variant="outline" size="sm" className="w-full sm:w-auto text-xs h-8">
                <FileText className="mr-1.5 h-3.5 w-3.5 text-typography-muted" />
                <span>View Documents</span>
              </Button>
            </Link>

            <Button
              variant="primary"
              size="sm"
              onClick={handleNavigateToAnalyze}
              className="w-full sm:w-auto text-xs h-8"
            >
              <Sparkles className="mr-1.5 h-3.5 w-3.5" />
              <span>Analyze Now</span>
              <ArrowRight className="ml-1 h-3.5 w-3.5" />
            </Button>
          </div>
        </Card>
      )}
    </div>
  );
}