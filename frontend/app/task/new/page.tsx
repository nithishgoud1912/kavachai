"use client";

import React from "react";
import AppShell from "@/app/components/AppShell";
import TaskComposer from "@/app/components/TaskComposer";

export default function NewTaskPage() {
  return (
    <AppShell
      title="Create Sovereign Task"
      subtitle="Multi-Agent Pipeline"
      breadcrumbs={[
        { label: "Workspace", href: "/workspace" },
        { label: "New Task" },
      ]}
    >
      <div className="max-w-3xl mx-auto space-y-6">
        <div>
          <h2 className="font-serif text-2xl font-bold text-text">
            Configure Sovereign Agentic Task
          </h2>
          <p className="text-xs text-text-3 font-mono mt-1">
            Specify technical parameters, attach P&IDs or inspection reports, and select deliverable format.
          </p>
        </div>

        <TaskComposer />
      </div>
    </AppShell>
  );
}
