"use client";

import React from "react";
import MermaidDiagram from "./MermaidDiagram";

export default function NetworkTopologyDiagram({ className = "" }: { className?: string }) {
  const chart = `graph LR
    browser["Browser"] -->|"Same-origin requests"| frontend["Next.js proxy"]
    frontend -->|"Private application API"| backend["FastAPI"]
    backend -->|"Configured local inference endpoint"| models["Open-weight model runtime"]
    backend -->|"Local files and indexes"| storage["SQLite, Chroma and object store"]
    backend -->|"Separate isolated daemon required"| worker["Docker code worker"]
    external["Other network destinations"] -.->|"Must be blocked and checked externally"| host["Host firewall and packet capture"]`;
  return <div className={`p-5 bg-surface border border-border rounded-2xl shadow-xs space-y-4 ${className}`}>
    <div className="flex items-center justify-between pb-2 border-b border-border-subtle">
      <div><h3 className="font-serif font-bold text-base text-text">Deployment components</h3>
        <p className="text-xs text-text-3">Illustrative only; this is not a live connection trace.</p></div>
      <span className="text-xs px-2 py-0.5 rounded bg-amber-100 text-amber-800">Egress verification pending</span>
    </div>
    <div className="bg-bg-base/70 rounded-xl p-4 border border-border overflow-x-auto flex justify-center"><MermaidDiagram code={chart} /></div>
  </div>;
}
