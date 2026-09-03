import React, { useMemo } from "react";
import Link from "next/link";
import { formatCurrency } from "@/lib/utils";
import { TransactionItem } from "@/types/api";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import {
  TrendingUp,
  TrendingDown,
  FileSpreadsheet,
  UploadCloud,
  AlertCircle,
  Activity,
  ArrowUpRight,
  ArrowDownRight,
  Receipt,
  Scale,
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

interface CashFlowRatioGaugeProps {
  credits: number | null;
  debits: number | null;
  netCashFlow: number | null;
  currency?: string;
}

export function CashFlowRatioGauge({
  credits,
  debits,
  netCashFlow,
  currency = "INR",
}: CashFlowRatioGaugeProps) {
  if (credits === null && debits === null) {
    return (
      <div className="rounded border border-dashed border-border p-6 text-center text-xs text-typography-muted">
        Credit and debit volume data not available for the selected documents.
      </div>
    );
  }

  const creditVal = credits || 0;
  const debitVal = debits || 0;
  const totalVolume = creditVal + debitVal;
  const creditPct = totalVolume > 0 ? (creditVal / totalVolume) * 100 : 50;
  const debitPct = totalVolume > 0 ? (debitVal / totalVolume) * 100 : 50;

  return (
    <div className="space-y-4">
      {/* Visual Proportional Bar */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between text-xs font-medium">
          <span className="flex items-center text-status-success">
            <ArrowUpRight className="h-3.5 w-3.5 mr-1" />
            Inflows ({creditPct.toFixed(1)}%)
          </span>
          <span className="flex items-center text-slate-700">
            Outflows ({debitPct.toFixed(1)}%)
            <ArrowDownRight className="h-3.5 w-3.5 ml-1" />
          </span>
        </div>
        <div
          className="flex h-3.5 w-full overflow-hidden rounded-full bg-slate-100 p-0.5 border border-border"
          role="progressbar"
          aria-label="Cash Flow Volume Gauge"
          aria-valuenow={creditPct}
          aria-valuemin={0}
          aria-valuemax={100}
        >
          <div
            style={{ width: `${creditPct}%` }}
            className="h-full bg-status-success rounded-l-full transition-all duration-300"
            title={`Credits: ${formatCurrency(creditVal, currency)} (${creditPct.toFixed(1)}%)`}
          />
          <div
            style={{ width: `${debitPct}%` }}
            className="h-full bg-slate-600 rounded-r-full transition-all duration-300"
            title={`Debits: ${formatCurrency(debitVal, currency)} (${debitPct.toFixed(1)}%)`}
          />
        </div>
      </div>

      {/* Grid Comparison */}
      <div className="grid grid-cols-2 gap-3 pt-1">
        <div className="rounded border border-border bg-slate-50/60 p-2.5 space-y-0.5">
          <span className="text-[11px] text-typography-muted uppercase tracking-wider font-semibold">Total Inflows</span>
          <p className="text-sm font-bold font-mono text-status-success">
            {formatCurrency(creditVal, currency)}
          </p>
        </div>
        <div className="rounded border border-border bg-slate-50/60 p-2.5 space-y-0.5">
          <span className="text-[11px] text-typography-muted uppercase tracking-wider font-semibold">Total Outflows</span>
          <p className="text-sm font-bold font-mono text-typography-primary">
            {formatCurrency(debitVal, currency)}
          </p>
        </div>
      </div>

      {/* Net Indicator */}
      <div className="flex items-center justify-between border-t border-border pt-3 text-xs">
        <span className="text-typography-secondary flex items-center">
          <Scale className="h-3.5 w-3.5 mr-1.5 text-typography-muted" />
          Net Liquidity Position:
        </span>
        <Badge variant={netCashFlow !== null && netCashFlow >= 0 ? "success" : "outline"} className="font-mono text-xs">
          {netCashFlow !== null ? formatCurrency(netCashFlow, currency) : "—"}
        </Badge>
      </div>
    </div>
  );
}

interface ChronologicalActivityChartProps {
  transactions: TransactionItem[];
  currency?: string;
}

export function ChronologicalActivityChart({
  transactions,
  currency = "INR",
}: ChronologicalActivityChartProps) {
  const dailyBuckets = useMemo(() => {
    if (!transactions || transactions.length === 0) return [];

    const map: Record<string, { date: string; credits: number; debits: number }> = {};
    transactions.forEach((t) => {
      const dateKey = t.date || "Unknown";
      if (!map[dateKey]) {
        map[dateKey] = { date: dateKey, credits: 0, debits: 0 };
      }
      if (t.credit_amount) map[dateKey].credits += t.credit_amount;
      else if (t.debit_amount) map[dateKey].debits += t.debit_amount;
      else if (t.transaction_type === "CR" || t.transaction_type === "CREDIT") {
        map[dateKey].credits += t.amount || 0;
      } else {
        map[dateKey].debits += t.amount || 0;
      }
    });

    return Object.values(map).slice(-12);
  }, [transactions]);

  if (dailyBuckets.length === 0) {
    return (
      <div className="rounded border border-dashed border-border p-6 text-center text-xs text-typography-muted">
        No chronological transaction timeline data available for the active statement.
      </div>
    );
  }

  const maxVal = Math.max(...dailyBuckets.map((b) => Math.max(b.credits, b.debits)), 1);
  const chartHeight = 110;
  const barWidth = 14;
  const gap = 18;
  const svgWidth = Math.max(dailyBuckets.length * (barWidth * 2 + gap), 320);

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between text-xs text-typography-muted">
        <span className="flex items-center">
          <Activity className="h-3.5 w-3.5 mr-1.5 text-primary-600" />
          Chronological Inflows vs Outflows (Recent Dates)
        </span>
        <div className="flex items-center space-x-3 text-[11px]">
          <span className="flex items-center">
            <span className="h-2 w-2 rounded-full bg-status-success mr-1" /> Credits
          </span>
          <span className="flex items-center">
            <span className="h-2 w-2 rounded-full bg-slate-600 mr-1" /> Debits
          </span>
        </div>
      </div>

      <div className="overflow-x-auto rounded border border-border bg-slate-50/40 p-3">
        <svg
          width={svgWidth}
          height={chartHeight + 25}
          className="w-full"
          viewBox={`0 0 ${svgWidth} ${chartHeight + 25}`}
        >
          {/* Baseline */}
          <line
            x1="0"
            y1={chartHeight}
            x2={svgWidth}
            y2={chartHeight}
            stroke="#e2e8f0"
            strokeWidth="1.5"
          />

          {dailyBuckets.map((b, idx) => {
            const groupX = idx * (barWidth * 2 + gap) + 12;
            const creditHeight = (b.credits / maxVal) * (chartHeight - 15);
            const debitHeight = (b.debits / maxVal) * (chartHeight - 15);

            return (
              <g key={b.date || idx}>
                {/* Credit Bar */}
                {b.credits > 0 && (
                  <rect
                    x={groupX}
                    y={chartHeight - creditHeight}
                    width={barWidth}
                    height={Math.max(creditHeight, 2)}
                    fill="#16a34a"
                    rx="2"
                  >
                    <title>{`${b.date} Credits: ${formatCurrency(b.credits, currency)}`}</title>
                  </rect>
                )}

                {/* Debit Bar */}
                {b.debits > 0 && (
                  <rect
                    x={groupX + barWidth + 2}
                    y={chartHeight - debitHeight}
                    width={barWidth}
                    height={Math.max(debitHeight, 2)}
                    fill="#475569"
                    rx="2"
                  >
                    <title>{`${b.date} Debits: ${formatCurrency(b.debits, currency)}`}</title>
                  </rect>
                )}

                {/* Date Label */}
                <text
                  x={groupX + barWidth}
                  y={chartHeight + 16}
                  textAnchor="middle"
                  fontSize="9.5"
                  fill="#64748b"
                  fontFamily="monospace"
                >
                  {b.date.length > 5 ? b.date.slice(5) : b.date}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
}

interface BalanceTrajectoryCardProps {
  openingBalance: number | null;
  closingBalance: number | null;
  currency?: string;
}

export function BalanceTrajectoryCard({
  openingBalance,
  closingBalance,
  currency = "INR",
}: BalanceTrajectoryCardProps) {
  const delta =
    openingBalance !== null && closingBalance !== null ? closingBalance - openingBalance : null;

  return (
    <Card className="border-border bg-surface shadow-card">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-semibold text-typography-primary">
          Statement Balances & Trajectory
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3 font-mono text-xs">
        <div className="flex justify-between items-center border-b border-border pb-2">
          <span className="text-typography-muted font-sans">Opening Balance:</span>
          <span className="font-semibold text-typography-primary">
            {openingBalance !== null ? formatCurrency(openingBalance, currency) : "Not available"}
          </span>
        </div>
        <div className="flex justify-between items-center border-b border-border pb-2">
          <span className="text-typography-muted font-sans">Closing Balance:</span>
          <span className="font-semibold text-typography-primary">
            {closingBalance !== null ? formatCurrency(closingBalance, currency) : "Not available"}
          </span>
        </div>
        <div className="flex justify-between items-center pt-1 font-sans">
          <span className="text-typography-muted">Net Movement ($\Delta$):</span>
          {delta !== null ? (
            <Badge variant={delta >= 0 ? "success" : "outline"} className="font-mono text-xs">
              {delta >= 0 ? "+" : ""}
              {formatCurrency(delta, currency)}
            </Badge>
          ) : (
            <span className="text-typography-muted">—</span>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

interface InvoiceBreakdownCardProps {
  subtotal: number | null;
  tax: number | null;
  grandTotal: number | null;
  invoiceCount: number;
  currency?: string;
}

export function InvoiceBreakdownCard({
  subtotal,
  tax,
  grandTotal,
  invoiceCount,
  currency = "INR",
}: InvoiceBreakdownCardProps) {
  if (invoiceCount === 0 && grandTotal === null) return null;

  const total = grandTotal || 0;
  const subtotalPct = total > 0 && subtotal !== null ? (subtotal / total) * 100 : 0;
  const taxPct = total > 0 && tax !== null ? (tax / total) * 100 : 0;

  return (
    <Card className="border-border bg-surface shadow-card">
      <CardHeader className="pb-3 flex flex-row items-center justify-between">
        <div className="flex items-center space-x-2">
          <Receipt className="h-4 w-4 text-primary-600" />
          <CardTitle className="text-sm font-semibold text-typography-primary">
            Invoice Summary
          </CardTitle>
        </div>
        <Badge variant="outline" className="text-[10px]">
          {invoiceCount} Invoice{invoiceCount !== 1 ? "s" : ""}
        </Badge>
      </CardHeader>
      <CardContent className="space-y-3 text-xs">
        {/* Proportional Stack */}
        {total > 0 && (
          <div className="space-y-1">
            <div className="flex h-2.5 w-full overflow-hidden rounded-full bg-slate-100">
              <div
                style={{ width: `${subtotalPct}%` }}
                className="bg-primary-600 transition-all duration-300"
                title={`Subtotal: ${subtotalPct.toFixed(1)}%`}
              />
              <div
                style={{ width: `${taxPct}%` }}
                className="bg-amber-500 transition-all duration-300"
                title={`Tax: ${taxPct.toFixed(1)}%`}
              />
            </div>
            <div className="flex justify-between text-[10px] text-typography-muted font-mono pt-0.5">
              <span>Subtotal: {subtotalPct.toFixed(0)}%</span>
              <span>Tax: {taxPct.toFixed(0)}%</span>
            </div>
          </div>
        )}

        <div className="space-y-2 pt-1 border-t border-border font-mono">
          <div className="flex justify-between items-center">
            <span className="text-typography-muted font-sans">Combined Subtotal:</span>
            <span className="font-medium text-typography-primary">
              {subtotal !== null ? formatCurrency(subtotal, currency) : "—"}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-typography-muted font-sans">Combined Tax:</span>
            <span className="font-medium text-typography-primary">
              {tax !== null ? formatCurrency(tax, currency) : "—"}
            </span>
          </div>
          <div className="border-t border-border pt-1.5 flex justify-between items-center font-bold">
            <span className="text-typography-primary font-sans">Grand Total:</span>
            <span className="text-primary-700">
              {grandTotal !== null ? formatCurrency(grandTotal, currency) : "—"}
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
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
      <div className="rounded border border-dashed border-border p-6 text-center text-sm text-typography-muted">
        No transaction items found in the selected statement.
      </div>
    );
  }

  return (
    <div className="rounded border border-border bg-surface overflow-hidden">
      <div className="max-h-[380px] overflow-y-auto overflow-x-auto">
        <table className="w-full text-left text-sm" aria-label="Statement Transactions">
          <thead className="sticky top-0 z-10 border-b border-border bg-slate-50 font-semibold text-xs text-typography-muted uppercase tracking-wider shadow-xs">
            <tr>
              <th scope="col" className="px-4 py-3 bg-slate-50">Date</th>
              <th scope="col" className="px-4 py-3 bg-slate-50">Description</th>
              <th scope="col" className="px-4 py-3 bg-slate-50">Type</th>
              <th scope="col" className="px-4 py-3 bg-slate-50 text-right">Amount</th>
              <th scope="col" className="px-4 py-3 bg-slate-50 text-right">Balance</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border font-mono">
            {transactions.map((t, idx) => (
              <tr key={`${t.item_number}-${idx}`} className="hover:bg-slate-50/60 transition-colors">
                <td className="px-4 py-3 text-typography-secondary whitespace-nowrap">{t.date || "—"}</td>
                <td className="px-4 py-3 text-typography-primary font-sans max-w-[280px] lg:max-w-md truncate" title={t.description || ""}>
                  {t.description || "—"}
                </td>
                <td className="px-4 py-3 font-sans">
                  {t.transaction_type === "CR" || t.transaction_type === "CREDIT" ? (
                    <Badge variant="success" className="text-xs px-2 py-0.5">CR</Badge>
                  ) : t.transaction_type === "DB" || t.transaction_type === "DEBIT" ? (
                    <Badge variant="outline" className="text-xs px-2 py-0.5 text-slate-700 bg-slate-100">DB</Badge>
                  ) : (
                    <span className="text-typography-muted">—</span>
                  )}
                </td>
                <td className={`px-4 py-3 text-right font-medium whitespace-nowrap ${t.credit_amount ? "text-status-success" : "text-typography-primary"}`}>
                  {t.amount !== null ? formatCurrency(t.amount, currency) : "—"}
                </td>
                <td className="px-4 py-3 text-right text-typography-secondary whitespace-nowrap">
                  {t.balance !== null ? formatCurrency(t.balance, currency) : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {totalCount > transactions.length && (
        <div className="border-t border-border bg-slate-50/60 px-4 py-2.5 text-right text-xs text-typography-muted">
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