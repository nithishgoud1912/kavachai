"use client";

import type { AgentName, AgentStatus } from "@/app/types";
import { AGENT_DISPLAY_NAMES } from "@/app/types";

interface AgentRowProps {
  agent: AgentName;
  status: AgentStatus;
  message: string;
  elapsed_ms: number;
  goal?: string;
  index: number;
}

const STATUS_COLORS: Record<AgentStatus, string> = {
  pending: "bg-text-3/30",
  working: "bg-purple",
  complete: "bg-green",
  skipped: "bg-orange/60",
  failed: "bg-red",
};

const STATUS_RING: Record<AgentStatus, string> = {
  pending: "border-text-3/30",
  working: "border-purple",
  complete: "border-green",
  skipped: "border-orange/60",
  failed: "border-red",
};

export default function AgentRow({
  agent,
  status,
  message,
  elapsed_ms,
  goal,
  index,
}: AgentRowProps) {
  const isPending = status === "pending";
  const isWorking = status === "working";

  return (
    <div
      className="flex items-center gap-4 py-3 px-4 rounded-lg
                 transition-colors duration-200 animate-fade-in-up-small
                 hover:bg-surface-2/50"
      style={{ animationDelay: `${index * 100}ms` }}
    >
      {/* Status Indicator */}
      <div className="relative flex-shrink-0">
        <div
          className={`w-3 h-3 rounded-full transition-colors duration-300 ${
            isPending
              ? "bg-transparent border-2 " + STATUS_RING[status]
              : STATUS_COLORS[status]
          }`}
        />
        {isWorking && (
          <div className="absolute inset-0 w-3 h-3 rounded-full bg-purple animate-ping opacity-40" />
        )}
      </div>

      {/* Agent Name */}
      <span
        className={`font-[family-name:var(--font-mono)] text-sm w-40 flex-shrink-0 ${
          isPending ? "text-text-3" : "text-text"
        }`}
      >
        {AGENT_DISPLAY_NAMES[agent]}
      </span>

      {/* Status Message */}
      <span className={`flex-1 text-sm ${isPending ? "text-text-3" : "text-text-2"}`}>
        {message || goal || (isPending ? "Waiting…" : "")}
        {isWorking && !message && (
          <span className="inline-flex gap-0.5 ml-1">
            <span className="animate-bounce" style={{ animationDelay: "0ms" }}>.</span>
            <span className="animate-bounce" style={{ animationDelay: "150ms" }}>.</span>
            <span className="animate-bounce" style={{ animationDelay: "300ms" }}>.</span>
          </span>
        )}
      </span>

      {/* Elapsed Time */}
      <span className="font-[family-name:var(--font-mono)] text-xs text-text-3 w-14 text-right flex-shrink-0">
        {status === "complete" || status === "failed" || status === "skipped"
          ? `${(elapsed_ms / 1000).toFixed(1)}s`
          : isWorking
          ? "⋯"
          : ""}
      </span>
    </div>
  );
}
