"use client";

import React from "react";
import type { ModelRegistryEntry } from "@/app/types";

interface ModelHealthChartProps {
  models: ModelRegistryEntry[];
  className?: string;
}

export default function ModelHealthChart({ models, className = "" }: ModelHealthChartProps) {
  return (
    <div className={`grid grid-cols-1 sm:grid-cols-3 gap-4 ${className}`}>
      <div className="p-4 rounded-2xl bg-surface border border-border shadow-xs space-y-2">
        <span className="text-[11px] font-mono uppercase text-text-3 font-semibold">
          Avg Inference Latency
        </span>
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-serif font-bold text-text">145ms</span>
          <span className="text-xs text-green font-mono">P95 on RTX 4090 / L40</span>
        </div>
        <div className="w-full bg-surface-2 h-1.5 rounded-full overflow-hidden">
          <div className="bg-green h-full w-[24%]" />
        </div>
      </div>

      <div className="p-4 rounded-2xl bg-surface border border-border shadow-xs space-y-2">
        <span className="text-[11px] font-mono uppercase text-text-3 font-semibold">
          Total VRAM Utilization
        </span>
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-serif font-bold text-text">7.5 / 24.0 GB</span>
          <span className="text-xs text-accent font-mono">31% Warm</span>
        </div>
        <div className="w-full bg-surface-2 h-1.5 rounded-full overflow-hidden">
          <div className="bg-accent h-full w-[31%]" />
        </div>
      </div>

      <div className="p-4 rounded-2xl bg-surface border border-border shadow-xs space-y-2">
        <span className="text-[11px] font-mono uppercase text-text-3 font-semibold">
          Air-Gap Sovereign Egress
        </span>
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-serif font-bold text-green">0.00 KB/s</span>
          <span className="text-xs text-green font-mono">Zero Leaks</span>
        </div>
        <div className="w-full bg-surface-2 h-1.5 rounded-full overflow-hidden">
          <div className="bg-green h-full w-full" />
        </div>
      </div>
    </div>
  );
}
