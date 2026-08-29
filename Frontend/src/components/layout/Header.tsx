"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useWorkspace } from "@/context/WorkspaceContext";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Menu, HelpCircle, User } from "lucide-react";

interface HeaderProps {
  onOpenMobileMenu: () => void;
}

export function Header({ onOpenMobileMenu }: HeaderProps) {
  const pathname = usePathname();
  const { workspaceId } = useWorkspace();

  const getPageTitle = (path: string): string => {
    if (path.startsWith("/dashboard")) return "Dashboard";
    if (path.startsWith("/documents")) return "Documents Library";
    if (path.startsWith("/upload")) return "Upload & Processing";
    if (path.startsWith("/analyze")) return "Analyze / Ask AI";
    if (path.startsWith("/history")) return "Analysis History";
    if (path.startsWith("/settings")) return "Settings";
    return "Workspace";
  };

  return (
    <header className="sticky top-0 z-30 flex h-14 w-full items-center justify-between border-b border-border bg-surface px-4 lg:px-6">
      <div className="flex items-center space-x-3">
        {/* Mobile Hamburger Button */}
        <Button
          variant="ghost"
          size="sm"
          className="lg:hidden p-1.5"
          onClick={onOpenMobileMenu}
          aria-label="Open mobile navigation"
        >
          <Menu className="h-5 w-5 text-typography-secondary" />
        </Button>

        {/* Page Title Breadcrumb */}
        <h1 className="text-sm font-semibold text-typography-primary tracking-tight">
          {getPageTitle(pathname)}
        </h1>
      </div>

      {/* Header Right Actions */}
      <div className="flex items-center space-x-3">
        {/* Workspace Badge */}
        <div className="hidden sm:flex items-center space-x-1.5">
          <Badge variant="outline" className="font-mono text-xs text-typography-secondary bg-slate-50">
            {workspaceId}
          </Badge>
        </div>

        {/* Help Link */}
        <Link
          href="/settings"
          className="inline-flex items-center text-typography-muted hover:text-typography-primary transition-colors p-1"
          title="Help and system details"
        >
          <HelpCircle className="h-4 w-4" />
        </Link>

        {/* User / Workspace Profile Indicator */}
        <div className="flex items-center space-x-2 pl-2 border-l border-border">
          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-slate-100 border border-border text-typography-secondary">
            <User className="h-3.5 w-3.5" />
          </div>
          <span className="hidden md:inline-block text-xs font-medium text-typography-secondary">
            Local User
          </span>
        </div>
      </div>
    </header>
  );
}