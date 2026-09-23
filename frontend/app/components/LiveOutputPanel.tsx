"use client";

import React, { useState } from "react";
import MarkdownMessage from "./MarkdownMessage";

interface LiveOutputPanelProps {
  content: string;
  isStreaming?: boolean;
  className?: string;
}

export default function LiveOutputPanel({
  content,
  isStreaming = false,
  className = "",
}: LiveOutputPanelProps) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className={`bg-surface border border-border rounded-2xl p-5 shadow-xs space-y-3 ${className}`}>
      <div className="flex items-center justify-between border-b border-border-subtle pb-3">
        <div className="flex items-center gap-2">
          <span className="text-sm">🧠</span>
          <h3 className="font-serif font-bold text-sm text-text">Agent Synthesis & Reasoning</h3>
          {isStreaming && (
            <span className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-accent/10 text-accent text-[11px] font-mono font-medium animate-pulse">
              <span className="w-1.5 h-1.5 rounded-full bg-accent" />
              Streaming Local Weights
            </span>
          )}
        </div>
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="text-xs text-text-3 hover:text-accent font-medium"
        >
          {collapsed ? "Expand Reasoning" : "Collapse"}
        </button>
      </div>

      {!collapsed && (
        <div className="text-sm text-text-2 space-y-2 leading-relaxed">
          {content ? (
            <MarkdownMessage content={content} />
          ) : (
            <p className="text-xs text-text-3 italic">
              Agent is formulating reasoning and cross-checking knowledge base...
            </p>
          )}
        </div>
      )}
    </div>
  );
}
