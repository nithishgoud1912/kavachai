"use client";

import React, { useState } from "react";
import MermaidDiagram from "./MermaidDiagram";

interface EquipmentGraphPanelProps {
  className?: string;
}

export default function EquipmentGraphPanel({ className = "" }: EquipmentGraphPanelProps) {
  const [selectedTag, setSelectedTag] = useState<string>("P-204A");

  const mermaidChart = `graph LR
    classDef pump fill:#FEFEFE,stroke:#C35C3E,stroke-width:2px,color:#2D2A26;
    classDef valve fill:#EDE7DE,stroke:#998C84,stroke-width:1px,color:#2D2A26;
    classDef alert fill:#F2E6E3,stroke:#B83838,stroke-width:2px,color:#B83838;

    TK201["Crude Storage TK-201"] --> MOV101["MOV-101 Suction Header"]
    MOV101 --> P204A["P-204A (Crude Feed Pump - Vibration Alert)"]:::alert
    MOV101 --> P204B["P-204B (Standby Pump)"]:::pump

    P204A --> HV204A["Discharge Valve HV-204A"]:::valve
    P204B --> HV204B["Discharge Valve HV-204B"]:::valve

    HV204A --> CDU2["CDU-II Atmospheric Column"]
    HV204B --> CDU2

    P204A -.->|"Bypass Loop"| HV204B
`;

  return (
    <div className={`p-5 bg-surface border border-border rounded-2xl shadow-xs space-y-4 ${className}`}>
      <div className="flex items-center justify-between pb-2 border-b border-border-subtle">
        <div>
          <h3 className="font-serif font-bold text-base text-text">
            P&ID Process Topology & Equipment Graph
          </h3>
          <p className="text-xs text-text-3 font-mono">
            Extracted from CDU-II Engineering Drawing MRPL-CDU2-PID-004
          </p>
        </div>
        <span className="text-xs font-mono px-2 py-0.5 rounded bg-surface-2 border border-border text-text-2">
          Mermaid SVG Topology
        </span>
      </div>

      <div className="bg-bg-base/70 rounded-xl p-4 border border-border overflow-x-auto flex justify-center">
        <MermaidDiagram code={mermaidChart} />
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3 text-xs pt-1">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded bg-red" />
            <span className="text-text-2 font-mono">P-204A: Anomaly (BPFO 142.4Hz)</span>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded bg-accent" />
            <span className="text-text-2 font-mono">P-204B: Standby Ready</span>
          </span>
        </div>
        <span className="text-text-3 font-mono text-[11px]">
          Click elements in diagram or view source P&ID drawing
        </span>
      </div>
    </div>
  );
}
