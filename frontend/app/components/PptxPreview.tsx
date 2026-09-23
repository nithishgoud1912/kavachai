"use client";

import React, { useState } from "react";
import type { ArtifactItem } from "@/app/types";
import { downloadArtifact } from "@/app/services/fileDownload";
import SovereignBadge from "./SovereignBadge";
import ModelChip from "./ModelChip";

interface PptxPreviewProps {
  artifact: ArtifactItem;
  className?: string;
}

export default function PptxPreview({ artifact, className = "" }: PptxPreviewProps) {
  const slides = artifact.metadata?.slides_data || [
    {
      title: "MRPL Crude Distillation Unit (CDU-II)",
      points: [
        "Equipment Under Review: Crude Charge Pump P-204A",
        "Operating Capacity: 85% Designed Flow (1,450 m³/h)",
        "Condition Trigger: Triaxial vibration alarm spike on DE & NDE bearings",
      ],
      speaker_notes: "Introduces the asset overview and reason for urgent plant technical review.",
    },
    {
      title: "Vibration FFT Spectral Diagnostics",
      points: [
        "Peak Frequency: 142.4 Hz (matches Ball Pass Frequency Outer Race)",
        "Amplitude: 9.8 mm/s RMS (exceeds ISO 10816 threshold of 4.5 mm/s)",
        "Thermal Imaging: 78.4°C on outboard bearing housing",
      ],
      speaker_notes: "Key technical evidence verifying mechanical bearing defect rather than cavitation.",
    },
    {
      title: "Mitigation & Pump Switchover Sequence",
      points: [
        "Step 1: Verify standby pump P-204B priming and lube levels",
        "Step 2: Crack open discharge valve HV-204B bypass manifold",
        "Step 3: Equalize differential pressure and initiate motor start",
        "Step 4: Execute LOTO isolation on P-204A for bearing overhaul",
      ],
      speaker_notes: "Zero throughput loss protocol endorsed by operations.",
    },
  ];

  const [activeSlide, setActiveSlide] = useState(0);

  const handleDownload = () => {
    const textContent = `${artifact.name}\n\n${slides
      .map(
        (s, i) =>
          `--- Slide ${i + 1}: ${s.title} ---\n${s.points
            .map((p) => `• ${p}`)
            .join("\n")}\nNotes: ${s.speaker_notes}\n`
      )
      .join("\n")}`;
    downloadArtifact(artifact.name, textContent);
  };

  const curr = slides[activeSlide];

  return (
    <div className={`space-y-4 max-w-5xl mx-auto ${className}`}>
      {/* Top Bar Actions */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-4 bg-surface border border-border rounded-2xl shadow-xs">
        <div className="flex items-center gap-3">
          <span className="text-3xl">📙</span>
          <div>
            <h2 className="font-serif font-bold text-base text-text">{artifact.name}</h2>
            <div className="flex items-center gap-2 pt-0.5 text-xs text-text-3 font-mono">
              <ModelChip model={artifact.model_used} size="sm" />
              <span>·</span>
              <span>{slides.length} Slides</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <SovereignBadge size="sm" />
          <button
            onClick={handleDownload}
            className="px-4 py-2 rounded-xl bg-accent text-white hover:bg-accent-hover text-xs font-semibold shadow-xs transition-colors cursor-pointer"
          >
            Download .PPTX
          </button>
        </div>
      </div>

      {/* Main Slide + Thumbnail Layout */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Left: Thumbnail Strip */}
        <div className="md:col-span-1 space-y-2 max-h-[500px] overflow-y-auto pr-1">
          {slides.map((s, idx) => (
            <button
              key={idx}
              onClick={() => setActiveSlide(idx)}
              className={`w-full text-left p-3 rounded-xl border transition-all cursor-pointer ${
                activeSlide === idx
                  ? "bg-accent/10 border-accent text-accent font-semibold shadow-xs"
                  : "bg-surface border-border hover:bg-surface-2 text-text-2"
              }`}
            >
              <div className="text-[10px] font-mono text-text-3 mb-1">Slide {idx + 1}</div>
              <div className="text-xs truncate font-medium">{s.title}</div>
            </button>
          ))}
        </div>

        {/* Right: Active Slide Display */}
        <div className="md:col-span-3 space-y-3">
          <div className="aspect-[16/9] bg-surface border border-border rounded-2xl p-8 sm:p-12 shadow-sm flex flex-col justify-between">
            <div className="space-y-6">
              <div className="border-b border-border pb-3 flex items-center justify-between">
                <span className="text-[10px] font-mono text-accent uppercase tracking-wider font-semibold">
                  MRPL Executive Briefing · Confidential
                </span>
                <span className="text-xs font-mono text-text-3">
                  Slide {activeSlide + 1} of {slides.length}
                </span>
              </div>
              <h1 className="font-serif text-2xl font-bold text-text">{curr.title}</h1>
              <ul className="space-y-3">
                {curr.points.map((pt, i) => (
                  <li key={i} className="flex items-start gap-2.5 text-sm text-text-2">
                    <span className="text-accent mt-0.5">▪</span>
                    <span>{pt}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="pt-4 border-t border-border-subtle flex items-center justify-between text-[11px] text-text-3 font-mono">
              <span>Mangalore Refinery and Petrochemicals Ltd</span>
              <span>100% Sovereign On-Premise Generation</span>
            </div>
          </div>

          {/* Speaker Notes */}
          {curr.speaker_notes && (
            <div className="p-3 bg-surface-2/60 border border-border rounded-xl text-xs space-y-1">
              <span className="font-mono font-semibold uppercase text-text-3 text-[10px]">
                Speaker Notes:
              </span>
              <p className="text-text-2 italic">{curr.speaker_notes}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
