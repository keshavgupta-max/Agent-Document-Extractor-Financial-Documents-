"use client";

import React, { useState, useMemo } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useWorkspace } from "@/context/WorkspaceContext";
import { getWorkspaceDocuments, deleteDocument } from "@/api/documents";
import { DocumentSummary } from "@/types/api";
import { MAX_SELECTION_DOCUMENTS } from "@/lib/constants";
import {
  DocumentSelectionBar,
  DocumentMetadataModal,
  DeleteDocumentModal,
  DocumentsEmptyState,
  DocumentsErrorState,
} from "@/components/documents/DocumentComponents";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import {
  Search,
  Filter,
  ArrowUpDown,
  FileText,
  FileSpreadsheet,
  Eye,
  Sparkles,
  UploadCloud,
  CheckSquare,
  Square,
  AlertCircle,
  X,
  Trash2,
} from "lucide-react";

type SortOption = "id_asc" | "id_desc" | "type_asc" | "chunks_desc" | "chunks_asc";

export default function DocumentsPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { workspaceId, isInitialized, selectedDocumentIds, setSelectedDocumentIds } = useWorkspace();

  const [searchQuery, setSearchQuery] = useState<string>("");
  const [filterType, setFilterType] = useState<string>("ALL");
  const [sortBy, setSortBy] = useState<SortOption>("id_asc");
  const [inspectDoc, setInspectDoc] = useState<DocumentSummary | null>(null);
  const [deleteDocTarget, setDeleteDocTarget] = useState<DocumentSummary | null>(null);
  const [isDeleting, setIsDeleting] = useState<boolean>(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [limitNotice, setLimitNotice] = useState<string | null>(null);

  // Fetch Documents for current workspace
  const {
    data: docsData,
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: ["documents", workspaceId],
    queryFn: () => getWorkspaceDocuments(workspaceId),
    enabled: Boolean(workspaceId && isInitialized),
  });

  const documents = useMemo(() => docsData?.documents ?? [], [docsData]);

  // Client-side search, filter, and deterministic sorting
  const filteredDocuments = useMemo(() => {
    return documents
      .filter((doc) => {
        const matchesSearch =
          (doc.original_filename && doc.original_filename.toLowerCase().includes(searchQuery.toLowerCase().trim())) ||
          doc.document_id.toLowerCase().includes(searchQuery.toLowerCase().trim()) ||
          doc.document_type.toLowerCase().includes(searchQuery.toLowerCase().trim());

        const normalizedType = doc.document_type.replace(/\s+/g, "_").toUpperCase();
        const matchesType =
          filterType === "ALL" || normalizedType === filterType;

        return matchesSearch && matchesType;
      })
      .sort((a, b) => {
        if (sortBy === "id_asc") {
          const nameA = a.original_filename || a.document_id;
          const nameB = b.original_filename || b.document_id;
          return nameA.localeCompare(nameB);
        }
        if (sortBy === "id_desc") {
          const nameA = a.original_filename || a.document_id;
          const nameB = b.original_filename || b.document_id;
          return nameB.localeCompare(nameA);
        }
        if (sortBy === "type_asc") return a.document_type.localeCompare(b.document_type);
        if (sortBy === "chunks_desc") return b.total_chunks - a.total_chunks;
        if (sortBy === "chunks_asc") return a.total_chunks - b.total_chunks;
        return 0;
      });
  }, [documents, searchQuery, filterType, sortBy]);

  // Selection toggle handling with 5-doc limit enforcement
  const toggleSelectDoc = (docId: string) => {
    setLimitNotice(null);
    if (selectedDocumentIds.includes(docId)) {
      setSelectedDocumentIds(selectedDocumentIds.filter((id) => id !== docId));
    } else {
      if (selectedDocumentIds.length >= MAX_SELECTION_DOCUMENTS) {
        setLimitNotice(`You can analyze up to ${MAX_SELECTION_DOCUMENTS} documents at a time.`);
        return;
      }
      setSelectedDocumentIds([...selectedDocumentIds, docId]);
    }
  };

  const handleClearSelection = () => {
    setSelectedDocumentIds([]);
    setLimitNotice(null);
  };

  const handleAnalyzeSelected = () => {
    if (selectedDocumentIds.length > 0) {
      router.push("/analyze");
    }
  };

  const handleAnalyzeSingleDoc = (docId: string) => {
    setSelectedDocumentIds([docId]);
    router.push("/analyze");
  };

  const handleConfirmDelete = async () => {
    if (!deleteDocTarget) return;

    setIsDeleting(true);
    setDeleteError(null);

    try {
      await deleteDocument(deleteDocTarget.document_id, workspaceId);

      // 1. Remove deleted document from active selection scope
      setSelectedDocumentIds(selectedDocumentIds.filter((id) => id !== deleteDocTarget.document_id));

      // 2. Invalidate workspace queries
      queryClient.invalidateQueries({ queryKey: ["documents", workspaceId] });
      queryClient.invalidateQueries({ queryKey: ["analytics-summary", workspaceId] });
      queryClient.invalidateQueries({ queryKey: ["analytics-transactions", workspaceId] });

      setDeleteDocTarget(null);
    } catch {
      setDeleteError("Unable to delete document. Please try again.");
    } finally {
      setIsDeleting(false);
    }
  };

  if (!isInitialized || isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center pb-2">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-9 w-32" />
        </div>
        <Skeleton className="h-12 w-full rounded-lg" />
        <div className="space-y-2">
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="space-y-4">
        <DocumentsErrorState onRetry={() => refetch()} />
      </div>
    );
  }

  if (documents.length === 0) {
    return <DocumentsEmptyState />;
  }

  return (
    <div className="space-y-6 pb-16">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-typography-primary">
            Documents Library
          </h1>
          <p className="text-xs text-typography-secondary">
            Manage and select documents for multi-document AI analysis. (Max {MAX_SELECTION_DOCUMENTS} selectable)
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <Link href="/upload">
            <Button variant="primary" size="sm">
              <UploadCloud className="mr-1.5 h-4 w-4" />
              <span>Upload Document</span>
            </Button>
          </Link>
        </div>
      </div>

      {/* Delete Error Alert */}
      {deleteError && (
        <div className="rounded border border-status-error/30 bg-status-errorBg p-3 text-xs text-slate-800 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <AlertCircle className="h-4 w-4 text-status-error flex-shrink-0" />
            <span>{deleteError}</span>
          </div>
          <button onClick={() => setDeleteError(null)} className="text-slate-500 hover:text-slate-800 text-xs">
            Dismiss
          </button>
        </div>
      )}

      {/* 5-Document Max Limit Alert */}
      {limitNotice && (
        <div className="rounded border border-status-warning/30 bg-status-warningBg p-3 text-xs text-amber-900 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <AlertCircle className="h-4 w-4 text-status-warning flex-shrink-0" />
            <span>{limitNotice}</span>
          </div>
          <button onClick={() => setLimitNotice(null)} className="text-amber-700 hover:text-amber-900">
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      )}

      {/* Search, Filter & Sort Controls */}
      <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
        {/* Search */}
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-typography-muted" />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by Document Name, ID or Type..."
            className="pl-9 h-9 text-xs"
          />
        </div>

        {/* Filter by Type & Sort */}
        <div className="flex items-center space-x-2">
          {/* Type Filter */}
          <div className="flex items-center space-x-1.5">
            <Filter className="h-3.5 w-3.5 text-typography-muted" />
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="h-9 rounded border border-border bg-surface px-2.5 text-xs text-typography-primary focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:outline-none font-medium"
            >
              <option value="ALL">All Types ({documents.length})</option>
              <option value="BANK_STATEMENT">Bank Statements</option>
              <option value="INVOICE">Invoices</option>
              <option value="UNKNOWN">Unknown</option>
            </select>
          </div>

          {/* Sort By */}
          <div className="flex items-center space-x-1.5">
            <ArrowUpDown className="h-3.5 w-3.5 text-typography-muted" />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as SortOption)}
              className="h-9 rounded border border-border bg-surface px-2.5 text-xs text-typography-primary focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:outline-none font-medium"
            >
              <option value="id_asc">Name / ID (A → Z)</option>
              <option value="id_desc">Name / ID (Z → A)</option>
              <option value="type_asc">Type</option>
              <option value="chunks_desc">Chunks (High → Low)</option>
              <option value="chunks_asc">Chunks (Low → High)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Documents Table */}
      <Card className="border-border bg-surface shadow-card overflow-hidden">
        {filteredDocuments.length === 0 ? (
          <div className="p-8 text-center text-xs text-typography-muted">
            No documents matching the current search/filter criteria.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs" aria-label="Documents Library">
              <thead className="border-b border-border bg-slate-50 font-semibold text-typography-muted uppercase">
                <tr>
                  <th scope="col" className="w-12 px-4 py-3 text-center">
                    <span className="sr-only">Select</span>
                  </th>
                  <th scope="col" className="px-4 py-3">Document Name / ID</th>
                  <th scope="col" className="px-4 py-3">Type</th>
                  <th scope="col" className="px-4 py-3">Chunks</th>
                  <th scope="col" className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border font-mono">
                {filteredDocuments.map((doc) => {
                  const isSelected = selectedDocumentIds.includes(doc.document_id);

                  return (
                    <tr
                      key={doc.document_id}
                      className={`hover:bg-slate-50/70 transition-colors ${
                        isSelected ? "bg-primary-50/40" : ""
                      }`}
                    >
                      {/* Selection Toggle */}
                      <td className="px-4 py-3 text-center">
                        <button
                          type="button"
                          onClick={() => toggleSelectDoc(doc.document_id)}
                          aria-label={`Select document ${doc.original_filename || doc.document_id}`}
                          aria-pressed={isSelected}
                          className="text-primary-600 hover:text-primary-700 focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:outline-none rounded p-0.5"
                        >
                          {isSelected ? (
                            <CheckSquare className="h-4 w-4 fill-primary-50 text-primary-600" />
                          ) : (
                            <Square className="h-4 w-4 text-slate-400" />
                          )}
                        </button>
                      </td>

                      {/* Document Name & ID */}
                      <td className="px-4 py-3 text-typography-primary font-medium">
                        <div className="flex items-center space-x-2">
                          {doc.document_type === "BANK_STATEMENT" ? (
                            <FileSpreadsheet className="h-4 w-4 text-primary-600 flex-shrink-0" />
                          ) : (
                            <FileText className="h-4 w-4 text-typography-muted flex-shrink-0" />
                          )}
                          <div className="flex flex-col truncate max-w-[240px] sm:max-w-md">
                            <span
                              className="font-semibold text-xs text-typography-primary truncate font-sans"
                              title={doc.original_filename || doc.document_id}
                            >
                              {doc.original_filename || doc.document_id}
                            </span>
                            <span className="text-[10px] font-mono text-typography-muted truncate">
                              {doc.document_id}
                            </span>
                          </div>
                        </div>
                      </td>

                      {/* Document Type */}
                      <td className="px-4 py-3 font-sans">
                        <Badge
                          variant={
                            doc.document_type === "BANK_STATEMENT"
                              ? "success"
                              : doc.document_type === "INVOICE"
                              ? "default"
                              : "outline"
                          }
                          className="text-[10px] px-2 py-0.5"
                        >
                          {doc.document_type}
                        </Badge>
                      </td>

                      {/* Total Chunks */}
                      <td className="px-4 py-3 text-typography-secondary font-sans">
                        {doc.total_chunks} chunks
                      </td>

                      {/* Actions */}
                      <td className="px-4 py-3 text-right font-sans space-x-1.5">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setInspectDoc(doc)}
                          className="h-7 px-2 text-xs"
                          title="View metadata"
                        >
                          <Eye className="h-3.5 w-3.5 mr-1" />
                          <span>View</span>
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleAnalyzeSingleDoc(doc.document_id)}
                          className="h-7 px-2 text-xs text-primary-700 bg-primary-50/50 hover:bg-primary-100"
                          title="Analyze document"
                        >
                          <Sparkles className="h-3.5 w-3.5 mr-1 text-primary-600" />
                          <span>Analyze</span>
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setDeleteDocTarget(doc)}
                          className="h-7 px-2 text-xs text-status-error hover:bg-red-50 hover:text-red-700"
                          title="Delete document"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </Button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Floating Selection Bar */}
      <DocumentSelectionBar
        selectedCount={selectedDocumentIds.length}
        maxCount={MAX_SELECTION_DOCUMENTS}
        onClear={handleClearSelection}
        onAnalyze={handleAnalyzeSelected}
      />

      {/* Metadata Inspection Dialog */}
      <DocumentMetadataModal
        document={inspectDoc}
        isOpen={Boolean(inspectDoc)}
        onClose={() => setInspectDoc(null)}
      />

      {/* Delete Confirmation Dialog */}
      <DeleteDocumentModal
        document={deleteDocTarget}
        isOpen={Boolean(deleteDocTarget)}
        onClose={() => setDeleteDocTarget(null)}
        onConfirm={handleConfirmDelete}
        isDeleting={isDeleting}
      />
    </div>
  );
}