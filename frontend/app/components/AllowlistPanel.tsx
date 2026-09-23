"use client";

import React from "react";

interface AllowlistPanelProps {
  allowlist?: string[];
  className?: string;
}

export default function AllowlistPanel({
  allowlist = [
    "127.0.0.1:11434 (Local Ollama Engine - Qwen 2.5 / CodeLlama)",
    "localhost:11434 (Local Ollama Engine)",
    "127.0.0.1:8000 (FastAPI Core Backend Engine)",
    "localhost:8000 (FastAPI Core Backend Engine)",
    "127.0.0.1:5432 (Local PostgreSQL Vector Database)",
    "internal://chromadb (In-Memory On-Premise Vector Store)",
  ],
  className = "",
}: AllowlistPanelProps) {
  return (
    <div className={`p-5 bg-surface border border-border rounded-2xl shadow-xs space-y-3 ${className}`}>
      <div className="flex items-center justify-between pb-2 border-b border-border-subtle">
        <div>
          <h3 className="font-serif font-bold text-base text-text">Authorized Sovereign Allowlist</h3>
          <p className="text-xs text-text-3 font-mono">
            Strict loopback policy — any destination outside this list triggers immediate kernel block
          </p>
        </div>
        <span className="text-xs font-mono px-2 py-0.5 rounded bg-green/10 text-green font-semibold">
          Hardened Policy
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
        {allowlist.map((host, idx) => (
          <div
            key={idx}
            className="flex items-center gap-2 p-2.5 rounded-xl border border-border bg-bg-base/60 text-xs font-mono text-text"
          >
            <span className="w-2 h-2 rounded-full bg-green shrink-0" />
            <span className="truncate">{host}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
