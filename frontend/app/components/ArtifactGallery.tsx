"use client";

import React from "react";
import type { ArtifactItem } from "@/app/types";
import ArtifactCard from "./ArtifactCard";

interface ArtifactGalleryProps {
  artifacts: ArtifactItem[];
  taskId: string;
  className?: string;
}

export default function ArtifactGallery({
  artifacts,
  taskId,
  className = "",
}: ArtifactGalleryProps) {
  if (!artifacts || artifacts.length === 0) {
    return (
      <div className="p-6 rounded-2xl border border-dashed border-border text-center space-y-2">
        <span className="text-2xl opacity-60">📦</span>
        <p className="text-xs text-text-3">
          Agent deliverable synthesis in progress... Real files (Word/PPT/Excel/Code) will populate here.
        </p>
      </div>
    );
  }

  return (
    <div className={`space-y-3 ${className}`}>
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-mono font-semibold uppercase tracking-wider text-text-3">
          Generated Deliverable Artifacts ({artifacts.length})
        </h3>
        <span className="text-[11px] font-mono text-text-3">100% On-Premise Storage</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {artifacts.map((art) => (
          <ArtifactCard key={art.id} artifact={art} taskId={taskId} />
        ))}
      </div>
    </div>
  );
}
