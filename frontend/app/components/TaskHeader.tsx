"use client";

import React from "react";
import type { WorkbenchTask } from "@/app/types";
import Badge from "./Badge";
import SovereignBadge from "./SovereignBadge";

interface TaskHeaderProps {
  task: WorkbenchTask;
  className?: string;
}

export default function TaskHeader({ task, className = "" }: TaskHeaderProps) {
  const getBadgeVariant = (status: string) => {
    switch (status) {
      case "complete":
        return "complete";
      case "awaiting_review":
        return "awaiting_review";
      case "running":
      case "planning":
        return "running";
      case "failed":
        return "failed";
      default:
        return "queued";
    }
  };

  return (
    <div className={`bg-surface border border-border rounded-2xl p-5 shadow-xs space-y-3 ${className}`}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <Badge variant={getBadgeVariant(task.status)} label={task.status.replace(/_/g, " ").toUpperCase()} />
          <span className="font-mono text-xs text-text-3">ID: {task.id}</span>
          {task.deliverable_type && (
            <span className="font-mono text-xs px-2 py-0.5 rounded bg-surface-2 border border-border text-text-2 uppercase">
              Target: {task.deliverable_type}
            </span>
          )}
        </div>
        <SovereignBadge size="sm" />
      </div>

      <h2 className="font-serif font-bold text-lg text-text tracking-tight leading-snug">
        {task.query}
      </h2>

      {task.attachments && task.attachments.length > 0 && (
        <div className="flex flex-wrap items-center gap-2 pt-1 border-t border-border-subtle">
          <span className="text-[11px] font-mono text-text-3 uppercase">Attachments:</span>
          {task.attachments.map((att, i) => (
            <span
              key={i}
              className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md bg-surface-2 border border-border text-xs font-mono text-text-2"
            >
              <span>{att.type === "image" ? "🖼️" : "📄"}</span>
              <span className="truncate max-w-[140px]">{att.filename}</span>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
