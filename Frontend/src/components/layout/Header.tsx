"use client";

import React from "react";
import Link from "next/link";
import { useWorkspace } from "@/context/WorkspaceContext";
import { Menu, Layers, UserCircle2 } from "lucide-react";

interface HeaderProps {
  onToggleSidebar: () => void;
  isSidebarOpen?: boolean;
}

export function Header({
  onToggleSidebar,
  isSidebarOpen = false,
}: HeaderProps) {
  const { workspaceId } = useWorkspace();

  return (
    <header className="sticky top-0 z-30 flex h-16 w-full items-center justify-between border-b border-border bg-surface/95 px-4 backdrop-blur transition-all sm:px-6">
      <div className="flex items-center space-x-3">
        {/* Mobile Sidebar Hamburger Toggle */}
        <button
          type="button"
          onClick={onToggleSidebar}
          aria-label="Toggle navigation sidebar"
          aria-expanded={isSidebarOpen}
          className="rounded p-2 text-typography-secondary hover:bg-slate-100 hover:text-typography-primary focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:outline-none md:hidden"
        >
          <Menu className="h-5 w-5" />
        </button>

        {/* Global Product Brand */}
        <Link href="/" className="flex items-center space-x-2.5">
          <span className="flex h-8 w-8 items-center justify-center rounded bg-primary-600 text-xs font-bold text-white shadow-subtle">
            FD
          </span>

          <span className="text-base font-bold tracking-tight text-typography-primary">
            FinDoc <span className="text-primary-600">AI</span>
          </span>
        </Link>
      </div>

      <div className="flex items-center space-x-3">
        {/* Active Workspace Scope Pill */}
        <Link
          href="/workspace"
          className="flex items-center space-x-2 rounded-full border border-border bg-slate-50 px-3 py-1.5 text-xs text-typography-secondary hover:border-slate-300 hover:text-typography-primary transition-colors focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:outline-none"
          title="Change active workspace"
        >
          <Layers className="h-4 w-4 text-primary-600" />
          <span className="font-medium text-xs">Workspace:</span>

          <span className="font-mono text-xs font-semibold text-typography-primary">
            {workspaceId}
          </span>
        </Link>

        {/* Local Session Indicator */}
        <div
          className="hidden items-center space-x-2 rounded-full bg-slate-50 px-3 py-1.5 text-xs text-typography-muted border border-border sm:flex"
          title="Browser-local session scope"
        >
          <UserCircle2 className="h-4 w-4 text-slate-500" />

          <span className="text-xs font-medium text-typography-secondary">
            Local Session
          </span>
        </div>
      </div>
    </header>
  );
}