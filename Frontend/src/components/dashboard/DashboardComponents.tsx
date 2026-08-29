import React from "react";
import Link from "next/link";
import { formatCurrency } from "@/lib/utils";
import { TransactionItem } from "@/types/api";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import {
  TrendingUp,
  TrendingDown,
  FileSpreadsheet,
  UploadCloud,
  AlertCircle,
} from "lucide-react";

interface SummaryCardProps {
  title: string;
  value: string;
  subtitle?: string;
  icon: React.ReactNode;
  trend?: "up" | "down" | "neutral";
}

export function SummaryCard({ title, value, subtitle, icon, trend }: SummaryCardProps) {
  return (
    <Card className="p-5 border-border bg-surface shadow-card">
      <div className="flex items-center justify-between pb-2">
        <span className="text-xs font-semibold text-typography-muted uppercase tracking-wider">
          {title}
        </span>
        <div className="flex h-8 w-8 items-center justify-center rounded bg-slate-50 text-typography-secondary">
          {icon}
        </div>
      </div>
      <div className="space-y-1">
        <p className="text-2xl font-bold tracking-tight text-typography-primary">{value}</p>
        {subtitle && (
          <p className="text-xs text-typography-muted flex items-center">
            {trend === "up" && <TrendingUp className="h-3.5 w-3.5 mr-1 text-status-success" />}
            {trend === "down" && <TrendingDown className="h-3.5 w-3.5 mr-1 text-status-error" />}
            <span>{subtitle}</span>
          </p>
        )}
      </div>
    </Card>
  );
}

interface CashFlowBarProps {
  credits: number | null;
  debits: number | null;
  currency?: string;
}

export function CashFlowBar({ credits, debits, currency = "INR" }: CashFlowBarProps) {
  if (credits === null || debits === null) {
    return (
      <div className="rounded border border-dashed border-border p-6 text-center text-xs text-typography-muted">
        Credit and debit volume data not available for the selected documents.
      </div>
    );
  }

  const totalVolume = credits + debits;
  const creditPct = totalVolume > 0 ? (credits / totalVolume) * 100 : 50;
  const debitPct = totalVolume > 0 ? (debits / totalVolume) * 100 : 50;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center space-x-2">
          <span className="flex h-2.5 w-2.5 rounded-full bg-status-success" />
          <span className="font-semibold text-typography-primary">Total Credits:</span>
          <span className="font-mono text-typography-secondary">
            {formatCurrency(credits, currency)} ({creditPct.toFixed(1)}%)
          </span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="flex h-2.5 w-2.5 rounded-full bg-slate-600" />
          <span className="font-semibold text-typography-primary">Total Debits:</span>
          <span className="font-mono text-typography-secondary">
            {formatCurrency(debits, currency)} ({debitPct.toFixed(1)}%)
          </span>
        </div>
      </div>

      {/* Visual Proportional Bar */}
      <div
        className="flex h-3 w-full overflow-hidden rounded-full bg-slate-100"
        role="progressbar"
        aria-label="Credit vs Debit Volume"
        aria-valuenow={creditPct}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div
          style={{ width: `${creditPct}%` }}
          className="bg-status-success transition-all duration-300"
          title={`Credits: ${creditPct.toFixed(1)}%`}
        />
        <div
          style={{ width: `${debitPct}%` }}
          className="bg-slate-600 transition-all duration-300"
          title={`Debits: ${debitPct.toFixed(1)}%`}
        />
      </div>

      <p className="text-[11px] text-typography-muted">
        Comparison of total credited and debited amounts for the selected workspace documents.
      </p>
    </div>
  );
}

interface StatementActivityTableProps {
  transactions: TransactionItem[];
  totalCount: number;
  currency?: string;
}

export function StatementActivityTable({
  transactions,
  totalCount,
  currency = "INR",
}: StatementActivityTableProps) {
  if (!transactions || transactions.length === 0) {
    return (
      <div className="rounded border border-dashed border-border p-6 text-center text-xs text-typography-muted">
        No transaction items found in the selected statement.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded border border-border bg-surface">
      <table className="w-full text-left text-xs" aria-label="Statement Transactions">
        <thead className="border-b border-border bg-slate-50 font-semibold text-typography-muted uppercase">
          <tr>
            <th scope="col" className="px-4 py-2.5">Date</th>
            <th scope="col" className="px-4 py-2.5">Description</th>
            <th scope="col" className="px-4 py-2.5">Type</th>
            <th scope="col" className="px-4 py-2.5 text-right">Amount</th>
            <th scope="col" className="px-4 py-2.5 text-right">Balance</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border font-mono">
          {transactions.map((t, idx) => (
            <tr key={`${t.item_number}-${idx}`} className="hover:bg-slate-50/50 transition-colors">
              <td className="px-4 py-2 text-typography-secondary">{t.date || "—"}</td>
              <td className="px-4 py-2 text-typography-primary font-sans max-w-[200px] truncate" title={t.description || ""}>
                {t.description || "—"}
              </td>
              <td className="px-4 py-2 font-sans">
                {t.transaction_type === "CR" || t.transaction_type === "CREDIT" ? (
                  <Badge variant="success" className="text-[10px] px-1.5 py-0">CR</Badge>
                ) : t.transaction_type === "DB" || t.transaction_type === "DEBIT" ? (
                  <Badge variant="outline" className="text-[10px] px-1.5 py-0 text-slate-700 bg-slate-100">DB</Badge>
                ) : (
                  <span className="text-typography-muted">—</span>
                )}
              </td>
              <td className={`px-4 py-2 text-right font-medium ${t.credit_amount ? "text-status-success" : "text-typography-primary"}`}>
                {t.amount !== null ? formatCurrency(t.amount, currency) : "—"}
              </td>
              <td className="px-4 py-2 text-right text-typography-secondary">
                {t.balance !== null ? formatCurrency(t.balance, currency) : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {totalCount > transactions.length && (
        <div className="border-t border-border bg-slate-50/50 px-4 py-2 text-right text-[11px] text-typography-muted">
          Showing {transactions.length} of {totalCount} transactions
        </div>
      )}
    </div>
  );
}

export function DashboardEmptyState() {
  return (
    <div className="rounded-lg border border-dashed border-border bg-surface p-12 text-center shadow-subtle space-y-4 max-w-lg mx-auto mt-8">
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary-50 text-primary-600 mx-auto">
        <FileSpreadsheet className="h-6 w-6" />
      </div>
      <div className="space-y-1">
        <h3 className="text-base font-bold text-typography-primary">No financial documents yet</h3>
        <p className="text-xs text-typography-secondary">
          Upload your bank statements, invoices, or CSV spreadsheets to unlock automated financial summaries, transaction browsing, and grounded AI queries.
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

export function DashboardErrorState({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="rounded border border-status-error/20 bg-status-errorBg p-4 text-xs text-slate-800 flex items-center justify-between">
      <div className="flex items-center space-x-2">
        <AlertCircle className="h-4 w-4 text-status-error flex-shrink-0" />
        <span>Financial summary metrics could not be loaded. Document library remains available.</span>
      </div>
      <Button variant="outline" size="sm" onClick={onRetry} className="bg-surface text-xs h-7">
        Retry
      </Button>
    </div>
  );
}