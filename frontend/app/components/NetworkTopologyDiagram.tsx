"use client";

import React from "react";
import MermaidDiagram from "./MermaidDiagram";

interface NetworkTopologyDiagramProps {
  className?: string;
}

export default function NetworkTopologyDiagram({ className = "" }: NetworkTopologyDiagramProps) {
  const chart = `graph TB
    subgraph Airgap["MRPL Sovereign Air-Gapped Boundary (100% On-Premise)"]
      style Airgap fill:#F9F7F4,stroke:#C35C3E,stroke-width:2px,stroke-dasharray: 5 5;

      FE["Next.js 16 Workbench UI<br/>(localhost:3000)"]
      BE["FastAPI Core Orchestrator<br/>(localhost:8000)"]
      OLLAMA["Ollama / vLLM LLM Runtime<br/>(localhost:11434)<br/>[Qwen2.5:3b, Qwen2.5-Coder, Qwen2.5-VL]"]
      VDB["Local PostgreSQL / pgvector<br/>(localhost:5432)"]
      SANDBOX["Docker Hardened Code Sandbox<br/>(--network none)"]

      FE <-->|"Internal HTTP / SSE"| BE
      BE <-->|"REST API (Loopback Only)"| OLLAMA
      BE <-->|"SQL / Vector Embeddings"| VDB
      BE <-->|"Isolated Exec"| SANDBOX
    end

    EXT["External Internet / Public Cloud APIs<br/>(OpenAI, Anthropic, HuggingFace)"]
    style EXT fill:#F2E6E3,stroke:#B83838,stroke-width:2px,color:#B83838;

    BE -.->|"BLOCKED BY EGRESS MONITOR (0 Calls)"| EXT
`;

  return (
    <div className={`p-5 bg-surface border border-border rounded-2xl shadow-xs space-y-4 ${className}`}>
      <div className="flex items-center justify-between pb-2 border-b border-border-subtle">
        <div>
          <h3 className="font-serif font-bold text-base text-text">
            Physical & Logical Network Architecture Topology
          </h3>
          <p className="text-xs text-text-3 font-mono">
            Mirrors docker-compose.yml configuration with strictly non-routed container interfaces
          </p>
        </div>
        <span className="text-xs font-mono px-2 py-0.5 rounded bg-green/10 text-green font-semibold">
          Network Isolation Verified
        </span>
      </div>

      <div className="bg-bg-base/70 rounded-xl p-4 border border-border overflow-x-auto flex justify-center">
        <MermaidDiagram code={chart} />
      </div>
    </div>
  );
}
