"use client";

import React from "react";
import Link from "next/link";
import type { ArtifactItem } from "@/app/types";
import { downloadArtifact } from "@/app/services/fileDownload";
import ModelChip from "./ModelChip";

interface ArtifactCardProps {
  artifact: ArtifactItem;
  taskId: string;
  className?: string;
}

function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function ArtifactCard({
  artifact,
  taskId,
  className = "",
}: ArtifactCardProps) {
  let typeLabel = "Document";
  let icon = "📄";
  let color = "bg-blue-500";

  switch (artifact.type) {
    case "docx":
      typeLabel = "Word Deliverable";
      icon = "📘";
      color = "bg-[#2b579a]";
      break;
    case "pptx":
      typeLabel = "PowerPoint Slides";
      icon = "📙";
      color = "bg-[#d24726]";
      break;
    case "xlsx":
      typeLabel = "Excel Spreadsheet";
      icon = "📗";
      color = "bg-[#217346]";
      break;
    case "code":
      typeLabel = "Python Script";
      icon = "💻";
      color = "bg-[#3572A5]";
      break;
    case "image":
      typeLabel = "Annotated Diagram";
      icon = "🖼️";
      color = "bg-[#9146FF]";
      break;
  }

  const handleDownload = (e: React.MouseEvent) => {
    e.stopPropagation();
    // In production/mock, trigger formatted content download
    const mockContent =
      artifact.type === "code"
        ? `# MRPL Air-Gapped Generated Script\n# Artifact: ${artifact.name}\n\nimport numpy as np\nprint("Harmonics validated on-premise.")\n`
        : `MRPL Sovereign Deliverable: ${artifact.name}\nGenerated on-premise without external network communication.\n\nSummary:\n${artifact.metadata?.summary || "Engineering assessment."}`;

    downloadArtifact(artifact.name, mockContent);
  };

  return (
    <div
      className={`p-4 rounded-2xl bg-surface border border-border hover:border-accent/40 shadow-xs hover:shadow-sm transition-all space-y-3 ${className}`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2.5">
          <span className="text-2xl">{icon}</span>
          <div>
            <h4 className="font-semibold text-xs text-text truncate max-w-[190px]" title={artifact.name}>
              {artifact.name}
            </h4>
            <div className="flex items-center gap-1.5 text-[10px] text-text-3 font-mono">
              <span>{typeLabel}</span>
              <span>·</span>
              <span>{formatSize(artifact.size_bytes)}</span>
            </div>
          </div>
        </div>
      </div>

      {artifact.metadata?.summary && (
        <p className="text-xs text-text-2 line-clamp-2 leading-relaxed">
          {artifact.metadata.summary}
        </p>
      )}

      <div className="flex items-center justify-between pt-1 border-t border-border-subtle">
        <ModelChip model={artifact.model_used} size="sm" />

        <div className="flex items-center gap-1.5">
          <Link
            href={`/task/${taskId}/artifact/${artifact.id}`}
            className="px-2.5 py-1 rounded-lg bg-surface-2 hover:bg-surface text-text text-[11px] font-medium border border-border transition-colors"
          >
            Open Viewer
          </Link>
          <button
            onClick={handleDownload}
            className="px-2.5 py-1 rounded-lg bg-accent text-white hover:bg-accent-hover text-[11px] font-semibold transition-colors shadow-2xs"
          >
            Download
          </button>
        </div>
      </div>
    </div>
  );
}
