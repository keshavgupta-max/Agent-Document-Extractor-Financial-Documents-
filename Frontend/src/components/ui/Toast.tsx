import React from "react";
import { cn } from "@/lib/utils";
import { CheckCircle2, AlertCircle, Info, X } from "lucide-react";

export interface ToastProps {
  type?: "success" | "error" | "info";
  message: string;
  onDismiss?: () => void;
}

export function Toast({ type = "info", message, onDismiss }: ToastProps) {
  const icons = {
    success: <CheckCircle2 className="h-4 w-4 text-status-success" />,
    error: <AlertCircle className="h-4 w-4 text-status-error" />,
    info: <Info className="h-4 w-4 text-status-info" />,
  };

  const bgStyles = {
    success: "border-status-success/20 bg-status-successBg text-slate-800",
    error: "border-status-error/20 bg-status-errorBg text-slate-800",
    info: "border-status-info/20 bg-status-infoBg text-slate-800",
  };

  return (
    <div className={cn("flex items-center justify-between rounded border p-3 text-sm shadow-subtle", bgStyles[type])}>
      <div className="flex items-center space-x-2">
        {icons[type]}
        <span>{message}</span>
      </div>
      {onDismiss && (
        <button onClick={onDismiss} className="text-slate-400 hover:text-slate-600">
          <X className="h-3.5 w-3.5" />
        </button>
      )}
    </div>
  );
}