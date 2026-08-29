import React from "react";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";

export default function UploadPage() {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Upload & Processing</CardTitle>
          <CardDescription>
            Drag-and-drop ingestion pipeline and stage progress monitoring. (Phase F7 Implementation)
          </CardDescription>
        </CardHeader>
      </Card>
    </div>
  );
}