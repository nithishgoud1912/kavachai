"use client";

import React from "react";
import type { SubTaskItem } from "@/app/types";
import ModelChip from "./ModelChip";
import Badge from "./Badge";

interface PlanTreeProps {
  plan: SubTaskItem[];
  className?: string;
}

export default function PlanTree({ plan, className = "" }: PlanTreeProps) {
  if (!plan || plan.length === 0) {
    return (
      <div className="p-4 rounded-xl border border-dashed border-border text-center text-xs text-text-3">
        Decomposing task requirements into sub-tasks...
      </div>
    );
  }

  return (
    <div className={`space-y-2.5 ${className}`}>
      <div className="flex items-center justify-between px-1">
        <h3 className="text-xs font-mono font-semibold uppercase tracking-wider text-text-3">
          Decomposed Plan & Model Routing ({plan.length} Steps)
        </h3>
      </div>

      <div className="space-y-2">
        {plan.map((step, idx) => {
          const isDone = step.status === "done";
          const isRunning = step.status === "running";
          const isFailed = step.status === "failed";

          return (
            <div
              key={step.id || idx}
              className={`p-3.5 rounded-xl border transition-all ${
                isRunning
                  ? "bg-accent/5 border-accent/40 shadow-xs"
                  : isDone
                  ? "bg-surface border-border"
                  : "bg-surface-2/40 border-border opacity-70"
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-start gap-2.5">
                  <span
                    className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-mono font-bold shrink-0 mt-0.5 ${
                      isDone
                        ? "bg-[#E9F0EC] text-[#2D794D]"
                        : isRunning
                        ? "bg-accent text-white animate-pulse"
                        : "bg-surface-2 text-text-3 border border-border"
                    }`}
                  >
                    {isDone ? "✓" : idx + 1}
                  </span>
                  <div className="space-y-1">
                    <p className="text-xs font-semibold text-text leading-tight">{step.goal}</p>
                    <div className="flex flex-wrap items-center gap-2 pt-0.5">
                      <ModelChip model={step.assigned_model} taskType={step.task_type} size="sm" />
                      {step.duration_ms && (
                        <span className="text-[10px] font-mono text-text-3">
                          {step.duration_ms}ms
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                <Badge
                  variant={isDone ? "complete" : isRunning ? "running" : isFailed ? "failed" : "queued"}
                  size="sm"
                  label={step.status.toUpperCase()}
                />
              </div>

              {step.error && (
                <div className="mt-2 text-xs text-red font-mono bg-red/10 p-2 rounded">
                  Error: {step.error}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
