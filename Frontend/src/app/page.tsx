import React from "react";
import Link from "next/link";
import {
  ArrowRight,
  ShieldCheck,
  FileText,
  Sparkles,
  BarChart3,
  CheckCircle2,
  Lock,
  Layers,
  FileSpreadsheet,
  Database,
  Search,
  DollarSign,
  TrendingUp,
} from "lucide-react";
import { LandingHeader } from "@/components/landing/LandingHeader";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";

export default function HomePage() {
  return (
    <div className="min-h-screen bg-background text-typography-primary scroll-smooth">
      {/* 1. Header */}
      <LandingHeader />

      <main>
        {/* 2. Hero Section */}
        <section className="relative overflow-hidden pt-12 pb-16 md:pt-20 md:pb-24">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 text-center">
            <div className="inline-flex items-center space-x-2 rounded-full border border-border bg-surface px-3 py-1 text-xs font-semibold text-primary-700 shadow-subtle mb-6">
              <span className="flex h-2 w-2 rounded-full bg-primary-600" />
              <span>FINANCIAL DOCUMENT INTELLIGENCE</span>
            </div>

            <h1 className="mx-auto max-w-4xl text-4xl font-extrabold tracking-tight text-typography-primary sm:text-5xl md:text-6xl">
              Analyze your financial documents with{" "}
              <span className="text-primary-600">grounded AI</span>.
            </h1>

            <p className="mx-auto mt-6 max-w-2xl text-base text-typography-secondary sm:text-lg">
              Upload invoices, bank statements, CSVs, and spreadsheets. Extract
              structured information, ask questions across selected documents, and
              verify answers directly against retrieved source evidence.
            </p>

            <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link href="/workspace">
                <Button variant="primary" size="lg" className="w-full sm:w-auto">
                  <span>Open Workspace</span>
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </Link>
              <a href="#how-it-works">
                <Button variant="outline" size="lg" className="w-full sm:w-auto">
                  See How It Works
                </Button>
              </a>
            </div>

            {/* Product UI Preview Mockup */}
            <div className="mx-auto mt-14 max-w-5xl">
              <div className="rounded-xl border border-border bg-surface p-2 shadow-elevated">
                <div className="rounded-lg border border-border bg-slate-50/50 p-4 sm:p-6 text-left">
                  {/* Top Mockup Header Bar */}
                  <div className="flex flex-wrap items-center justify-between border-b border-border pb-4 gap-2">
                    <div className="flex items-center space-x-2">
                      <div className="h-3 w-3 rounded-full bg-slate-300" />
                      <div className="h-3 w-3 rounded-full bg-slate-300" />
                      <div className="h-3 w-3 rounded-full bg-slate-300" />
                      <span className="ml-2 text-xs font-mono font-medium text-typography-muted">
                        FinDoc AI — Analysis View
                      </span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Badge variant="outline" className="bg-surface font-mono text-[11px]">
                        Scope: 1 Document Selected
                      </Badge>
                      <span className="rounded bg-primary-50 px-2 py-0.5 text-[11px] font-semibold text-primary-700">
                        Product Preview
                      </span>
                    </div>
                  </div>

                  {/* Mockup Workspace Grid */}
                  <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
                    {/* Left: Selected Document Frame */}
                    <div className="rounded border border-border bg-surface p-3.5 space-y-2">
                      <span className="text-xs font-semibold uppercase tracking-wider text-typography-muted">
                        Selected Scope
                      </span>
                      <div className="flex items-center space-x-2 rounded border border-primary-100 bg-primary-50/60 p-2 text-xs">
                        <FileSpreadsheet className="h-4 w-4 text-primary-600 flex-shrink-0" />
                        <div className="truncate">
                          <p className="font-semibold text-typography-primary truncate">
                            bank_statement_2022.csv
                          </p>
                          <p className="text-[10px] text-typography-muted">
                            Type: Bank Statement • 229 Chunks
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Center: Query & Grounded Answer */}
                    <div className="md:col-span-2 rounded border border-border bg-surface p-4 space-y-3">
                      <div className="flex items-start space-x-2">
                        <Search className="h-4 w-4 text-primary-600 mt-0.5 flex-shrink-0" />
                        <div>
                          <p className="text-xs font-semibold text-typography-muted">User Query</p>
                          <p className="text-sm font-medium text-typography-primary">
                            &quot;How much money was credited to the account in total?&quot;
                          </p>
                        </div>
                      </div>

                      <div className="rounded border border-border/80 bg-slate-50/70 p-3 space-y-1.5">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-semibold text-primary-700">
                            Grounded Answer
                          </span>
                          <span className="text-[10px] font-mono text-status-success flex items-center">
                            <CheckCircle2 className="h-3 w-3 mr-1 inline" /> Verified
                          </span>
                        </div>
                        <p className="text-sm text-typography-primary leading-relaxed">
                          The total amount credited to the account across the statement period is{" "}
                          <strong className="font-semibold text-typography-primary">₹55,000.00</strong>.
                        </p>
                      </div>

                      {/* Cited Evidence Source */}
                      <div className="rounded border border-dashed border-border p-2.5 bg-surface text-xs space-y-1">
                        <span className="font-semibold text-typography-muted">
                          Retrieved Source Evidence:
                        </span>
                        <p className="font-mono text-[11px] text-typography-secondary bg-slate-50 p-1.5 rounded">
                          [Chunk 0] Statement Summary: Total Credit Amount: 55000.00 | Total Transactions: 200
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* 3. Capability / Workflow Strip */}
        <section className="border-y border-border bg-surface py-6">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
              <div className="flex items-center justify-center space-x-2">
                <span className="text-sm font-bold text-primary-600 font-mono">01</span>
                <span className="text-sm font-semibold text-typography-primary">Upload Document</span>
              </div>
              <div className="flex items-center justify-center space-x-2">
                <span className="text-sm font-bold text-primary-600 font-mono">02</span>
                <span className="text-sm font-semibold text-typography-primary">Structured Process</span>
              </div>
              <div className="flex items-center justify-center space-x-2">
                <span className="text-sm font-bold text-primary-600 font-mono">03</span>
                <span className="text-sm font-semibold text-typography-primary">Grounded Analyze</span>
              </div>
              <div className="flex items-center justify-center space-x-2">
                <span className="text-sm font-bold text-primary-600 font-mono">04</span>
                <span className="text-sm font-semibold text-typography-primary">Source Verify</span>
              </div>
            </div>
          </div>
        </section>

        {/* 4. Core Features */}
        <section id="features" className="py-16 md:py-24">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="text-center max-w-3xl mx-auto mb-12">
              <h2 className="text-2xl font-bold tracking-tight text-typography-primary sm:text-3xl">
                Purpose-built for financial accuracy
              </h2>
              <p className="mt-3 text-sm text-typography-secondary sm:text-base">
                Generic language models often fail on tables, statement math, and complex multi-page invoices.
                FinDoc AI uses deterministic extraction combined with scoped retrieval.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <Card className="p-5 border-border bg-surface shadow-card">
                <div className="flex h-10 w-10 items-center justify-center rounded bg-primary-50 text-primary-600 mb-4">
                  <FileText className="h-5 w-5" />
                </div>
                <h3 className="text-base font-semibold text-typography-primary">
                  Document Intelligence
                </h3>
                <p className="mt-2 text-xs text-typography-secondary leading-relaxed">
                  Extract structured entities, line items, taxes, and statement aggregates automatically upon upload.
                </p>
              </Card>

              <Card className="p-5 border-border bg-surface shadow-card">
                <div className="flex h-10 w-10 items-center justify-center rounded bg-primary-50 text-primary-600 mb-4">
                  <Sparkles className="h-5 w-5" />
                </div>
                <h3 className="text-base font-semibold text-typography-primary">
                  Grounded AI Analysis
                </h3>
                <p className="mt-2 text-xs text-typography-secondary leading-relaxed">
                  Responses are generated strictly using retrieved document context with verifiable evidence citations.
                </p>
              </Card>

              <Card className="p-5 border-border bg-surface shadow-card">
                <div className="flex h-10 w-10 items-center justify-center rounded bg-primary-50 text-primary-600 mb-4">
                  <Layers className="h-5 w-5" />
                </div>
                <h3 className="text-base font-semibold text-typography-primary">
                  Multi-Document Scope
                </h3>
                <p className="mt-2 text-xs text-typography-secondary leading-relaxed">
                  Select 1 to 5 documents simultaneously to compare totals, cross-reference vendors, or sum invoice figures.
                </p>
              </Card>

              <Card className="p-5 border-border bg-surface shadow-card">
                <div className="flex h-10 w-10 items-center justify-center rounded bg-primary-50 text-primary-600 mb-4">
                  <ShieldCheck className="h-5 w-5" />
                </div>
                <h3 className="text-base font-semibold text-typography-primary">
                  Source Verification
                </h3>
                <p className="mt-2 text-xs text-typography-secondary leading-relaxed">
                  Inspect the underlying chunk excerpts and exact numeric passages used to answer every inquiry.
                </p>
              </Card>
            </div>
          </div>
        </section>

        {/* 5. Data Enrichment Section */}
        <section id="enrichment" className="border-t border-border bg-surface py-16 md:py-24">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="text-center max-w-3xl mx-auto mb-12">
              <span className="text-xs font-bold uppercase tracking-wider text-primary-600">
                Data Enrichment
              </span>
              <h2 className="mt-1 text-2xl font-bold tracking-tight text-typography-primary sm:text-3xl">
                From raw files to analysis-ready data
              </h2>
              <p className="mt-3 text-sm text-typography-secondary sm:text-base">
                Documents undergo an 8-stage deterministic ingestion pipeline before entering vector memory.
              </p>
            </div>

            {/* Pipeline Step Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2.5 text-center mb-12">
              {[
                "1. Upload",
                "2. Parse",
                "3. Classify",
                "4. Extract",
                "5. Validate",
                "6. Semantic Prep",
                "7. Embed",
                "8. Store",
              ].map((step, idx) => (
                <div key={idx} className="rounded border border-border bg-slate-50 p-2.5 text-xs font-semibold text-typography-primary shadow-subtle">
                  <CheckCircle2 className="h-3.5 w-3.5 text-primary-600 mx-auto mb-1" />
                  {step}
                </div>
              ))}
            </div>

            {/* Schema Models Comparison Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card className="border-border bg-background p-5">
                <div className="flex items-center space-x-2 border-b border-border pb-3 mb-3">
                  <FileText className="h-4 w-4 text-primary-600" />
                  <h3 className="text-sm font-bold text-typography-primary">
                    Structured Invoice Model
                  </h3>
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs font-mono text-typography-secondary">
                  <div className="bg-surface p-2 rounded border border-border">Invoice Number</div>
                  <div className="bg-surface p-2 rounded border border-border">Vendor / Seller</div>
                  <div className="bg-surface p-2 rounded border border-border">Tax Breakdown (GST)</div>
                  <div className="bg-surface p-2 rounded border border-border">Subtotal & Totals</div>
                  <div className="bg-surface p-2 rounded border border-border">Currency Code</div>
                  <div className="bg-surface p-2 rounded border border-border">Line Items Table</div>
                </div>
              </Card>

              <Card className="border-border bg-background p-5">
                <div className="flex items-center space-x-2 border-b border-border pb-3 mb-3">
                  <FileSpreadsheet className="h-4 w-4 text-primary-600" />
                  <h3 className="text-sm font-bold text-typography-primary">
                    Bank Statement Model
                  </h3>
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs font-mono text-typography-secondary">
                  <div className="bg-surface p-2 rounded border border-border">Total Credits</div>
                  <div className="bg-surface p-2 rounded border border-border">Total Debits</div>
                  <div className="bg-surface p-2 rounded border border-border">Opening Balance</div>
                  <div className="bg-surface p-2 rounded border border-border">Closing Balance</div>
                  <div className="bg-surface p-2 rounded border border-border">Transaction Count</div>
                  <div className="bg-surface p-2 rounded border border-border">Cr/Db Categorization</div>
                </div>
              </Card>
            </div>
          </div>
        </section>

        {/* 6. Why This Is Different (Comparison Table) */}
        <section className="py-16 md:py-24 border-t border-border">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="text-center max-w-3xl mx-auto mb-12">
              <h2 className="text-2xl font-bold tracking-tight text-typography-primary sm:text-3xl">
                How FinDoc AI compares
              </h2>
              <p className="mt-3 text-sm text-typography-secondary">
                Designed specifically for analytical rigor rather than generic conversation.
              </p>
            </div>

            <div className="overflow-x-auto rounded-lg border border-border bg-surface shadow-card">
              <table className="w-full text-left text-sm">
                <thead className="border-b border-border bg-slate-50 text-xs font-semibold text-typography-muted uppercase">
                  <tr>
                    <th className="px-6 py-4">Capability</th>
                    <th className="px-6 py-4 text-typography-secondary">Generic AI / Open Chat</th>
                    <th className="px-6 py-4 text-primary-700 bg-primary-50/50">FinDoc AI Platform</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  <tr>
                    <td className="px-6 py-4 font-semibold text-typography-primary">Scope Boundaries</td>
                    <td className="px-6 py-4 text-typography-secondary">Open-ended global chat</td>
                    <td className="px-6 py-4 font-semibold text-primary-700 bg-primary-50/30">
                      Strict document-scoped analysis
                    </td>
                  </tr>
                  <tr>
                    <td className="px-6 py-4 font-semibold text-typography-primary">Evidence & Citations</td>
                    <td className="px-6 py-4 text-typography-secondary">No document evidence layer</td>
                    <td className="px-6 py-4 font-semibold text-primary-700 bg-primary-50/30">
                      Source-backed answers with chunk inspector
                    </td>
                  </tr>
                  <tr>
                    <td className="px-6 py-4 font-semibold text-typography-primary">Multi-Document Analysis</td>
                    <td className="px-6 py-4 text-typography-secondary">Single-context interaction</td>
                    <td className="px-6 py-4 font-semibold text-primary-700 bg-primary-50/30">
                      Select up to 5 documents for cross-comparison
                    </td>
                  </tr>
                  <tr>
                    <td className="px-6 py-4 font-semibold text-typography-primary">Financial Semantics</td>
                    <td className="px-6 py-4 text-typography-secondary">Treats numbers as plain text</td>
                    <td className="px-6 py-4 font-semibold text-primary-700 bg-primary-50/30">
                      Understands credits, debits, tax rates, balances
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </section>

        {/* 7. Graphical Analysis Preview */}
        <section className="border-t border-border bg-surface py-16 md:py-24">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="flex flex-col md:flex-row md:items-end justify-between mb-12">
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-primary-600">
                  Analytics Layer
                </span>
                <h2 className="mt-1 text-2xl font-bold tracking-tight text-typography-primary sm:text-3xl">
                  Deterministic visual analysis
                </h2>
                <p className="mt-2 text-sm text-typography-secondary">
                  Visual metrics are calculated directly from structured financial data, not estimated by language models.
                </p>
              </div>
              <div className="mt-4 md:mt-0">
                <Badge variant="outline" className="text-xs font-mono bg-slate-50">
                  Sample Analysis Preview
                </Badge>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Sample Card 1: Inflow / Outflow */}
              <Card className="p-5 border-border bg-background">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-semibold text-typography-muted uppercase">
                    Cash Movement
                  </span>
                  <DollarSign className="h-4 w-4 text-primary-600" />
                </div>
                <div className="space-y-3">
                  <div>
                    <span className="text-xs text-typography-muted">Total Credits</span>
                    <p className="text-xl font-bold text-status-success">₹112,000.00</p>
                  </div>
                  <div>
                    <span className="text-xs text-typography-muted">Total Debits</span>
                    <p className="text-xl font-bold text-typography-primary">₹84,500.00</p>
                  </div>
                  <div className="pt-2 border-t border-border flex justify-between items-center text-xs">
                    <span className="text-typography-muted">Net Movement:</span>
                    <span className="font-semibold text-status-success">+₹27,500.00</span>
                  </div>
                </div>
              </Card>

              {/* Sample Card 2: Invoice Totals Comparison */}
              <Card className="p-5 border-border bg-background">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-semibold text-typography-muted uppercase">
                    Multi-Invoice Compare
                  </span>
                  <BarChart3 className="h-4 w-4 text-primary-600" />
                </div>
                <div className="space-y-2.5">
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="font-medium text-typography-primary">Invoice A (Acme Corp)</span>
                      <span className="font-semibold">₹12,500</span>
                    </div>
                    <div className="h-2 w-full rounded bg-slate-200">
                      <div className="h-2 rounded bg-primary-600 w-2/5" />
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="font-medium text-typography-primary">Invoice B (Global Tech)</span>
                      <span className="font-semibold">₹31,200</span>
                    </div>
                    <div className="h-2 w-full rounded bg-slate-200">
                      <div className="h-2 rounded bg-primary-600 w-4/5" />
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="font-medium text-typography-primary">Invoice C (Apex Logistics)</span>
                      <span className="font-semibold">₹18,900</span>
                    </div>
                    <div className="h-2 w-full rounded bg-slate-200">
                      <div className="h-2 rounded bg-primary-600 w-3/5" />
                    </div>
                  </div>
                </div>
              </Card>

              {/* Sample Card 3: Tax Structure */}
              <Card className="p-5 border-border bg-background">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-semibold text-typography-muted uppercase">
                    Tax Breakdown
                  </span>
                  <TrendingUp className="h-4 w-4 text-primary-600" />
                </div>
                <div className="space-y-3">
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-typography-secondary">CGST (9%)</span>
                    <span className="font-mono font-medium text-typography-primary">₹5,400.00</span>
                  </div>
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-typography-secondary">SGST (9%)</span>
                    <span className="font-mono font-medium text-typography-primary">₹5,400.00</span>
                  </div>
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-typography-secondary">IGST (18%)</span>
                    <span className="font-mono font-medium text-typography-primary">₹0.00</span>
                  </div>
                  <div className="pt-2 border-t border-border flex justify-between items-center text-xs font-bold">
                    <span>Total Tax Extracted:</span>
                    <span className="text-primary-700">₹10,800.00</span>
                  </div>
                </div>
              </Card>
            </div>
          </div>
        </section>

        {/* 8. How It Works */}
        <section id="how-it-works" className="py-16 md:py-24 border-t border-border">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="text-center max-w-3xl mx-auto mb-12">
              <h2 className="text-2xl font-bold tracking-tight text-typography-primary sm:text-3xl">
                How it works
              </h2>
              <p className="mt-3 text-sm text-typography-secondary">
                Three clean steps to grounded document analysis.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="rounded-lg border border-border bg-surface p-6 shadow-card space-y-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary-600 text-white font-bold text-sm">
                  1
                </div>
                <h3 className="text-base font-semibold text-typography-primary">
                  Set Workspace & Upload
                </h3>
                <p className="text-xs text-typography-secondary leading-relaxed">
                  Open a workspace and upload your financial PDF, CSV, or XLSX files. Documents are ingested through deterministic parsers.
                </p>
              </div>

              <div className="rounded-lg border border-border bg-surface p-6 shadow-card space-y-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary-600 text-white font-bold text-sm">
                  2
                </div>
                <h3 className="text-base font-semibold text-typography-primary">
                  Select Scope (1–5 Docs)
                </h3>
                <p className="text-xs text-typography-secondary leading-relaxed">
                  Pick the exact documents you want analyzed from your library. All queries operate strictly within this chosen scope.
                </p>
              </div>

              <div className="rounded-lg border border-border bg-surface p-6 shadow-card space-y-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary-600 text-white font-bold text-sm">
                  3
                </div>
                <h3 className="text-base font-semibold text-typography-primary">
                  Ask & Verify Evidence
                </h3>
                <p className="text-xs text-typography-secondary leading-relaxed">
                  Ask financial questions, receive grounded answers, and click cited source excerpts to verify numeric accuracy.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* 9. Security & Trust */}
        <section id="security" className="border-t border-border bg-surface py-16 md:py-24">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="text-center max-w-3xl mx-auto mb-12">
              <span className="text-xs font-bold uppercase tracking-wider text-primary-600">
                Security & Scope
              </span>
              <h2 className="mt-1 text-2xl font-bold tracking-tight text-typography-primary sm:text-3xl">
                Conservative data boundaries
              </h2>
              <p className="mt-3 text-sm text-typography-secondary">
                Designed with strict boundaries ensuring document isolation and verified answering.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="rounded border border-border bg-background p-5 space-y-2">
                <Lock className="h-5 w-5 text-primary-600 mb-1" />
                <h3 className="text-sm font-semibold text-typography-primary">
                  Workspace Isolation
                </h3>
                <p className="text-xs text-typography-secondary leading-relaxed">
                  Every document and query vector is isolated by workspace ID boundaries. Cross-workspace retrieval is prevented.
                </p>
              </div>

              <div className="rounded border border-border bg-background p-5 space-y-2">
                <Database className="h-5 w-5 text-primary-600 mb-1" />
                <h3 className="text-sm font-semibold text-typography-primary">
                  Explicit Document Scoping
                </h3>
                <p className="text-xs text-typography-secondary leading-relaxed">
                  Vector retrieval is restricted strictly to the user&apos;s explicit selection of 1 to 5 document UUIDs.
                </p>
              </div>

              <div className="rounded border border-border bg-background p-5 space-y-2">
                <ShieldCheck className="h-5 w-5 text-primary-600 mb-1" />
                <h3 className="text-sm font-semibold text-typography-primary">
                  Grounded Guardrails
                </h3>
                <p className="text-xs text-typography-secondary leading-relaxed">
                  When evidence is insufficient, the system explicitly reports that data is unavailable rather than fabricating answers.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* 10. Final CTA */}
        <section className="border-t border-border bg-background py-16 md:py-20 text-center">
          <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 space-y-6">
            <h2 className="text-3xl font-extrabold tracking-tight text-typography-primary sm:text-4xl">
              Ready to analyze your financial documents?
            </h2>
            <p className="mx-auto max-w-xl text-sm text-typography-secondary">
              Open a workspace now to start uploading, extracting, and querying your documents with grounded AI.
            </p>
            <div className="pt-2 flex justify-center">
              <Link href="/workspace">
                <Button variant="primary" size="lg">
                  <span>Open Workspace</span>
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </Link>
            </div>
          </div>
        </section>
      </main>

      {/* 11. Footer */}
      <footer className="border-t border-border bg-surface py-8">
        <div className="mx-auto flex max-w-7xl flex-col sm:flex-row items-center justify-between px-4 sm:px-6 lg:px-8 gap-4 text-xs text-typography-muted">
          <div className="flex items-center space-x-2">
            <div className="flex h-5 w-5 items-center justify-center rounded bg-primary-600 text-white font-bold text-[10px]">
              F
            </div>
            <span className="font-semibold text-typography-primary">FinDoc AI</span>
            <span>• Financial Document Intelligence Platform</span>
          </div>
          <div className="flex space-x-6">
            <Link href="/workspace" className="hover:text-typography-primary transition-colors">
              Workspace
            </Link>
            <Link href="/dashboard" className="hover:text-typography-primary transition-colors">
              Dashboard
            </Link>
            <a href="#features" className="hover:text-typography-primary transition-colors">
              Features
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}