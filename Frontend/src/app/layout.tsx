import React, { ReactNode } from "react";
import type { Metadata } from "next";
import "@/styles/globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "FinDoc AI — Financial Document Intelligence",
  description: "Grounded AI analysis, extraction, and verification for financial documents.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-background text-typography-primary antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}