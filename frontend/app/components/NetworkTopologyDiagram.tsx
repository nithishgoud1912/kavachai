"use client";

import React from "react";
import MermaidDiagram from "./MermaidDiagram";

interface NetworkTopologyDiagramProps {
  className?: string;
}

export default function NetworkTopologyDiagram({ className = "" }: NetworkTopologyDiagramProps) {
  const chart = `graph TB
    subgraph Airgap["MRPL Sovereign Air-Gapped Boundary (100% On-Premise Industrial Network)"]
      style Airgap fill:#F9F7F4,stroke:#2D794D,stroke-width:2px,stroke-dasharray: 4 4;

      FE["Next.js 16 Sovereign UI<br/>(localhost:3000)"]
      BE["FastAPI Core Orchestrator<br/>(localhost:8000)"]
      LLM["Local AI Inference Engine<br/>(localhost:11434)<br/><b>Reasoning model</b><br/><b>coder model</b> (engineering calculations)<br/><b>vision language model</b><br/><b>Embedding model</b>"]
      DB["Local Knowledge Base & Indexes<br/>(SQLite + Chroma Local Embeddings)"]
      SANDBOX["Hardened Code Sandbox<br/>(Docker isolated --network none)"]

      FE <-->|"Internal HTTP / Loopback"| BE
      BE <-->|"Local Inference Stream"| LLM
      BE <-->|"Local Vector & Audit Storage"| DB
      BE <-->|"Isolated Calculations Exec"| SANDBOX
    end

    EXT["External Internet & Public Cloud APIs<br/>(OpenAI, Anthropic, Public Gateways)"]
    style EXT fill:#F2E6E3,stroke:#B83838,stroke-width:2px,color:#B83838;

    BE -.->|"BLOCKED BY SOVEREIGN AUDIT HOOK (0 Packets)"| EXT
`;

  return (
    <div className={`p-5 bg-surface border border-border rounded-2xl shadow-xs space-y-4 ${className}`}>
      <div className="flex items-center justify-between pb-3 border-b border-border-subtle flex-wrap gap-2">
        <div>
          <h3 className="font-serif font-bold text-base text-text">
            Physical & Logical Network Architecture Topology
          </h3>
          <p className="text-xs text-text-3 font-mono">
            Mirrors refinery on-premise topology with non-routable loopback interfaces
          </p>
        </div>
        <span className="text-xs font-mono px-3 py-1 rounded-full bg-green/10 border border-green/30 text-green font-semibold flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-green" />
          <span>Network Isolation Verified</span>
        </span>
      </div>

      <div className="bg-bg-base/70 rounded-xl p-4 border border-border overflow-x-auto flex justify-center">
        <MermaidDiagram code={chart} />
      </div>

      {/* ─── Defense-in-Depth Ring Callouts ─── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-1">
        <div className="p-3 rounded-xl border border-border bg-bg-base/50 space-y-1">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-text">
            <span className="text-accent">🔒</span>
            <span>1. Loopback-Only Transport</span>
          </div>
          <p className="text-[11px] text-text-3 leading-relaxed">
            All IPC between Next.js, FastAPI, and Ollama is constrained to <code className="font-mono text-accent">127.0.0.1</code> and <code className="font-mono text-accent">::1</code>.
          </p>
        </div>

        <div className="p-3 rounded-xl border border-border bg-bg-base/50 space-y-1">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-text">
            <span className="text-green">🛡️</span>
            <span>2. Kernel Socket Auditing</span>
          </div>
          <p className="text-[11px] text-text-3 leading-relaxed">
            CPython <code className="font-mono text-green">sys.addaudithook</code> intercepts DNS resolution and socket calls before any network packet can reach the NIC.
          </p>
        </div>

        <div className="p-3 rounded-xl border border-border bg-bg-base/50 space-y-1">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-text">
            <span className="text-accent">⚙️</span>
            <span>3. AST Sandbox Guard</span>
          </div>
          <p className="text-[11px] text-text-3 leading-relaxed">
            Engineering calculations and Python scripts are checked via AST before execution; network modules are rejected immediately.
          </p>
        </div>
      </div>
    </div>
  );
}
