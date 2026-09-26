"use client";

import React from "react";
import type { RoutingDecisionLog } from "@/app/types";
import { getModelDisplayName } from "@/app/utils/modelNames";

interface LiveRoutingLogProps {
  logs: RoutingDecisionLog[];
  className?: string;
}

export default function LiveRoutingLog({ logs, className = "" }: LiveRoutingLogProps) {
  return (
    <div className={`bg-surface border border-border rounded-2xl p-5 shadow-xs space-y-3 ${className}`}>
      <div className="flex items-center justify-between pb-2 border-b border-border-subtle">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-green animate-pulse" />
          <h3 className="font-serif font-bold text-base text-text">Recorded Model Selections</h3>
        </div>
        <span className="text-xs font-mono text-text-3">Task events</span>
      </div>

      <div className="space-y-2.5 max-h-72 overflow-y-auto pr-1">
        {logs.map((log) => (
          <div
            key={log.id}
            className="p-3 rounded-xl border border-border bg-bg-base/40 text-xs font-mono space-y-1.5 hover:bg-surface transition-colors"
          >
            <div className="flex items-center justify-between text-text-3 text-[10px]">
              <span>{new Date(log.timestamp).toLocaleTimeString()}</span>
              <span className="px-1.5 py-0.5 rounded bg-green/10 text-green font-semibold">
                {log.confidence > 0 ? `Estimated score: ${(log.confidence * 100).toFixed(0)}%` : "Score not measured"}
              </span>
            </div>

            <p className="font-sans font-medium text-text text-xs line-clamp-1">
              &quot;{log.query_snippet}&quot;
            </p>

            <div className="flex flex-wrap items-center gap-2 pt-1 border-t border-border-subtle">
              <span className="text-accent font-bold">{getModelDisplayName(log.selected_model)}</span>
              <span className="text-text-3">·</span>
              <span className="text-text-2 font-sans text-[11px] truncate max-w-sm">
                {log.reason}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
