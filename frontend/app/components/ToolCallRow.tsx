"use client";

import React, { useState } from "react";
import Link from "next/link";
import type { ToolCallEvent } from "@/app/types";
import Badge from "./Badge";

interface ToolCallRowProps {
  toolCall: ToolCallEvent;
  className?: string;
}

export default function ToolCallRow({ toolCall, className = "" }: ToolCallRowProps) {
  const [expanded, setExpanded] = useState(false);

  let icon = "🔧";
  switch (toolCall.category) {
    case "code_sandbox":
      icon = "💻";
      break;
    case "ocr":
      icon = "📄";
      break;
    case "vision":
      icon = "👁️";
      break;
    case "spreadsheet":
      icon = "📊";
      break;
    case "doc_search":
      icon = "🔍";
      break;
    case "file":
      icon = "📁";
      break;
  }

  const isCompleted = toolCall.status === "completed";
  const isRunning = toolCall.status === "running";
  const isBlocked = toolCall.status === "blocked";

  return (
    <div
      className={`border rounded-xl p-3 text-xs transition-all ${
        isBlocked
          ? "bg-red/5 border-red/30"
          : isRunning
          ? "bg-accent/5 border-accent/30 shadow-xs"
          : "bg-surface border-border hover:border-border-hi"
      } ${className}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-2.5">
          <span className="text-base shrink-0 mt-0.5">{icon}</span>
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="font-mono font-bold text-text">{toolCall.tool_name}</span>
              <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-surface-2 text-text-3 uppercase">
                {toolCall.category.replace(/_/g, " ")}
              </span>
            </div>
            {toolCall.result_summary && (
              <p className="text-text-2 font-sans text-xs">{toolCall.result_summary}</p>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {toolCall.duration_ms && (
            <span className="font-mono text-[10px] text-text-3">{toolCall.duration_ms}ms</span>
          )}
          <Badge
            variant={isCompleted ? "complete" : isRunning ? "running" : isBlocked ? "failed" : "queued"}
            label={toolCall.status.toUpperCase()}
            size="sm"
          />
        </div>
      </div>

      {/* Code Sandbox Preview Snippet if applicable */}
      {toolCall.sandbox_result && (
        <div className="mt-2.5 p-2.5 rounded-lg bg-bg-base border border-border font-mono text-[11px] space-y-1">
          <div className="flex items-center justify-between text-text-3">
            <span className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-green" />
              <span>Sandbox Exit: {toolCall.sandbox_result.exit_code}</span>
            </span>
            <Link href="/sandbox" className="text-accent hover:underline text-[10px]">
              Open Standalone Sandbox →
            </Link>
          </div>
          <pre className="text-text-primary overflow-x-auto whitespace-pre-wrap max-h-24">
            {toolCall.sandbox_result.stdout || toolCall.sandbox_result.stderr}
          </pre>
        </div>
      )}

      {/* Toggle raw args & output */}
      <div className="mt-2 pt-1 border-t border-border-subtle flex items-center justify-between text-[11px] text-text-3">
        <button
          onClick={() => setExpanded(!expanded)}
          className="hover:text-accent font-mono flex items-center gap-1 cursor-pointer"
        >
          <span>{expanded ? "▼ Hide Arguments" : "▶ View Arguments & Audit Payload"}</span>
        </button>
      </div>

      {expanded && (
        <div className="mt-2 p-2 rounded bg-surface-2 border border-border font-mono text-[11px] overflow-x-auto text-text-2 space-y-1">
          <div>
            <span className="font-semibold text-text">Arguments:</span>
            <pre className="whitespace-pre-wrap">
              {typeof toolCall.arguments === "string"
                ? toolCall.arguments
                : JSON.stringify(toolCall.arguments, null, 2)}
            </pre>
          </div>
          {toolCall.raw_output && (
            <div>
              <span className="font-semibold text-text">Raw Output:</span>
              <pre className="whitespace-pre-wrap">{toolCall.raw_output}</pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
