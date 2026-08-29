import React from "react";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { HardDrive, Lock, ShieldCheck, Info } from "lucide-react";

interface ClearHistorySettingModalProps {
  isOpen: boolean;
  workspaceId: string;
  onClose: () => void;
  onConfirm: () => void;
}

export function ClearHistorySettingModal({
  isOpen,
  workspaceId,
  onClose,
  onConfirm,
}: ClearHistorySettingModalProps) {
  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Clear Workspace Analysis History">
      <div className="space-y-4 text-xs">
        <p className="text-typography-secondary leading-relaxed">
          Are you sure you want to clear all locally cached analysis records for workspace{" "}
          <strong className="font-mono text-typography-primary">{workspaceId}</strong>?
        </p>
        <p className="text-[11px] text-typography-muted">
          This only removes locally saved question-and-answer records for this workspace in this browser. Uploaded documents and backend indices remain unaffected.
        </p>

        <div className="pt-3 border-t border-border flex justify-end space-x-2">
          <Button variant="ghost" size="sm" onClick={onClose}>
            Cancel
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => {
              onConfirm();
              onClose();
            }}
            className="bg-status-error hover:bg-red-700 text-white"
          >
            Clear History
          </Button>
        </div>
      </div>
    </Modal>
  );
}

export function StorageInfoCard() {
  return (
    <Card className="border-border bg-surface shadow-card">
      <CardHeader className="pb-3">
        <div className="flex items-center space-x-2">
          <HardDrive className="h-4 w-4 text-primary-600" />
          <CardTitle className="text-sm font-semibold text-typography-primary">
            Storage & Data Boundaries
          </CardTitle>
        </div>
      </CardHeader>
      <CardContent className="space-y-3 text-xs text-typography-secondary">
        <div className="flex items-start space-x-2.5">
          <ShieldCheck className="h-4 w-4 text-primary-600 mt-0.5 flex-shrink-0" />
          <p>
            <strong className="font-semibold text-typography-primary">Workspace ID Scope:</strong> The workspace identifier serves as the isolation boundary for document ingestion, analytics, and grounded AI retrieval.
          </p>
        </div>

        <div className="flex items-start space-x-2.5">
          <Lock className="h-4 w-4 text-primary-600 mt-0.5 flex-shrink-0" />
          <p>
            <strong className="font-semibold text-typography-primary">Local Analysis History:</strong> Questions and answers are stored locally in this browser and isolated by workspace.
          </p>
        </div>

        <div className="flex items-start space-x-2.5">
          <Info className="h-4 w-4 text-typography-muted mt-0.5 flex-shrink-0" />
          <p>
            <strong className="font-semibold text-typography-primary">Device Isolation:</strong> Local history is retained solely on this device and browser session; it is not synchronized across different devices.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}