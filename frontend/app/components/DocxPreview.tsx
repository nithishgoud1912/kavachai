"use client";

import React, { useState } from "react";
import type { ArtifactItem } from "@/app/types";
import { downloadArtifact } from "@/app/services/fileDownload";
import SovereignBadge from "./SovereignBadge";
import ModelChip from "./ModelChip";

interface DocxPreviewProps {
  artifact: ArtifactItem;
  className?: string;
}

export default function DocxPreview({ artifact, className = "" }: DocxPreviewProps) {
  const sections = artifact.metadata?.sections || [
    {
      title: "1. Executive Summary & Problem Scope",
      content:
        "Severe vibration anomaly observed on Crude Charge Pump P-204A during routine condition monitoring. BPFO frequency spikes identify imminent bearing degradation requiring planned handover.",
    },
    {
      title: "2. Technical Diagnostic Findings",
      content:
        "Triaxial vibration spectra shows 142.4 Hz harmonics at 9.8 mm/s RMS (ISO 10816 Zone D). Outer ring raceway flaking confirmed via high-frequency demodulation analysis.",
    },
    {
      title: "3. Operational Isolation & Safety Mitigation",
      content:
        "Switch refinery feed flow to standby pump P-204B via manifold valve HV-204B. Perform full LOTO electrical and mechanical isolation before disassembly.",
    },
    {
      title: "4. Procurement & Overhaul Schedule",
      content:
        "Replacement SKF 6318 bearing available in MRPL Central Warehouse. Estimated maintenance turnaround: 6.5 hours. Zero crude distillation throughput impact.",
    },
  ];

  const [activeSections, setActiveSections] = useState(sections);
  const [regeneratingIndex, setRegeneratingIndex] = useState<number | null>(null);

  const handleRegenerate = (index: number) => {
    setRegeneratingIndex(index);
    setTimeout(() => {
      const copy = [...activeSections];
      copy[index] = {
        ...copy[index],
        content:
          copy[index].content +
          " [Section refined with additional safety clearance criteria from MRPL Plant Standard Std-04].",
      };
      setActiveSections(copy);
      setRegeneratingIndex(null);
    }, 900);
  };

  const handleDownload = () => {
    const textContent = `${artifact.name}\n\n${activeSections
      .map((s) => `${s.title}\n${s.content}\n`)
      .join("\n")}\n\nGenerated on-premise by ${artifact.model_used}`;
    downloadArtifact(artifact.name, textContent);
  };

  return (
    <div className={`space-y-4 max-w-4xl mx-auto ${className}`}>
      {/* Top Bar Actions */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-4 bg-surface border border-border rounded-2xl shadow-xs">
        <div className="flex items-center gap-3">
          <span className="text-3xl">📘</span>
          <div>
            <h2 className="font-serif font-bold text-base text-text">{artifact.name}</h2>
            <div className="flex items-center gap-2 pt-0.5 text-xs text-text-3 font-mono">
              <ModelChip model={artifact.model_used} size="sm" />
              <span>·</span>
              <span>{activeSections.length} Sections</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <SovereignBadge size="sm" />
          <button
            onClick={handleDownload}
            className="px-4 py-2 rounded-xl bg-accent text-white hover:bg-accent-hover text-xs font-semibold shadow-xs transition-colors cursor-pointer"
          >
            Download .DOCX
          </button>
        </div>
      </div>

      {/* Formal Paper-Styled Document Preview */}
      <div className="bg-surface border border-border rounded-2xl p-8 sm:p-12 shadow-sm space-y-8 font-sans">
        <div className="border-b-2 border-accent pb-4 flex items-end justify-between">
          <div>
            <p className="text-[11px] font-mono uppercase tracking-widest text-text-3">
              Mangalore Refinery and Petrochemicals Limited
            </p>
            <h1 className="font-serif text-2xl sm:text-3xl font-bold text-text mt-1">
              Executive Approval & Action Note
            </h1>
          </div>
          <div className="text-right text-xs font-mono text-text-3">
            <p>MRPL/CDU-II/2026/04</p>
            <p>{new Date(artifact.created_at).toLocaleDateString()}</p>
          </div>
        </div>

        {/* Document Sections */}
        <div className="space-y-6">
          {activeSections.map((sec, idx) => (
            <div key={idx} className="group relative space-y-2 p-4 rounded-xl hover:bg-bg-base/60 transition-colors">
              <div className="flex items-center justify-between">
                <h3 className="font-serif font-bold text-base text-text">{sec.title}</h3>
                <button
                  onClick={() => handleRegenerate(idx)}
                  disabled={regeneratingIndex === idx}
                  className="opacity-0 group-hover:opacity-100 text-[11px] text-accent hover:underline font-mono transition-opacity"
                >
                  {regeneratingIndex === idx ? "Regenerating section..." : "↻ Regenerate with VLM"}
                </button>
              </div>
              <p className="text-sm text-text-2 leading-relaxed">{sec.content}</p>
            </div>
          ))}
        </div>

        {/* Formal Footer Sign-Off Blocks */}
        <div className="pt-8 border-t border-border grid grid-cols-3 gap-6 text-xs text-text-3 font-mono">
          <div>
            <p className="font-bold text-text">Prepared By:</p>
            <p>AI Diagnostic Agent (Local)</p>
            <p className="text-[10px] text-green">Verified Air-Gapped</p>
          </div>
          <div>
            <p className="font-bold text-text">Reviewed By:</p>
            <p>Condition Monitoring Lead</p>
            <p className="text-[10px]">Pending Digital Sign</p>
          </div>
          <div>
            <p className="font-bold text-text">Approved By:</p>
            <p>Chief General Manager (Plant)</p>
            <p className="text-[10px]">MRPL Operations</p>
          </div>
        </div>
      </div>
    </div>
  );
}
