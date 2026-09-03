import React, { useState } from "react";
import Link from "next/link";
import ReactMarkdown from "react-markdown";
import { DocumentSummary, QueryResult, QuerySourceChunk } from "@/types/api";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader, CardContent } from "@/components/ui/Card";
import { Modal } from "@/components/ui/Modal";
import {
  FileText,
  FileSpreadsheet,
  CheckCircle2,
  Layers,
  Sparkles,
  ChevronDown,
  ChevronUp,
  X,
  UploadCloud,
  CheckSquare,
  Square,
  ShieldCheck,
  BarChart2,
} from "lucide-react";

interface ScopeSelectorPillBarProps {
  selectedDocIds: string[];
  allDocs: DocumentSummary[];
  maxCount: number;
  onUpdateSelection: (newIds: string[]) => void;
  disabled?: boolean;
}

export function ScopeSelectorPillBar({
  selectedDocIds,
  allDocs,
  maxCount,
  onUpdateSelection,
  disabled = false,
}: ScopeSelectorPillBarProps) {
  const [modalOpen, setModalOpen] = useState(false);
  const [tempSelection, setTempSelection] = useState<string[]>(selectedDocIds);

  const handleOpenModal = () => {
    if (disabled) return;
    setTempSelection(selectedDocIds);
    setModalOpen(true);
  };

  const handleToggleDoc = (id: string) => {
    if (tempSelection.includes(id)) {
      setTempSelection(tempSelection.filter((item) => item !== id));
    } else {
      if (tempSelection.length >= maxCount) return;
      setTempSelection([...tempSelection, id]);
    }
  };

  const handleSaveModal = () => {
    onUpdateSelection(tempSelection);
    setModalOpen(false);
  };

  return (
    <>
      <div className="flex flex-wrap items-center gap-2 rounded-lg border border-border bg-surface p-3 shadow-subtle">
        <div className="flex items-center space-x-1.5 pr-2 border-r border-border">
          <Layers className="h-4 w-4 text-primary-600" />
          <span className="text-xs font-semibold text-typography-primary">Scope:</span>
          <Badge
            variant={selectedDocIds.length > 0 ? "default" : "outline"}
            className="text-[11px] font-mono"
          >
            {selectedDocIds.length} / {maxCount}
          </Badge>
        </div>

        {/* Selected Document Tags */}
        <div className="flex flex-wrap items-center gap-1.5 flex-1">
          {selectedDocIds.length === 0 ? (
            <span className="text-xs text-typography-muted italic">
              No documents selected. Click &quot;Change Scope&quot; to pick 1–5 documents.
            </span>
          ) : (
            selectedDocIds.map((docId) => {
              const docMeta = allDocs.find((d) => d.document_id === docId);
              const displayName = docMeta?.original_filename || `${docId.slice(0, 8)}...`;

              return (
                <span
                  key={docId}
                  className="inline-flex items-center space-x-1.5 rounded border border-primary-200 bg-primary-50 px-2 py-1 text-xs text-primary-900 font-sans"
                >
                  {docMeta?.document_type === "BANK_STATEMENT" ? (
                    <FileSpreadsheet className="h-3 w-3 text-primary-600 flex-shrink-0" />
                  ) : (
                    <FileText className="h-3 w-3 text-typography-muted flex-shrink-0" />
                  )}
                  <span className="truncate max-w-[120px] sm:max-w-[180px] font-medium" title={docMeta?.original_filename || docId}>
                    {displayName}
                  </span>
                  <button
                    type="button"
                    onClick={() => onUpdateSelection(selectedDocIds.filter((id) => id !== docId))}
                    disabled={disabled}
                    className="text-primary-700 hover:text-primary-900 focus:outline-none ml-1"
                    title="Remove from scope"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </span>
              );
            })
          )}
        </div>

        {/* Action Button */}
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={handleOpenModal}
          disabled={disabled || allDocs.length === 0}
          className="h-7 text-xs"
        >
          Change Scope
        </Button>
      </div>

      {/* Scope Adjustment Modal */}
      <Modal isOpen={modalOpen} onClose={() => setModalOpen(false)} title="Select Document Scope">
        <div className="space-y-4 text-xs">
          <p className="text-typography-secondary">
            Select 1 to {maxCount} documents from your library to constrain vector retrieval and analysis.
          </p>

          <div className="max-h-60 overflow-y-auto space-y-1.5 divide-y divide-border pr-1">
            {allDocs.map((doc) => {
              const isChecked = tempSelection.includes(doc.document_id);
              const reachedLimit = tempSelection.length >= maxCount && !isChecked;

              return (
                <div
                  key={doc.document_id}
                  onClick={() => !reachedLimit && handleToggleDoc(doc.document_id)}
                  className={`flex items-center justify-between p-2 rounded cursor-pointer transition-colors ${
                    isChecked ? "bg-primary-50" : reachedLimit ? "opacity-50 cursor-not-allowed" : "hover:bg-slate-50"
                  }`}
                >
                  <div className="flex items-center space-x-2.5 truncate">
                    <button type="button" className="text-primary-600 focus:outline-none">
                      {isChecked ? (
                        <CheckSquare className="h-4 w-4 fill-primary-50 text-primary-600" />
                      ) : (
                        <Square className="h-4 w-4 text-slate-400" />
                      )}
                    </button>
                    <div className="truncate">
                      <p className="text-xs font-semibold text-typography-primary truncate max-w-[280px] font-sans">
                        {doc.original_filename || doc.document_id}
                      </p>
                      <p className="text-[10px] text-typography-muted font-mono">
                        Type: {doc.document_type} • {doc.total_chunks} chunks
                      </p>
                    </div>
                  </div>

                  <Badge variant="outline" className="text-[10px]">
                    {doc.document_type}
                  </Badge>
                </div>
              );
            })}
          </div>

          <div className="pt-3 border-t border-border flex items-center justify-between">
            <span className="text-xs font-mono text-typography-muted">
              {tempSelection.length} / {maxCount} selected
            </span>
            <div className="space-x-2">
              <Button variant="ghost" size="sm" onClick={() => setModalOpen(false)}>
                Cancel
              </Button>
              <Button variant="primary" size="sm" onClick={handleSaveModal}>
                Apply Scope
              </Button>
            </div>
          </div>
        </div>
      </Modal>
    </>
  );
}

interface EvidenceContributionBarProps {
  chunks: QuerySourceChunk[];
  allDocs?: DocumentSummary[];
}

export function EvidenceContributionBar({ chunks, allDocs = [] }: EvidenceContributionBarProps) {
  if (!chunks || chunks.length === 0) return null;

  const total = chunks.length;
  const docCounts: Record<string, { count: number; displayName: string }> = {};

  chunks.forEach((c) => {
    const docId = c.document_id || "Unknown";
    const docMeta = allDocs.find((d) => d.document_id === docId);
    const displayName = docMeta?.original_filename || (docId.length > 12 ? `${docId.slice(0, 8)}...` : docId);

    if (!docCounts[docId]) {
      docCounts[docId] = { count: 0, displayName };
    }
    docCounts[docId].count += 1;
  });

  const distinctDocs = Object.keys(docCounts);
  if (distinctDocs.length <= 1 && total <= 1) return null;

  const colors = ["bg-primary-600", "bg-emerald-600", "bg-amber-600", "bg-purple-600", "bg-slate-600"];

  return (
    <div className="rounded border border-border bg-slate-50/50 p-4 space-y-3">
      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center space-x-1.5">
          <BarChart2 className="h-4 w-4 text-primary-600" />
          <span className="font-semibold text-typography-primary">Retrieved Evidence Scope</span>
        </div>
        <span className="text-xs font-mono text-typography-muted">
          {total} chunk{total > 1 ? "s" : ""} across {distinctDocs.length} document{distinctDocs.length > 1 ? "s" : ""}
        </span>
      </div>

      {/* Proportional Segmented Bar */}
      <div className="flex h-2.5 w-full overflow-hidden rounded-full bg-slate-200">
        {distinctDocs.map((docId, idx) => {
          const info = docCounts[docId];
          const pct = (info.count / total) * 100;
          return (
            <div
              key={docId}
              style={{ width: `${pct}%` }}
              className={`${colors[idx % colors.length]} transition-all duration-300`}
              title={`${info.displayName}: ${info.count} chunks (${pct.toFixed(0)}%)`}
            />
          );
        })}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap items-center gap-3 pt-0.5">
        {distinctDocs.map((docId, idx) => {
          const info = docCounts[docId];
          return (
            <div key={docId} className="flex items-center space-x-1.5 text-xs font-mono text-typography-muted">
              <span className={`h-2.5 w-2.5 rounded-full ${colors[idx % colors.length]}`} />
              <span className="truncate max-w-[180px]" title={info.displayName}>{info.displayName}:</span>
              <strong className="text-typography-primary">{info.count}</strong>
            </div>
          );
        })}
      </div>
    </div>
  );
}

interface AnswerCardProps {
  queryResult: QueryResult;
  onReset: () => void;
  allDocs?: DocumentSummary[];
}

export function AnswerCard({ queryResult, onReset, allDocs = [] }: AnswerCardProps) {
  return (
    <Card className="border-border bg-surface shadow-card overflow-hidden">
      <CardHeader className="border-b border-border bg-slate-50/50 pb-3.5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <Badge variant="success" className="text-xs">
                <CheckCircle2 className="mr-1 h-3.5 w-3.5" />
                Grounded Answer
              </Badge>
              <span className="text-xs font-mono text-typography-muted">
                {(queryResult.processing_time_ms / 1000).toFixed(2)}s processing
              </span>
            </div>
            <p className="text-sm font-semibold text-typography-secondary">
              Query: &quot;{queryResult.query}&quot;
            </p>
          </div>

          <Button variant="ghost" size="sm" onClick={onReset} className="h-8 text-xs text-typography-muted hover:text-typography-primary">
            New Query
          </Button>
        </div>
      </CardHeader>

      <CardContent className="p-5 sm:p-6 space-y-6">
        {/* Rendered Markdown Answer */}
        <div className="prose prose-slate max-w-4xl text-sm sm:text-base text-typography-primary leading-relaxed">
          <ReactMarkdown>{queryResult.answer}</ReactMarkdown>
        </div>

        {/* Visual Summary: Evidence Contribution */}
        <EvidenceContributionBar chunks={queryResult.source_chunks || []} allDocs={allDocs} />

        {/* Source Evidence Citations */}
        <SourceChunksList chunks={queryResult.source_chunks || []} allDocs={allDocs} />
      </CardContent>
    </Card>
  );
}

interface SourceChunksListProps {
  chunks: QuerySourceChunk[];
  allDocs?: DocumentSummary[];
}

export function SourceChunksList({ chunks, allDocs = [] }: SourceChunksListProps) {
  const [expanded, setExpanded] = useState<boolean>(true);

  if (!chunks || chunks.length === 0) {
    return (
      <div className="rounded border border-dashed border-border p-4 text-sm text-typography-muted">
        No source evidence chunks retrieved for this inquiry.
      </div>
    );
  }

  return (
    <div className="space-y-3 pt-3.5 border-t border-border">
      <div
        className="flex items-center justify-between cursor-pointer select-none"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center space-x-2">
          <ShieldCheck className="h-4 w-4 text-primary-600" />
          <h4 className="text-sm font-bold text-typography-primary tracking-tight">
            Retrieved Source Evidence ({chunks.length})
          </h4>
        </div>
        <button
          type="button"
          className="text-typography-muted hover:text-typography-primary text-xs flex items-center space-x-1"
        >
          <span>{expanded ? "Hide" : "Show"} Evidence</span>
          {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </button>
      </div>

      {expanded && (
        <div className="space-y-3">
          {chunks.map((chunk) => {
            const docMeta = allDocs.find((d) => d.document_id === chunk.document_id);
            const displayDocName = docMeta?.original_filename || (chunk.document_id.length > 12 ? `${chunk.document_id.slice(0, 8)}...` : chunk.document_id);

            return (
              <div
                key={chunk.chunk_id}
                className="rounded border border-border bg-slate-50/70 p-3.5 text-xs space-y-2 shadow-subtle"
              >
                {/* Chunk Header Metadata */}
                <div className="flex flex-wrap items-center justify-between text-xs font-mono text-typography-muted border-b border-border/60 pb-1.5 gap-1">
                  <span>
                    Document: <strong className="text-typography-primary font-sans">{displayDocName}</strong> • Chunk #{chunk.chunk_index}
                  </span>
                  <span>
                    Distance:{" "}
                    <strong className="text-typography-primary">
                      {chunk.distance !== null && chunk.distance !== undefined
                        ? chunk.distance.toFixed(4)
                        : "Not available"}
                    </strong>
                  </span>
                </div>

                {/* Exact Unaltered Evidence Snippet */}
                <p className="font-mono text-xs text-typography-secondary bg-surface p-2.5 rounded border border-border/80 whitespace-pre-wrap leading-relaxed break-words">
                  {chunk.snippet}
                </p>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export function AnalyzeEmptyState({ docCount }: { docCount: number }) {
  if (docCount === 0) {
    return (
      <div className="rounded-lg border border-dashed border-border bg-surface p-10 text-center shadow-subtle space-y-4 max-w-lg mx-auto my-6">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary-50 text-primary-600 mx-auto">
          <FileText className="h-6 w-6" />
        </div>
        <div className="space-y-1">
          <h3 className="text-base font-bold text-typography-primary">Workspace has no documents</h3>
          <p className="text-xs text-typography-secondary">
            Upload financial files first to begin asking grounded questions across statement and invoice data.
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

  return (
    <div className="rounded-lg border border-dashed border-border bg-surface p-8 text-center text-xs text-typography-muted space-y-2">
      <Sparkles className="h-6 w-6 text-primary-600 mx-auto mb-1 opacity-70" />
      <p className="font-semibold text-typography-primary">Ready for Grounded Analysis</p>
      <p>
        Select 1 to 5 documents from the scope bar above and enter a question to inspect verifiable source evidence.
      </p>
    </div>
  );
}