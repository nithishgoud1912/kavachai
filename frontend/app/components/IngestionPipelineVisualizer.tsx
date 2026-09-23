"use client";

import React from "react";

interface Step {
  id: number;
  name: string;
  engine: string;
  description: string;
  status: "completed" | "active" | "standby";
}

interface IngestionPipelineVisualizerProps {
  currentTier?: number; // 1 to 4
  className?: string;
}

export default function IngestionPipelineVisualizer({
  currentTier = 3,
  className = "",
}: IngestionPipelineVisualizerProps) {
  const steps: Step[] = [
    {
      id: 1,
      name: "Tier 1: Native Text Extraction",
      engine: "pdfminer.six / PyMuPDF",
      description: "Direct vector character stream & font parsing for digital PDFs",
      status: currentTier > 1 ? "completed" : currentTier === 1 ? "active" : "standby",
    },
    {
      id: 2,
      name: "Tier 2: Character Density & Layout",
      engine: "Internal Heuristic Engine",
      description: "Scanned vs digital discrimination (flags low density pages)",
      status: currentTier > 2 ? "completed" : currentTier === 2 ? "active" : "standby",
    },
    {
      id: 3,
      name: "Tier 3: Industrial OCR",
      engine: "Tesseract 5.3 (Local)",
      description: "Binarization, deskewing & OCR for printed tabular reports",
      status: currentTier > 3 ? "completed" : currentTier === 3 ? "active" : "standby",
    },
    {
      id: 4,
      name: "Tier 4: Multimodal VLM Fallback",
      engine: "Qwen 2.5 VL (Local 3B)",
      description: "Complex handwritten annotations, P&ID symbols & low-contrast sketches",
      status: currentTier === 4 ? "active" : "standby",
    },
  ];

  return (
    <div className={`p-5 bg-surface border border-border rounded-2xl shadow-xs space-y-4 ${className}`}>
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-serif font-bold text-sm text-text">
            4-Tier Sovereign OCR & Document Ingestion Pipeline
          </h3>
          <p className="text-xs text-text-3 font-mono">
            Every confidential refinery page is extracted on-site without external cloud OCR APIs
          </p>
        </div>
        <span className="text-xs font-mono px-2.5 py-1 rounded-full bg-accent/10 text-accent font-semibold">
          Active Tier: Tier {currentTier}
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
        {steps.map((s) => {
          const isDone = s.status === "completed";
          const isActive = s.status === "active";

          return (
            <div
              key={s.id}
              className={`p-3.5 rounded-xl border transition-all space-y-1.5 ${
                isActive
                  ? "bg-accent/5 border-accent shadow-xs"
                  : isDone
                  ? "bg-[#E9F0EC]/50 border-[#2D794D]/30"
                  : "bg-surface-2/30 border-border opacity-65"
              }`}
            >
              <div className="flex items-center justify-between">
                <span
                  className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-mono font-bold ${
                    isDone
                      ? "bg-green text-white"
                      : isActive
                      ? "bg-accent text-white animate-pulse"
                      : "bg-surface-2 text-text-3 border border-border"
                  }`}
                >
                  {isDone ? "✓" : s.id}
                </span>
                <span className="text-[10px] font-mono uppercase text-text-3">
                  {s.status}
                </span>
              </div>

              <h4 className="font-semibold text-xs text-text leading-tight">{s.name}</h4>
              <p className="text-[10px] font-mono text-accent">{s.engine}</p>
              <p className="text-[11px] text-text-2 leading-relaxed">{s.description}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
