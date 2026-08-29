import React from "react";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";

export default function HistoryPage() {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Analysis History</CardTitle>
          <CardDescription>
            Workspace query records and historical answer previews. (Phase F9 Implementation)
          </CardDescription>
        </CardHeader>
      </Card>
    </div>
  );
}