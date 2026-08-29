import React from "react";
import Link from "next/link";
import { Layers, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/Button";

export function LandingHeader() {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-border bg-surface/95 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Brand Logo */}
        <Link href="/" className="flex items-center space-x-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded bg-primary-600 text-white shadow-subtle">
            <Layers className="h-5 w-5" />
          </div>
          <span className="text-lg font-bold tracking-tight text-typography-primary">
            FinDoc AI
          </span>
        </Link>

        {/* Section Navigation Links */}
        <nav className="hidden md:flex items-center space-x-8 text-sm font-medium text-typography-secondary">
          <a href="#features" className="hover:text-typography-primary transition-colors">
            Features
          </a>
          <a href="#how-it-works" className="hover:text-typography-primary transition-colors">
            How It Works
          </a>
          <a href="#enrichment" className="hover:text-typography-primary transition-colors">
            Enrichment
          </a>
          <a href="#security" className="hover:text-typography-primary transition-colors">
            Security
          </a>
        </nav>

        {/* Primary CTA */}
        <div className="flex items-center space-x-3">
          <Link href="/workspace">
            <Button variant="primary" size="sm">
              <span>Open Workspace</span>
              <ArrowRight className="ml-1.5 h-3.5 w-3.5" />
            </Button>
          </Link>
        </div>
      </div>
    </header>
  );
}