"use client";

import React, { useRef, useEffect } from "react";
import type { ToolCallEvent } from "@/app/types";
import ToolCallRow from "./ToolCallRow";

interface ToolCallTimelineProps {
  toolCalls: ToolCallEvent[];
  className?: string;
}

export default function ToolCallTimeline({
  toolCalls,
  className = "",
}: ToolCallTimelineProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [toolCalls.length]);

  return (
    <div className={`space-y-2.5 ${className}`}>
      <div className="flex items-center justify-between px-1">
        <h3 className="text-xs font-mono font-semibold uppercase tracking-wider text-text-3">
          Live Tool Executions & Sandbox Audit ({toolCalls.length})
        </h3>
        <span className="text-[10px] font-mono text-green flex items-center gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-green animate-pulse" />
          <span>Air-Gapped Stream</span>
        </span>
      </div>

      {toolCalls.length === 0 ? (
        <div className="p-4 rounded-xl border border-dashed border-border text-center text-xs text-text-3">
          Awaiting first tool invocation from agent...
        </div>
      ) : (
        <div className="space-y-2 max-h-[420px] overflow-y-auto pr-1">
          {toolCalls.map((tc) => (
            <ToolCallRow key={tc.id} toolCall={tc} />
          ))}
          <div ref={bottomRef} />
        </div>
      )}
    </div>
  );
}
