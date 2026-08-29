"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useWorkspace } from "@/context/WorkspaceContext";
import {
  LayoutDashboard,
  FileText,
  UploadCloud,
  Sparkles,
  History,
  Settings,
  Layers,
} from "lucide-react";

interface SidebarProps {
  onNavigate?: () => void;
}

export function Sidebar({ onNavigate }: SidebarProps) {
  const pathname = usePathname();
  const { workspaceId } = useWorkspace();

  const navItems = [
    { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { label: "Documents", href: "/documents", icon: FileText },
    { label: "Upload", href: "/upload", icon: UploadCloud },
    { label: "Analyze", href: "/analyze", icon: Sparkles },
    { label: "History", href: "/history", icon: History },
    { label: "Settings", href: "/settings", icon: Settings },
  ];

  return (
    <aside className="flex h-full w-64 flex-col border-r border-border bg-surface select-none">
      {/* Brand Header */}
      <div className="flex h-14 items-center px-6 border-b border-border">
        <Link
          href="/dashboard"
          className="flex items-center space-x-2 text-typography-primary font-semibold tracking-tight"
          onClick={onNavigate}
        >
          <div className="flex h-7 w-7 items-center justify-center rounded bg-primary-600 text-white shadow-subtle">
            <Layers className="h-4 w-4" />
          </div>
          <span className="text-base font-bold">FinDoc AI</span>
        </Link>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 space-y-1 p-4" aria-label="Main Navigation">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);

          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onNavigate}
              aria-current={isActive ? "page" : undefined}
              className={cn(
                "flex items-center space-x-3 rounded px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary-50 text-primary-700 font-semibold shadow-subtle"
                  : "text-typography-secondary hover:bg-slate-50 hover:text-typography-primary"
              )}
            >
              <Icon className={cn("h-4 w-4", isActive ? "text-primary-600" : "text-typography-muted")} />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      {/* Bottom Workspace Indicator */}
      <div className="border-t border-border p-4 bg-slate-50/50">
        <div className="flex flex-col space-y-1">
          <span className="text-xs font-semibold text-typography-muted uppercase tracking-wider">
            Active Workspace
          </span>
          <div className="flex items-center justify-between rounded border border-border bg-surface px-2.5 py-1.5 shadow-subtle">
            <span className="text-xs font-mono font-medium text-typography-primary truncate max-w-[170px]">
              {workspaceId}
            </span>
            <span className="flex h-2 w-2 rounded-full bg-status-success" title="Local active workspace" />
          </div>
        </div>
      </div>
    </aside>
  );
}