"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { useWorkspace } from "@/context/WorkspaceContext";
import { getWorkspaceDocuments } from "@/api/documents";
import { getFinancialSummary, getDocumentTransactions } from "@/api/analytics";
import { formatCurrency } from "@/lib/utils";
import {
  SummaryCard,
  CashFlowBar,
  StatementActivityTable,
  DashboardEmptyState,
  DashboardErrorState,
} from "@/components/dashboard/DashboardComponents";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { Badge } from "@/components/ui/Badge";
import {
  DollarSign,
  TrendingUp,
  TrendingDown,
  Layers,
  FileText,
  FileSpreadsheet,
  Search,
  ArrowRight,
  UploadCloud,
  Sparkles,
} from "lucide-react";

export default function DashboardPage() {
  const router = useRouter();
  const { workspaceId, isInitialized } = useWorkspace();
  const [selectedStatementId, setSelectedStatementId] = useState<string | null>(null);
  const [askAiQuery, setAskAiQuery] = useState<string>("");

  // 1. Fetch Workspace Documents
  const {
    data: docsData,
    isLoading: docsLoading,
    isError: docsError,
    refetch: refetchDocs,
  } = useQuery({
    queryKey: ["documents", workspaceId],
    queryFn: () => getWorkspaceDocuments(workspaceId),
    enabled: Boolean(workspaceId && isInitialized),
  });

  const documents = docsData?.documents || [];
  const docIds = documents.map((d) => d.document_id);

  // Identify Bank Statement documents deterministically
  const statementDocs = documents.filter((d) => d.document_type === "BANK_STATEMENT");
  const invoiceDocs = documents.filter((d) => d.document_type === "INVOICE");

  // Determine active statement ID for Statement Activity viewing
  const activeStatementId =
    selectedStatementId && statementDocs.some((d) => d.document_id === selectedStatementId)
      ? selectedStatementId
      : statementDocs.length > 0
      ? statementDocs[0].document_id
      : null;

  // 2. Fetch Financial Summary across all scoped documents
  const {
    data: summaryData,
    isLoading: summaryLoading,
    isError: summaryError,
    refetch: refetchSummary,
  } = useQuery({
    queryKey: ["analytics-summary", workspaceId, docIds],
    queryFn: () => getFinancialSummary(workspaceId, docIds),
    enabled: docIds.length > 0,
  });

  // 3. Fetch Transactions for the selected Bank Statement
  const {
    data: txnData,
    isLoading: txnLoading,
  } = useQuery({
    queryKey: ["analytics-transactions", workspaceId, activeStatementId],
    queryFn: () => getDocumentTransactions(workspaceId, activeStatementId!, 5, 0),
    enabled: Boolean(activeStatementId),
  });

  const handleAskAiSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (askAiQuery.trim()) {
      router.push(`/analyze?q=${encodeURIComponent(askAiQuery.trim())}`);
    } else {
      router.push("/analyze");
    }
  };

  if (!isInitialized || docsLoading) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center pb-2">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-9 w-32" />
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Skeleton className="h-28 rounded-lg" />
          <Skeleton className="h-28 rounded-lg" />
          <Skeleton className="h-28 rounded-lg" />
          <Skeleton className="h-28 rounded-lg" />
        </div>
        <Skeleton className="h-64 rounded-lg" />
      </div>
    );
  }

  if (docsError) {
    return (
      <div className="space-y-4">
        <DashboardErrorState onRetry={() => refetchDocs()} />
      </div>
    );
  }

  if (documents.length === 0) {
    return <DashboardEmptyState />;
  }

  const currency = summaryData?.currency || "INR";

  return (
    <div className="space-y-6">
      {/* Top Header & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-typography-primary">
            Financial Overview
          </h1>
          <p className="text-xs text-typography-secondary">
            Workspace metrics derived from {documents.length} ingested document{documents.length !== 1 ? "s" : ""}.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <Link href="/upload">
            <Button variant="outline" size="sm">
              <UploadCloud className="mr-1.5 h-4 w-4 text-typography-muted" />
              <span>Upload</span>
            </Button>
          </Link>
          <Link href="/analyze">
            <Button variant="primary" size="sm">
              <Sparkles className="mr-1.5 h-4 w-4" />
              <span>Analyze Docs</span>
            </Button>
          </Link>
        </div>
      </div>

      {summaryError && <DashboardErrorState onRetry={() => refetchSummary()} />}

      {/* 1. Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <SummaryCard
          title="Total Credits"
          value={
            summaryLoading
              ? "Loading..."
              : summaryData?.total_credit_amount !== null && summaryData?.total_credit_amount !== undefined
              ? formatCurrency(summaryData.total_credit_amount, currency)
              : "Not available"
          }
          subtitle="Inflow deposits"
          icon={<DollarSign className="h-4 w-4 text-status-success" />}
        />

        <SummaryCard
          title="Total Debits"
          value={
            summaryLoading
              ? "Loading..."
              : summaryData?.total_debit_amount !== null && summaryData?.total_debit_amount !== undefined
              ? formatCurrency(summaryData.total_debit_amount, currency)
              : "Not available"
          }
          subtitle="Outflow expenses"
          icon={<TrendingDown className="h-4 w-4 text-typography-muted" />}
        />

        <SummaryCard
          title="Net Cash Flow"
          value={
            summaryLoading
              ? "Loading..."
              : summaryData?.net_cash_flow !== null && summaryData?.net_cash_flow !== undefined
              ? formatCurrency(summaryData.net_cash_flow, currency)
              : "Not available"
          }
          subtitle="Credits minus Debits"
          icon={<TrendingUp className="h-4 w-4 text-primary-600" />}
          trend={
            summaryData?.net_cash_flow !== null && summaryData?.net_cash_flow !== undefined
              ? summaryData.net_cash_flow >= 0
                ? "up"
                : "down"
              : "neutral"
          }
        />

        <SummaryCard
          title="Documents"
          value={documents.length.toString()}
          subtitle={`${statementDocs.length} Statements • ${invoiceDocs.length} Invoices`}
          icon={<Layers className="h-4 w-4 text-typography-secondary" />}
        />
      </div>

      {/* 2. Main Analytics Grid: Activity vs Invoices/Balances */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column (2/3): Volume Visualization & Statement Activity */}
        <div className="lg:col-span-2 space-y-6">
          {/* Credit vs Debit Proportional Volume */}
          <Card className="border-border bg-surface shadow-card">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-semibold text-typography-primary">
                Credit vs Debit Distribution
              </CardTitle>
              <CardDescription className="text-xs text-typography-muted">
                Workspace aggregate volume comparison across statement data.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {summaryLoading ? (
                <Skeleton className="h-16 w-full rounded" />
              ) : (
                <CashFlowBar
                  credits={summaryData?.total_credit_amount ?? null}
                  debits={summaryData?.total_debit_amount ?? null}
                  currency={currency}
                />
              )}
            </CardContent>
          </Card>

          {/* Statement Activity Section */}
          <Card className="border-border bg-surface shadow-card">
            <CardHeader className="pb-3 flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-sm font-semibold text-typography-primary">
                  Statement Activity
                </CardTitle>
                <CardDescription className="text-xs text-typography-muted">
                  Normalized transactions extracted from statement records.
                </CardDescription>
              </div>

              {/* Statement Selector if multiple statements exist */}
              {statementDocs.length > 1 && (
                <div className="flex items-center space-x-2">
                  <label htmlFor="statement-select" className="text-xs text-typography-muted font-medium">
                    Statement:
                  </label>
                  <select
                    id="statement-select"
                    value={activeStatementId || ""}
                    onChange={(e) => setSelectedStatementId(e.target.value)}
                    className="h-8 rounded border border-border bg-surface px-2 text-xs text-typography-primary focus:outline-none focus:ring-1 focus:ring-primary-500 font-mono"
                  >
                    {statementDocs.map((doc, idx) => (
                      <option key={doc.document_id} value={doc.document_id}>
                        Statement #{idx + 1} ({doc.document_id.slice(0, 8)}...)
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </CardHeader>

            <CardContent>
              {txnLoading ? (
                <div className="space-y-2">
                  <Skeleton className="h-8 w-full" />
                  <Skeleton className="h-8 w-full" />
                  <Skeleton className="h-8 w-full" />
                </div>
              ) : (
                <StatementActivityTable
                  transactions={txnData?.transactions || []}
                  totalCount={txnData?.total_transactions || 0}
                  currency={currency}
                />
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right Column (1/3): Balances, Invoice Overview, & Document Mix */}
        <div className="space-y-6">
          {/* Statement Balances Card */}
          <Card className="border-border bg-surface shadow-card">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-semibold text-typography-primary">
                Statement Balances
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 font-mono text-xs">
              <div className="flex justify-between items-center border-b border-border pb-2">
                <span className="text-typography-muted font-sans">Opening Balance:</span>
                <span className="font-semibold text-typography-primary">
                  {summaryData?.opening_balance !== null && summaryData?.opening_balance !== undefined
                    ? formatCurrency(summaryData.opening_balance, currency)
                    : "Not available"}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-typography-muted font-sans">Closing Balance:</span>
                <span className="font-semibold text-typography-primary">
                  {summaryData?.closing_balance !== null && summaryData?.closing_balance !== undefined
                    ? formatCurrency(summaryData.closing_balance, currency)
                    : "Not available"}
                </span>
              </div>
            </CardContent>
          </Card>

          {/* Invoice Aggregate Overview */}
          <Card className="border-border bg-surface shadow-card">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-semibold text-typography-primary">
                  Invoice Summary
                </CardTitle>
                <Badge variant="outline" className="text-[10px]">
                  {invoiceDocs.length} Invoice{invoiceDocs.length !== 1 ? "s" : ""}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-2.5 text-xs">
              <div className="flex justify-between items-center">
                <span className="text-typography-muted">Combined Subtotal:</span>
                <span className="font-mono font-medium text-typography-primary">
                  {summaryData?.invoice_subtotal !== null && summaryData?.invoice_subtotal !== undefined
                    ? formatCurrency(summaryData.invoice_subtotal, currency)
                    : "Not available"}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-typography-muted">Combined Tax:</span>
                <span className="font-mono font-medium text-typography-primary">
                  {summaryData?.invoice_tax !== null && summaryData?.invoice_tax !== undefined
                    ? formatCurrency(summaryData.invoice_tax, currency)
                    : "Not available"}
                </span>
              </div>
              <div className="border-t border-border pt-2 flex justify-between items-center font-bold">
                <span className="text-typography-primary">Combined Grand Total:</span>
                <span className="font-mono text-primary-700">
                  {summaryData?.invoice_grand_total !== null && summaryData?.invoice_grand_total !== undefined
                    ? formatCurrency(summaryData.invoice_grand_total, currency)
                    : "Not available"}
                </span>
              </div>
            </CardContent>
          </Card>

          {/* Document Mix Pill Overview */}
          <Card className="border-border bg-surface shadow-card p-4 space-y-2">
            <span className="text-xs font-semibold text-typography-muted uppercase tracking-wider">
              Document Scope
            </span>
            <div className="flex flex-wrap gap-1.5 pt-1">
              {documents.map((d) => (
                <span
                  key={d.document_id}
                  className="inline-flex items-center rounded border border-border bg-slate-50 px-2 py-1 text-[11px] font-mono text-typography-secondary truncate max-w-[200px]"
                  title={`ID: ${d.document_id} (${d.document_type})`}
                >
                  {d.document_type === "BANK_STATEMENT" ? (
                    <FileSpreadsheet className="mr-1 h-3 w-3 text-primary-600 flex-shrink-0" />
                  ) : (
                    <FileText className="mr-1 h-3 w-3 text-typography-muted flex-shrink-0" />
                  )}
                  <span className="truncate">{d.document_id.slice(0, 8)}...</span>
                </span>
              ))}
            </div>
          </Card>
        </div>
      </div>

      {/* 3. Ask AI Prompt Bar */}
      <Card className="border-border bg-gradient-to-r from-primary-50/50 to-surface shadow-card p-5">
        <form onSubmit={handleAskAiSubmit} className="flex flex-col sm:flex-row items-center gap-3">
          <div className="relative flex-1 w-full">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-typography-muted" />
            <input
              type="text"
              value={askAiQuery}
              onChange={(e) => setAskAiQuery(e.target.value)}
              placeholder="What would you like to know about your financial documents? (e.g. Total credit amount?)"
              className="h-9 w-full rounded border border-border bg-surface pl-9 pr-3 text-xs text-typography-primary placeholder:text-typography-muted focus:outline-none focus:ring-2 focus:ring-primary-500 shadow-subtle"
            />
          </div>
          <Button type="submit" variant="primary" size="sm" className="w-full sm:w-auto">
            <span>Ask AI</span>
            <ArrowRight className="ml-1.5 h-3.5 w-3.5" />
          </Button>
        </form>
      </Card>
    </div>
  );
}