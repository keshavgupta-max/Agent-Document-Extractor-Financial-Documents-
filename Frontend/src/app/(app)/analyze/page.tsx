import React from "react";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";

export default function AnalyzePage() {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Analyze / Ask AI</CardTitle>
          <CardDescription>
            Grounded AI analysis, citation drawers, and question answering. (Phase F8 Implementation)
          </CardDescription>
        </CardHeader>
      </Card>
    </div>
  );
}