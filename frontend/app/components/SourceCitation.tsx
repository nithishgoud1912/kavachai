"use client";

import React from "react";
import type { EvidenceReference } from "@/app/types";

interface SourceCitationProps {
  citation: EvidenceReference;
  onClick?: (citation: EvidenceReference) => void;
  className?: string;
}

export default function SourceCitation({
  citation,
  onClick,
  className = "",
}: SourceCitationProps) {
  let icon = "📄";
  if (citation.type === "pid_drawing") icon = "📐";
  if (citation.type === "dataset") icon = "📊";

  return (
    <button
      type="button"
      onClick={() => onClick?.(citation)}
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-surface-2 hover:bg-surface border border-border text-[11px] font-mono text-text transition-all cursor-pointer ${className}`}
      title={`Inspect cited evidence: ${citation.label} (Page ${citation.page || 1})`}
    >
      <span className="text-[10px]">{icon}</span>
      <span className="truncate max-w-[150px] font-medium">{citation.label}</span>
      {citation.page && <span className="text-text-3">p.{citation.page}</span>}
    </button>
  );
}
