"use client";

import React, { use, useState } from "react";
import Link from "next/link";
import AppShell from "@/app/components/AppShell";
import Badge from "@/app/components/Badge";
import SovereignBadge from "@/app/components/SovereignBadge";

export default function DocumentDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [rerunning, setRerunning] = useState(false);
  const [activeTier, setActiveTier] = useState("Tier 3 (Tesseract 5.3)");

  const handleRerunOCR = () => {
    setRerunning(true);
    setTimeout(() => {
      setActiveTier("Tier 4 (Qwen2.5-VL Multimodal Fallback)");
      setRerunning(false);
    }, 1200);
  };

  const chunks = [
    {
      index: 1,
      page: 1,
      method: "Native PDF Stream",
      tokenCount: 412,
      preview: "MRPL Crude Distillation Unit (CDU-II) Technical Inspection. Pump P-204A operational log recorded at 08:00 hrs. Vibration monitoring triggered automatically.",
    },
    {
      index: 2,
      page: 2,
      method: "Tesseract 5.3 Binarized",
      tokenCount: 388,
      preview: "Triaxial spectra readings: Horizontal 9.8 mm/s, Vertical 7.2 mm/s, Axial 4.1 mm/s. Harmonics confirm outer ring defect (BPFO) @ 142.4 Hz.",
    },
    {
      index: 3,
      page: 3,
      method: "VLM Diagram OCR",
      tokenCount: 295,
      preview: "P&ID Schematic snippet: Pump bypass loop HV-204B connects manifold to standby pump P-204B with manual isolation check valve CV-204.",
    },
  ];

  return (
    <AppShell
      title={`Document: ${id}`}
      subtitle="Extraction Chunks & OCR Inspect"
      breadcrumbs={[
        { label: "Workspace", href: "/workspace" },
        { label: "Knowledge Base", href: "/knowledge-base" },
        { label: id },
      ]}
    >
      <div className="space-y-6 max-w-5xl mx-auto pb-12">
        {/* Document Metadata Card */}
        <div className="p-6 bg-surface border border-border rounded-2xl shadow-xs space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <span className="text-3xl">📄</span>
              <div>
                <h2 className="font-serif text-lg font-bold text-text">
                  P-204A_Vibration_Spectra_Apr2026.pdf
                </h2>
                <div className="flex items-center gap-2 text-xs font-mono text-text-3">
                  <span>Scope: MAINTENANCE</span>
                  <span>·</span>
                  <span>3 Pages / 3 Chunks</span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <SovereignBadge size="sm" />
              <button
                onClick={handleRerunOCR}
                disabled={rerunning}
                className="px-3 py-1.5 rounded-xl border border-accent text-accent hover:bg-accent/10 text-xs font-semibold transition-colors cursor-pointer"
              >
                {rerunning ? "Executing VLM Extraction..." : "↻ Re-Run with Tier 4 VLM"}
              </button>
            </div>
          </div>

          <div className="pt-2 border-t border-border-subtle grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-mono">
            <div>
              <span className="text-text-3 block text-[10px] uppercase">Current OCR Tier</span>
              <span className="text-text font-semibold">{activeTier}</span>
            </div>
            <div>
              <span className="text-text-3 block text-[10px] uppercase">Vector Embedding</span>
              <span className="text-green font-semibold">Indexed (768-dim)</span>
            </div>
            <div>
              <span className="text-text-3 block text-[10px] uppercase">Storage Status</span>
              <span className="text-text font-semibold">Local SSD Encrypted</span>
            </div>
            <div>
              <span className="text-text-3 block text-[10px] uppercase">Air-Gap Egress</span>
              <span className="text-green font-semibold">0 External Calls</span>
            </div>
          </div>
        </div>

        {/* Chunks List */}
        <div className="bg-surface border border-border rounded-2xl p-5 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-border-subtle">
            <h3 className="font-serif font-bold text-base text-text">
              Indexed Chunks & Extraction Lineage
            </h3>
            <span className="text-xs font-mono text-text-3">
              Chunks are semantically searchable by all agents
            </span>
          </div>

          <div className="space-y-3">
            {chunks.map((chunk) => (
              <div
                key={chunk.index}
                className="p-4 rounded-xl border border-border bg-bg-base/40 space-y-2 hover:bg-surface transition-colors"
              >
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-accent">
                      Chunk #{chunk.index}
                    </span>
                    <span className="text-text-3 font-mono">Page {chunk.page}</span>
                    <Badge variant="complete" label={chunk.method} size="sm" />
                  </div>
                  <span className="text-[11px] font-mono text-text-3">
                    {chunk.tokenCount} tokens
                  </span>
                </div>
                <p className="text-xs text-text leading-relaxed font-sans font-medium">
                  {chunk.preview}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
