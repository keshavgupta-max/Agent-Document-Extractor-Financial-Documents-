"use client";

import React, { useState, useMemo } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { useWorkspace } from "@/context/WorkspaceContext";
import { getWorkspaceDocuments } from "@/api/documents";
import { getFinancialSummary, getDocumentTransactions } from "@/api/analytics";
import { formatCurrency } from "@/lib/utils";
import {
  SummaryCard,
  CashFlowRatioGauge,
  ChronologicalActivityChart,
  BalanceTrajectoryCard,
  InvoiceBreakdownCard,
  StatementActivityTable,
  DashboardEmptyState,
  DashboardErrorState,
} from "@/components/dashboard/DashboardComponents";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
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

  const documents = useMemo(() => docsData?.documents ?? [], [docsData]);
  const docIds = useMemo(() => documents.map((d) => d.document_id), [documents]);

  // Identify Bank Statement and Invoice documents with normalized type check
  const statementDocs = useMemo(
    () =>
      documents.filter(
        (d) => d.document_type.replace(/\s+/g, "_").toUpperCase() === "BANK_STATEMENT"
      ),
    [documents]
  );
  const invoiceDocs = useMemo(
    () =>
      documents.filter(
        (d) => d.document_type.replace(/\s+/g, "_").toUpperCase() === "INVOICE"
      ),
    [documents]
  );

  // Active statement ID for Statement Activity viewing
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
    queryFn: () => getDocumentTransactions(workspaceId, activeStatementId!, 50, 0),
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
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-typography-primary">
            Financial Overview
          </h1>
          <p className="text-sm text-typography-secondary mt-0.5">
            Workspace metrics derived from {documents.length} ingested document{documents.length !== 1 ? "s" : ""}.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <Link href="/upload">
            <Button variant="outline" size="md">
              <UploadCloud className="mr-2 h-4 w-4 text-typography-muted" />
              <span>Upload</span>
            </Button>
          </Link>
          <Link href="/analyze">
            <Button variant="primary" size="md">
              <Sparkles className="mr-2 h-4 w-4" />
              <span>Analyze Docs</span>
            </Button>
          </Link>
        </div>
      </div>

      {summaryError && <DashboardErrorState onRetry={() => refetchSummary()} />}

      {/* 1. Summary KPI Cards */}
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

      {/* 2. Main Financial Visualizations Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column (2/3): Volume Gauge, Chronological Activity, & Statement Table */}
        <div className="lg:col-span-2 space-y-6">
          {/* Cash Flow Ratio Gauge */}
          <Card className="border-border bg-surface shadow-card">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-semibold text-typography-primary">
                Cash Flow Volume & Liquidity Distribution
              </CardTitle>
              <CardDescription className="text-xs text-typography-muted">
                Workspace aggregate inflow vs outflow ratio across all statement data.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {summaryLoading ? (
                <Skeleton className="h-24 w-full rounded" />
              ) : (
                <CashFlowRatioGauge
                  credits={summaryData?.total_credit_amount ?? null}
                  debits={summaryData?.total_debit_amount ?? null}
                  netCashFlow={summaryData?.net_cash_flow ?? null}
                  currency={currency}
                />
              )}
            </CardContent>
          </Card>

          {/* Chronological Cash Flow Timeline Chart */}
          <Card className="border-border bg-surface shadow-card">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-semibold text-typography-primary">
                Cash Flow Timeline Movement
              </CardTitle>
              <CardDescription className="text-xs text-typography-muted">
                Discrete daily inflow and outflow volumes for the active statement.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {txnLoading ? (
                <Skeleton className="h-32 w-full rounded" />
              ) : (
                <ChronologicalActivityChart
                  transactions={txnData?.transactions || []}
                  currency={currency}
                />
              )}
            </CardContent>
          </Card>

          {/* Statement Activity Section */}
          <Card className="border-border bg-surface shadow-card">
            <CardHeader className="pb-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div>
                <CardTitle className="text-sm font-semibold text-typography-primary">
                  Statement Activity
                </CardTitle>
                <CardDescription className="text-xs text-typography-muted">
                  Normalized transactions extracted from statement records.
                </CardDescription>
              </div>

              {/* Statement Selector using original_filename */}
              {statementDocs.length > 1 && (
                <div className="flex items-center space-x-2">
                  <label htmlFor="statement-select" className="text-sm text-typography-muted font-medium">
                    Statement:
                  </label>
                  <select
                    id="statement-select"
                    value={activeStatementId || ""}
                    onChange={(e) => setSelectedStatementId(e.target.value)}
                    className="h-10 rounded border border-border bg-surface px-3 text-sm text-typography-primary focus:outline-none focus:ring-2 focus:ring-primary-500 font-sans max-w-[240px] truncate shadow-subtle"
                  >
                    {statementDocs.map((doc, idx) => (
                      <option key={doc.document_id} value={doc.document_id}>
                        {doc.original_filename || `Statement #${idx + 1}`}
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

        {/* Right Column (1/3): Balances, Invoice Overview, & Document Scope */}
        <div className="space-y-6">
          {/* Balances & Trajectory Card */}
          <BalanceTrajectoryCard
            openingBalance={summaryData?.opening_balance ?? null}
            closingBalance={summaryData?.closing_balance ?? null}
            currency={currency}
          />

          {/* Invoice Financial Breakdown Card */}
          <InvoiceBreakdownCard
            subtotal={summaryData?.invoice_subtotal ?? null}
            tax={summaryData?.invoice_tax ?? null}
            grandTotal={summaryData?.invoice_grand_total ?? null}
            invoiceCount={invoiceDocs.length}
            currency={currency}
          />

          {/* Document Scope Tag Cloud */}
          <Card className="border-border bg-surface shadow-card p-4 space-y-2">
            <span className="text-xs font-semibold text-typography-muted uppercase tracking-wider">
              Document Scope
            </span>
            <div className="flex flex-wrap gap-1.5 pt-1">
              {documents.map((d) => (
                <span
                  key={d.document_id}
                  className="inline-flex items-center rounded border border-border bg-slate-50 px-2 py-1 text-[11px] font-sans text-typography-secondary truncate max-w-[220px]"
                  title={`ID: ${d.document_id} (${d.document_type})`}
                >
                  {d.document_type.replace(/\s+/g, "_").toUpperCase() === "BANK_STATEMENT" ? (
                    <FileSpreadsheet className="mr-1.5 h-3.5 w-3.5 text-primary-600 flex-shrink-0" />
                  ) : (
                    <FileText className="mr-1.5 h-3.5 w-3.5 text-typography-muted flex-shrink-0" />
                  )}
                  <span className="truncate">{d.original_filename || d.document_id.slice(0, 8)}</span>
                </span>
              ))}
            </div>
          </Card>
        </div>
      </div>

      {/* 3. Ask AI Prompt Bar */}
      <Card className="border-border bg-gradient-to-r from-primary-50/50 to-surface shadow-card p-5 sm:p-6">
        <form onSubmit={handleAskAiSubmit} className="flex flex-col sm:flex-row items-center gap-3">
          <div className="relative flex-1 w-full">
            <Search className="absolute left-3.5 top-3 h-4 w-4 text-typography-muted" />
            <input
              type="text"
              value={askAiQuery}
              onChange={(e) => setAskAiQuery(e.target.value)}
              placeholder="What would you like to know about your financial documents? (e.g. Total credit amount?)"
              className="h-10 w-full rounded border border-border bg-surface pl-10 pr-3.5 text-sm text-typography-primary placeholder:text-typography-muted focus:outline-none focus:ring-2 focus:ring-primary-500 shadow-subtle"
            />
          </div>
          <Button type="submit" variant="primary" size="md" className="w-full sm:w-auto">
            <span>Ask AI</span>
            <ArrowRight className="ml-1.5 h-4 w-4" />
          </Button>
        </form>
      </Card>
    </div>
  );
}