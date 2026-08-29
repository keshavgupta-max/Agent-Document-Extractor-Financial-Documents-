"use client";

import React, { useState, useEffect } from "react";
import { useWorkspace } from "@/context/WorkspaceContext";
import { DEFAULT_WORKSPACE_ID } from "@/lib/constants";
import { getWorkspaceHistory, clearWorkspaceHistory } from "@/lib/history";
import {
  ClearHistorySettingModal,
  StorageInfoCard,
} from "@/components/settings/SettingsComponents";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import {
  Layers,
  Trash2,
  Check,
  RotateCcw,
  AlertCircle,
} from "lucide-react";

const WORKSPACE_NAME_PREFIX = "findoc_ws_name_";

export default function SettingsPage() {
  const { workspaceId, setWorkspaceId, isInitialized } = useWorkspace();

  const [inputWorkspaceId, setInputWorkspaceId] = useState<string>("");
  const [workspaceName, setWorkspaceName] = useState<string>("");
  const [historyCount, setHistoryCount] = useState<number>(0);
  const [isSavedNotice, setIsSavedNotice] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [clearModalOpen, setClearModalOpen] = useState<boolean>(false);

  // Sync inputs on initial mount or when workspaceId changes
  useEffect(() => {
    if (isInitialized) {
      setInputWorkspaceId(workspaceId);
      setHistoryCount(getWorkspaceHistory(workspaceId).length);

      try {
        const storedName = localStorage.getItem(`${WORKSPACE_NAME_PREFIX}${workspaceId}`);
        setWorkspaceName(storedName || "");
      } catch {
        setWorkspaceName("");
      }
    }
  }, [isInitialized, workspaceId]);

  const handleSaveSettings = (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setIsSavedNotice(false);

    const cleanId = inputWorkspaceId.trim();
    if (!cleanId) {
      setErrorMessage("Workspace ID cannot be empty.");
      return;
    }

    // Save local workspace name
    try {
      if (workspaceName.trim()) {
        localStorage.setItem(`${WORKSPACE_NAME_PREFIX}${cleanId}`, workspaceName.trim());
      } else {
        localStorage.removeItem(`${WORKSPACE_NAME_PREFIX}${cleanId}`);
      }
    } catch {
      // Ignore storage errors gracefully
    }

    // Update global workspace ID (triggers context updates & resets active doc selection)
    if (cleanId !== workspaceId) {
      setWorkspaceId(cleanId);
    }

    setIsSavedNotice(true);
    setTimeout(() => setIsSavedNotice(false), 3000);
  };

  const handleResetToDefault = () => {
    setErrorMessage(null);
    setInputWorkspaceId(DEFAULT_WORKSPACE_ID);
    setWorkspaceName("");
    setWorkspaceId(DEFAULT_WORKSPACE_ID);

    try {
      localStorage.removeItem(`${WORKSPACE_NAME_PREFIX}${DEFAULT_WORKSPACE_ID}`);
    } catch {
      // Ignore storage errors gracefully
    }

    setIsSavedNotice(true);
    setTimeout(() => setIsSavedNotice(false), 3000);
  };

  const handleClearHistoryConfirm = () => {
    clearWorkspaceHistory(workspaceId);
    setHistoryCount(0);
  };

  if (!isInitialized) {
    return (
      <div className="space-y-6 max-w-3xl mx-auto">
        <div className="h-8 w-48 bg-slate-100 rounded animate-pulse" />
        <div className="h-40 w-full bg-slate-100 rounded animate-pulse" />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-3xl mx-auto pb-16">
      {/* Page Header */}
      <div className="border-b border-border pb-4">
        <h1 className="text-xl font-bold tracking-tight text-typography-primary">
          Workspace Settings
        </h1>
        <p className="text-xs text-typography-secondary">
          Configure active workspace parameters and manage local browser preferences.
        </p>
      </div>

      {/* Save Success Notice */}
      {isSavedNotice && (
        <div className="rounded border border-status-success/30 bg-status-successBg p-3 text-xs text-emerald-900 flex items-center space-x-2">
          <Check className="h-4 w-4 text-status-success flex-shrink-0" />
          <span>Workspace settings updated successfully.</span>
        </div>
      )}

      {/* Error Alert */}
      {errorMessage && (
        <div className="rounded border border-status-error/30 bg-status-errorBg p-3 text-xs text-slate-800 flex items-center space-x-2">
          <AlertCircle className="h-4 w-4 text-status-error flex-shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* 1. Workspace Configuration Form */}
      <Card className="border-border bg-surface shadow-card">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Layers className="h-4 w-4 text-primary-600" />
              <CardTitle className="text-sm font-semibold text-typography-primary">
                Active Workspace
              </CardTitle>
            </div>
            <Badge variant="outline" className="text-[10px] font-mono">
              Active Scope
            </Badge>
          </div>
          <CardDescription className="text-xs text-typography-muted">
            All document uploads, analytics, and queries are strictly bound to this identifier.
          </CardDescription>
        </CardHeader>

        <CardContent>
          <form onSubmit={handleSaveSettings} className="space-y-4">
            {/* Workspace ID Input */}
            <div className="space-y-1.5">
              <label htmlFor="workspace-id-input" className="text-xs font-semibold text-typography-primary">
                Workspace ID
              </label>
              <Input
                id="workspace-id-input"
                value={inputWorkspaceId}
                onChange={(e) => setInputWorkspaceId(e.target.value)}
                placeholder="e.g. ws_default"
                className="font-mono text-xs h-9"
              />
              <p className="text-[11px] text-typography-muted">
                Switching workspace ID will immediately change the active document library and analytics scope.
              </p>
            </div>

            {/* Local Workspace Name (Frontend-only) */}
            <div className="space-y-1.5">
              <label htmlFor="workspace-name-input" className="text-xs font-semibold text-typography-primary">
                Workspace Display Name <span className="text-typography-muted font-normal">(Optional, local only)</span>
              </label>
              <Input
                id="workspace-name-input"
                value={workspaceName}
                onChange={(e) => setWorkspaceName(e.target.value)}
                placeholder="e.g. FY 2025 Financial Audit"
                className="text-xs h-9"
              />
              <p className="text-[11px] text-typography-muted">
                A convenient custom label for this workspace stored locally in your browser.
              </p>
            </div>

            {/* Form Actions */}
            <div className="pt-2 flex flex-col sm:flex-row items-center justify-between gap-3 border-t border-border">
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={handleResetToDefault}
                className="text-xs h-8 text-typography-muted hover:text-typography-primary w-full sm:w-auto"
              >
                <RotateCcw className="mr-1.5 h-3.5 w-3.5" />
                <span>Reset to Default</span>
              </Button>

              <Button type="submit" variant="primary" size="sm" className="w-full sm:w-auto text-xs h-8">
                Save Workspace Settings
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* 2. Analysis History Management */}
      <Card className="border-border bg-surface shadow-card">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-semibold text-typography-primary">
              Local Analysis History
            </CardTitle>
            <Badge variant="default" className="text-[10px] bg-slate-100 text-slate-700 font-mono">
              {historyCount} record{historyCount !== 1 ? "s" : ""}
            </Badge>
          </div>
          <CardDescription className="text-xs text-typography-muted">
            Locally saved inquiry records and evidence citations for workspace <strong className="font-mono text-typography-primary">{workspaceId}</strong>.
          </CardDescription>
        </CardHeader>

        <CardContent className="pt-1">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 rounded border border-border bg-slate-50/60 p-3">
            <div className="text-xs text-typography-secondary">
              <p className="font-medium text-typography-primary">Clear Workspace History</p>
              <p className="text-[11px] text-typography-muted">
                Permanently remove locally cached query records for this workspace.
              </p>
            </div>

            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setClearModalOpen(true)}
              disabled={historyCount === 0}
              className="text-xs h-8 text-status-error hover:bg-red-50 hover:text-red-700 border-border"
            >
              <Trash2 className="mr-1.5 h-3.5 w-3.5" />
              <span>Clear History</span>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 3. Storage & Data Boundaries */}
      <StorageInfoCard />

      {/* 4. About Application Section */}
      <Card className="border-border bg-surface shadow-card p-5">
        <div className="flex items-center justify-between text-xs">
          <div className="space-y-0.5">
            <p className="font-bold text-typography-primary">FinDoc AI</p>
            <p className="text-typography-muted">Financial Document Intelligence Platform</p>
          </div>
          <Badge variant="outline" className="font-mono text-[10px]">
            Frontend v1.0.0
          </Badge>
        </div>
      </Card>

      {/* Clear History Confirmation Modal */}
      <ClearHistorySettingModal
        isOpen={clearModalOpen}
        workspaceId={workspaceId}
        onClose={() => setClearModalOpen(false)}
        onConfirm={handleClearHistoryConfirm}
      />
    </div>
  );
}