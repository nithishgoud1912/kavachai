"use client";

import React from "react";

interface AllowlistPanelProps {
  allowlist?: string[];
  className?: string;
}

const AUTHORIZED_DESTINATIONS = [
  {
    host: "localhost / 127.0.0.1",
    port: "3000, 8000",
    role: "Next.js UI & FastAPI Orchestrator IPC",
    protocol: "HTTP/1.1 Loopback",
    status: "Allowed",
  },
  {
    host: "localhost:11434 / ollama",
    port: "11434",
    role: "Local AI Inference Engine (Reasoning, Coder, VLM)",
    protocol: "REST Streaming IPC",
    status: "Allowed",
  },
  {
    host: "::1",
    port: "All Loopback",
    role: "IPv6 System Local Loopback",
    protocol: "TCP / UDP Loopback",
    status: "Allowed",
  },
  {
    host: "SQLite & Chroma Embeddings",
    port: "Local Memory",
    role: "Relational DB & Semantic Vector Indexes",
    protocol: "In-Process Memory",
    status: "Allowed",
  },
  {
    host: "Hardened Sandbox Container",
    port: "None",
    role: "Engineering Calculations Worker (--network none)",
    protocol: "Docker IPC Socket",
    status: "Allowed",
  },
];

export default function AllowlistPanel({
  allowlist = [],
  className = "",
}: AllowlistPanelProps) {
  return (
    <div className={`p-5 bg-surface border border-border rounded-2xl shadow-xs space-y-4 ${className}`}>
      {/* ─── Header ─── */}
      <div className="flex items-center justify-between pb-2 border-b border-border-subtle flex-wrap gap-2">
        <div>
          <h3 className="font-serif font-bold text-base text-text">Authorized Sovereign Allowlist</h3>
          <p className="text-xs text-text-3 font-mono">
            Strict Default-Deny: Any destination outside this table is terminated instantly
          </p>
        </div>
        <span className="text-xs font-mono px-2.5 py-0.5 rounded-full bg-green/10 text-green border border-green/30 font-semibold">
          Strict Whitelist
        </span>
      </div>

      {/* ─── Permitted Endpoints Grid ─── */}
      <div className="space-y-2.5">
        {AUTHORIZED_DESTINATIONS.map((item, idx) => (
          <div
            key={idx}
            className="p-3 rounded-xl border border-border bg-bg-base/60 text-xs space-y-1 hover:border-accent/40 transition-colors"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-green shrink-0" />
                <span className="font-mono font-bold text-text">{item.host}</span>
              </div>
              <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-surface border border-border text-text-3">
                {item.port}
              </span>
            </div>
            <p className="text-[11px] text-text-2 pl-4">{item.role}</p>
          </div>
        ))}
      </div>

      {/* ─── Prohibited External WAN Card ─── */}
      <div className="p-3.5 rounded-xl border border-red/30 bg-red/5 space-y-1.5 text-xs">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-red shrink-0" />
            <span className="font-mono font-bold text-red">0.0.0.0 / WAN / Public Cloud APIs</span>
          </div>
          <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-red/10 border border-red/20 text-red font-bold">
            DROP ALL
          </span>
        </div>
        <p className="text-[11px] text-text-2 pl-4">
          All external gateways, tracking beacons, and cloud endpoints (OpenAI, Anthropic, HuggingFace, etc.) are strictly dropped before packets reach the physical interface.
        </p>
      </div>

      {/* ─── Allowlist Config Summary ─── */}
      <div className="text-[11px] font-mono text-text-3 pt-2 border-t border-border-subtle flex items-center justify-between">
        <span>Configured hosts: {allowlist.length > 0 ? allowlist.join(", ") : "localhost, 127.0.0.1, ::1, ollama"}</span>
        <span className="text-green font-semibold">100% On-Premise</span>
      </div>
    </div>
  );
}
