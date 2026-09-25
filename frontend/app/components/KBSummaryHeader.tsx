"use client";

import React from "react";
import SovereignBadge from "./SovereignBadge";

interface KBSummaryHeaderProps {
  totalDocs?: number;
  totalChunks?: number;
  totalPid?: number;
  storageMb?: number;
  className?: string;
}

export default function KBSummaryHeader({
  totalDocs = 18,
  totalChunks = 1240,
  totalPid = 6,
  storageMb = 142.5,
  className = "",
}: KBSummaryHeaderProps) {
  return (
    <div className={`p-6 bg-surface border border-border rounded-2xl shadow-xs space-y-4 ${className}`}>
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border-subtle pb-3">
        <div>
          <h2 className="font-serif text-xl font-bold text-text">MRPL Industrial Knowledge Base</h2>
          <p className="text-xs text-text-3 font-mono">
            Confidential Standard Operating Procedures, P&ID Topologies, and Equipment Manuals
          </p>
        </div>
        <SovereignBadge size="sm" showSubtitle={true} />
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-1">
        <div className="space-y-1">
          <p className="text-[11px] font-mono uppercase text-text-3">Ingested Documents</p>
          <p className="text-2xl font-serif font-bold text-text">{totalDocs}</p>
          <p className="text-[10px] text-green font-mono">Ready document records</p>
        </div>

        <div className="space-y-1">
          <p className="text-[11px] font-mono uppercase text-text-3">Text & Vector Chunks</p>
          <p className="text-2xl font-serif font-bold text-accent">{totalChunks.toLocaleString()}</p>
          <p className="text-[10px] text-text-3 font-mono">Nomic Embed 768-dim</p>
        </div>

        <div className="space-y-1">
          <p className="text-[11px] font-mono uppercase text-text-3">P&ID Engineering Drawings</p>
          <p className="text-2xl font-serif font-bold text-text">{totalPid}</p>
          <p className="text-[10px] text-accent font-mono">Topological Graph Linked</p>
        </div>

        <div className="space-y-1">
          <p className="text-[11px] font-mono uppercase text-text-3">Local Storage Footprint</p>
          <p className="text-2xl font-serif font-bold text-text">{storageMb.toFixed(1)} MB</p>
          <p className="text-[10px] text-text-3 font-mono">Encrypted At Rest</p>
        </div>
      </div>
    </div>
  );
}
