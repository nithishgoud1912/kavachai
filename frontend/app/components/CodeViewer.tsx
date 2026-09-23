"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import type { ArtifactItem } from "@/app/types";
import { downloadArtifact } from "@/app/services/fileDownload";
import SovereignBadge from "./SovereignBadge";
import ModelChip from "./ModelChip";

interface CodeViewerProps {
  artifact: ArtifactItem;
  className?: string;
}

export default function CodeViewer({ artifact, className = "" }: CodeViewerProps) {
  const router = useRouter();
  const [copied, setCopied] = useState(false);

  const samplePython = `"""
MRPL Air-Gapped Industrial Analytics
Asset: P-204 Crude Charge Pump
Calculation: Characteristic Bearing Fault Frequencies (SKF 6318)
"""

import numpy as np

RPM = 2980.0
SHAFT_HZ = RPM / 60.0  # 49.67 Hz

# Bearing Geometry Constants (SKF 6318)
N_BALLS = 8
BALL_DIA_MM = 30.0
PITCH_DIA_MM = 140.0
CONTACT_ANGLE_RAD = 0.0

cos_theta = np.cos(CONTACT_ANGLE_RAD)
gamma = (BALL_DIA_MM / PITCH_DIA_MM) * cos_theta

# ISO Characteristic Formulas
BPFO = (N_BALLS / 2.0) * SHAFT_HZ * (1.0 - gamma)
BPFI = (N_BALLS / 2.0) * SHAFT_HZ * (1.0 + gamma)
BSF  = (PITCH_DIA_MM / (2.0 * BALL_DIA_MM)) * SHAFT_HZ * (1.0 - gamma**2)
FTF  = 0.5 * SHAFT_HZ * (1.0 - gamma)

print(f"Calculated BPFO: {BPFO:.2f} Hz (Matches 142.4 Hz sensor spike)")
print(f"Calculated BPFI: {BPFI:.2f} Hz")
print(f"Calculated BSF:  {BSF:.2f} Hz")
print(f"Calculated FTF:  {FTF:.2f} Hz")

# Severity Check
OVERALL_RMS_MM_S = 9.8
if OVERALL_RMS_MM_S > 4.5:
    print("STATUS: DANGER - ISO 10816 Zone D exceeded. Switch pump immediately.")
`;

  const code = artifact.metadata?.summary && artifact.metadata.summary.includes("import")
    ? artifact.metadata.summary
    : samplePython;

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleRunInSandbox = () => {
    // Save to sessionStorage and navigate to sandbox
    sessionStorage.setItem("sandbox_preset_code", code);
    router.push("/sandbox");
  };

  return (
    <div className={`space-y-4 max-w-5xl mx-auto ${className}`}>
      {/* Top Bar Actions */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-4 bg-surface border border-border rounded-2xl shadow-xs">
        <div className="flex items-center gap-3">
          <span className="text-3xl">💻</span>
          <div>
            <h2 className="font-serif font-bold text-base text-text">{artifact.name}</h2>
            <div className="flex items-center gap-2 pt-0.5 text-xs text-text-3 font-mono">
              <ModelChip model={artifact.model_used} size="sm" />
              <span>·</span>
              <span>Python 3.11</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <SovereignBadge size="sm" />
          <button
            onClick={handleCopy}
            className="px-3 py-1.5 rounded-xl border border-border text-xs text-text hover:bg-surface-2 transition-colors cursor-pointer"
          >
            {copied ? "✓ Copied" : "Copy Code"}
          </button>
          <button
            onClick={() => downloadArtifact(artifact.name, code, "text/x-python")}
            className="px-3 py-1.5 rounded-xl border border-border text-xs text-text hover:bg-surface-2 transition-colors cursor-pointer"
          >
            Download .py
          </button>
          <button
            onClick={handleRunInSandbox}
            className="px-4 py-2 rounded-xl bg-accent text-white hover:bg-accent-hover text-xs font-semibold shadow-xs transition-colors cursor-pointer"
          >
            Run in Air-Gapped Sandbox →
          </button>
        </div>
      </div>

      {/* Code Editor Window */}
      <div className="rounded-2xl border border-border bg-[#1E1E1E] text-[#D4D4D4] font-mono text-xs overflow-hidden shadow-sm">
        <div className="flex items-center justify-between px-4 py-2 bg-[#252526] border-b border-[#333333] text-text-3">
          <span className="text-[#9CDCFE]">{artifact.name}</span>
          <span className="text-[11px] text-[#6A9955]"># No Network Access (--network none)</span>
        </div>
        <pre className="p-4 sm:p-6 overflow-x-auto whitespace-pre leading-relaxed">
          {code}
        </pre>
      </div>
    </div>
  );
}
