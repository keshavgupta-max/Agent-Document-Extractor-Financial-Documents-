"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { useWorkspace } from "@/context/WorkspaceContext";
import { getWorkspaceDocuments } from "@/api/documents";
import { executeGroundedQuery } from "@/api/query";
import { QueryResult } from "@/types/api";
import { MAX_SELECTION_DOCUMENTS } from "@/lib/constants";
import { saveAnalysisHistory } from "@/lib/history";
import {
  ScopeSelectorPillBar,
  AnswerCard,
  AnalyzeEmptyState,
} from "@/components/analyze/AnalyzeComponents";
import { Button } from "@/components/ui/Button";
import { Card, CardContent } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import {
  Search,
  Sparkles,
  ArrowRight,
  AlertCircle,
  Loader2,
} from "lucide-react";

function AnalyzeContent() {
  const searchParams = useSearchParams();
  const { workspaceId, isInitialized, selectedDocumentIds, setSelectedDocumentIds } = useWorkspace();

  const [questionInput, setQuestionInput] = useState<string>("");
  const [isQuerying, setIsQuerying] = useState<boolean>(false);
  const [queryResult, setQueryResult] = useState<QueryResult | null>(null);
  const [queryError, setQueryError] = useState<string | null>(null);

  // Initialize query text from URL search param if present (e.g. from Dashboard Ask AI)
  useEffect(() => {
    const q = searchParams.get("q");
    if (q && q.trim()) {
      setQuestionInput(q.trim());
    }
  }, [searchParams]);

  // Fetch available workspace documents for the Scope Selector
  const {
    data: docsData,
    isLoading: docsLoading,
  } = useQuery({
    queryKey: ["documents", workspaceId],
    queryFn: () => getWorkspaceDocuments(workspaceId),
    enabled: Boolean(workspaceId && isInitialized),
  });

  const allDocuments = docsData?.documents || [];

  const handleQuerySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setQueryError(null);

    const cleanQuery = questionInput.trim();
    if (!cleanQuery) {
      setQueryError("Please enter a question to analyze.");
      return;
    }

    if (selectedDocumentIds.length === 0) {
      setQueryError("Please select at least 1 document (up to 5) in the scope bar above.");
      return;
    }

    if (selectedDocumentIds.length > MAX_SELECTION_DOCUMENTS) {
      setQueryError(`Document scope cannot exceed ${MAX_SELECTION_DOCUMENTS} documents.`);
      return;
    }

    setIsQuerying(true);

    try {
      const response = await executeGroundedQuery({
        workspace_id: workspaceId,
        selected_document_ids: selectedDocumentIds,
        query: cleanQuery,
        top_k: 5,
      });

      if (response.success && response.final_output) {
        setQueryResult(response.final_output);

        // Save successful query to local analysis history
        saveAnalysisHistory({
          id: `hist_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`,
          workspaceId,
          question: cleanQuery,
          selectedDocumentIds,
          answer: response.final_output.answer,
          timestamp: new Date().toISOString(),
          sourceChunks: response.final_output.source_chunks || [],
          processingTimeMs: response.final_output.processing_time_ms,
        });
      } else {
        setQueryError(response.error_message || "Unable to complete grounded analysis.");
      }
    } catch {
      setQueryError("Unable to complete the analysis. Please try again.");
    } finally {
      setIsQuerying(false);
    }
  };

  const handleResetQuery = () => {
    setQueryResult(null);
    setQueryError(null);
    setQuestionInput("");
  };

  if (!isInitialized || docsLoading) {
    return (
      <div className="space-y-6 max-w-4xl mx-auto">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-12 w-full rounded-lg" />
        <Skeleton className="h-24 w-full rounded-lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto pb-16">
      {/* Top Header */}
      <div className="border-b border-border pb-4">
        <h1 className="text-xl font-bold tracking-tight text-typography-primary">
          Analyze / Ask AI
        </h1>
        <p className="text-xs text-typography-secondary">
          Ask grounded questions across your selected financial documents with verifiable source citations.
        </p>
      </div>

      {/* 1. Scope Selector Pill Bar */}
      <ScopeSelectorPillBar
        selectedDocIds={selectedDocumentIds}
        allDocs={allDocuments}
        maxCount={MAX_SELECTION_DOCUMENTS}
        onUpdateSelection={setSelectedDocumentIds}
        disabled={isQuerying}
      />

      {/* 2. Query Composer Form */}
      <Card className="border-border bg-surface shadow-card">
        <CardContent className="p-4 sm:p-5">
          <form onSubmit={handleQuerySubmit} className="space-y-3">
            <div className="relative">
              <Search className="absolute left-3 top-3 h-4 w-4 text-typography-muted" />
              <textarea
                value={questionInput}
                onChange={(e) => {
                  setQuestionInput(e.target.value);
                  if (queryError) setQueryError(null);
                }}
                disabled={isQuerying || allDocuments.length === 0}
                placeholder="Ask a question about the selected documents (e.g. 'What is the total credit amount?' or 'What is the grand total for invoice #102?')"
                rows={3}
                className="w-full rounded border border-border bg-surface pl-9 pr-3 py-2.5 text-xs text-typography-primary placeholder:text-typography-muted focus:outline-none focus:ring-2 focus:ring-primary-500 shadow-subtle resize-none"
              />
            </div>

            {/* Submit Action */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-1">
              <span className="text-[11px] text-typography-muted">
                Answers are grounded strictly in the {selectedDocumentIds.length} scoped document{selectedDocumentIds.length !== 1 ? "s" : ""}.
              </span>

              <Button
                type="submit"
                variant="primary"
                size="sm"
                disabled={isQuerying || allDocuments.length === 0 || !questionInput.trim()}
                className="w-full sm:w-auto h-8 text-xs"
              >
                {isQuerying ? (
                  <>
                    <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />
                    <span>Analyzing Documents...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="mr-1.5 h-3.5 w-3.5" />
                    <span>Run Analysis</span>
                    <ArrowRight className="ml-1 h-3.5 w-3.5" />
                  </>
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Error Banner */}
      {queryError && (
        <div className="rounded border border-status-error/30 bg-status-errorBg p-3.5 text-xs text-slate-800 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <AlertCircle className="h-4 w-4 text-status-error flex-shrink-0" />
            <span>{queryError}</span>
          </div>
          <button
            onClick={() => setQueryError(null)}
            className="text-slate-500 hover:text-slate-800 text-xs"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* 3. Answer Display or Empty State */}
      {isQuerying ? (
        <Card className="border-border bg-surface p-8 text-center space-y-3">
          <Loader2 className="h-8 w-8 animate-spin text-primary-600 mx-auto" />
          <p className="text-xs font-semibold text-typography-primary">
            Retrieving evidence & generating grounded answer...
          </p>
          <p className="text-[11px] text-typography-muted">
            Matching vector embeddings across {selectedDocumentIds.length} selected document chunks.
          </p>
        </Card>
      ) : queryResult ? (
        <AnswerCard queryResult={queryResult} onReset={handleResetQuery} />
      ) : (
        <AnalyzeEmptyState docCount={allDocuments.length} />
      )}
    </div>
  );
}

function AnalyzeFallback() {
  return (
    <div className="space-y-6 max-w-4xl mx-auto pb-16">
      <Skeleton className="h-8 w-48" />
      <Skeleton className="h-12 w-full rounded-lg" />
      <Skeleton className="h-28 w-full rounded-lg" />
    </div>
  );
}

export default function AnalyzePage() {
  return (
    <Suspense fallback={<AnalyzeFallback />}>
      <AnalyzeContent />
    </Suspense>
  );
}