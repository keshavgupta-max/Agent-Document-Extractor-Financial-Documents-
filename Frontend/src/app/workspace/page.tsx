"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useWorkspace } from "@/context/WorkspaceContext";
import { DEFAULT_WORKSPACE_ID } from "@/lib/constants";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/Card";
import { Layers, ArrowRight, ShieldCheck } from "lucide-react";

export default function WorkspaceEntryPage() {
  const router = useRouter();
  const { workspaceId, setWorkspaceId, isInitialized } = useWorkspace();

  const [workspaceNameInput, setWorkspaceNameInput] = useState<string>("My Finance");
  const [workspaceIdInput, setWorkspaceIdInput] = useState<string>(DEFAULT_WORKSPACE_ID);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Synchronize initial input values once WorkspaceContext hydrates from localStorage
  useEffect(() => {
    if (isInitialized) {
      setWorkspaceIdInput(workspaceId || DEFAULT_WORKSPACE_ID);
    }
  }, [isInitialized, workspaceId]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    const cleanId = workspaceIdInput.trim();
    const cleanName = workspaceNameInput.trim();

    if (!cleanId) {
      setErrorMessage("Workspace ID is required to scope documents.");
      return;
    }

    if (!cleanName) {
      setErrorMessage("Workspace Name is required.");
      return;
    }

    // Persist workspace ID via the existing context
    setWorkspaceId(cleanId);

    // Navigate directly to Dashboard
    router.push("/dashboard");
  };

  return (
    <div className="flex min-h-screen w-full flex-col items-center justify-center bg-background px-4 py-12 sm:px-6 lg:px-8">
      {/* Brand Header Link */}
      <div className="mb-6 flex items-center space-x-2">
        <Link href="/" className="flex items-center space-x-2 text-typography-primary hover:opacity-90 transition-opacity">
          <div className="flex h-8 w-8 items-center justify-center rounded bg-primary-600 text-white shadow-subtle">
            <Layers className="h-5 w-5" />
          </div>
          <span className="text-lg font-bold tracking-tight">FinDoc AI</span>
        </Link>
      </div>

      {/* Main Workspace Setup Card */}
      <Card className="w-full max-w-md shadow-elevated border-border bg-surface">
        <CardHeader className="space-y-1 pb-4">
          <CardTitle className="text-xl font-bold tracking-tight text-typography-primary">
            Welcome to your workspace
          </CardTitle>
          <CardDescription className="text-sm text-typography-secondary">
            Set your workspace name and ID to isolate your uploaded financial documents and analysis.
          </CardDescription>
        </CardHeader>

        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Workspace Local Name */}
            <div>
              <label htmlFor="workspace-name" className="block text-xs font-semibold text-typography-secondary mb-1">
                Workspace Name
              </label>
              <Input
                id="workspace-name"
                value={workspaceNameInput}
                onChange={(e) => {
                  setWorkspaceNameInput(e.target.value);
                  if (errorMessage) setErrorMessage(null);
                }}
                placeholder="e.g. My Finance"
                autoComplete="off"
              />
            </div>

            {/* Workspace ID Scope */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <label htmlFor="workspace-id" className="block text-xs font-semibold text-typography-secondary">
                  Workspace ID
                </label>
                <span className="text-[11px] text-typography-muted">Scope identifier</span>
              </div>
              <Input
                id="workspace-id"
                value={workspaceIdInput}
                onChange={(e) => {
                  setWorkspaceIdInput(e.target.value);
                  if (errorMessage) setErrorMessage(null);
                }}
                placeholder="e.g. ws_default"
                error={Boolean(errorMessage)}
                autoComplete="off"
              />
            </div>

            {/* Action Submit */}
            <div className="pt-2">
              <Button type="submit" variant="primary" className="w-full">
                <span>Continue to Dashboard</span>
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </form>
        </CardContent>

        {/* Security / Scope Reassurance Footer */}
        <CardFooter className="border-t border-border/80 bg-slate-50/50 p-4 rounded-b-lg">
          <div className="flex items-start space-x-2.5 text-xs text-typography-muted">
            <ShieldCheck className="h-4 w-4 text-primary-600 flex-shrink-0 mt-0.5" />
            <span>
              Documents, queries, and financial metrics remain scoped exclusively to this Workspace ID.
            </span>
          </div>
        </CardFooter>
      </Card>
    </div>
  );
}