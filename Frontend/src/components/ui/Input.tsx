import React from "react";
import { cn } from "@/lib/utils";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: boolean;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, error, type = "text", ...props }, ref) => {
    return (
      <input
        type={type}
        ref={ref}
        className={cn(
          "flex h-10 w-full rounded border border-border bg-surface px-3.5 py-2 text-sm text-typography-primary shadow-subtle placeholder:text-typography-muted transition-colors focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:border-primary-500 focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-50",
          error && "border-status-error focus-visible:ring-status-error",
          className
        )}
        {...props}
      />
    );
  }
);

Input.displayName = "Input";