"use client";

import React from "react";
import type { ModelRegistryEntry } from "@/app/types";
import Badge from "./Badge";

interface ModelRegistryTableProps {
  models: ModelRegistryEntry[];
  onSelectModel?: (model: ModelRegistryEntry) => void;
  className?: string;
}

export default function ModelRegistryTable({
  models,
  onSelectModel,
  className = "",
}: ModelRegistryTableProps) {
  return (
    <div className={`bg-surface border border-border rounded-2xl overflow-hidden shadow-xs space-y-3 p-5 ${className}`}>
      <div className="flex items-center justify-between pb-2 border-b border-border-subtle">
        <div>
          <h3 className="font-serif font-bold text-base text-text">On-Premise Model Registry</h3>
          <p className="text-xs text-text-3 font-mono">
            {models.length} Local Open-Weight Models Registered & Hosted On-Site
          </p>
        </div>
        <span className="px-2.5 py-1 rounded-full bg-green/10 text-green border border-green/20 text-xs font-mono font-medium">
          Zero Cloud Calls
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs font-sans border-collapse">
          <thead>
            <tr className="border-b border-border text-text-3 font-mono text-[11px] uppercase">
              <th className="pb-2.5">Model Identifier</th>
              <th className="pb-2.5">Capabilities</th>
              <th className="pb-2.5">Size / Quant</th>
              <th className="pb-2.5">Context</th>
              <th className="pb-2.5">VRAM Footprint</th>
              <th className="pb-2.5">Status</th>
              <th className="pb-2.5 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/60">
            {models.map((m) => (
              <tr key={m.id} className="hover:bg-bg-base/70 transition-colors">
                <td className="py-3 font-mono font-semibold text-text">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-accent" />
                    <span>{m.display_name || m.name}</span>
                  </div>
                  <span className="text-[10px] text-text-3 font-normal block pl-4">{m.id}</span>
                </td>
                <td className="py-3">
                  <div className="flex flex-wrap gap-1">
                    {m.capabilities.map((c) => (
                      <span
                        key={c}
                        className="px-2 py-0.5 rounded bg-surface-2 border border-border text-[10px] font-mono text-text-2 uppercase"
                      >
                        {c}
                      </span>
                    ))}
                  </div>
                </td>
                <td className="py-3 font-mono text-text-2">
                  {m.size} {m.quantization ? `(${m.quantization})` : ""}
                </td>
                <td className="py-3 font-mono text-text-2">
                  {(m.context_length / 1024).toFixed(0)}k tokens
                </td>
                <td className="py-3 font-mono text-text-2">
                  <div className="flex items-center gap-2">
                    <div className="w-16 h-1.5 rounded-full bg-surface-2 overflow-hidden">
                      <div
                        className="h-full bg-accent rounded-full"
                        style={{ width: `${(m.vram_usage_gb / m.max_vram_gb) * 100}%` }}
                      />
                    </div>
                    <span>{m.vram_usage_gb.toFixed(1)} GB</span>
                  </div>
                </td>
                <td className="py-3">
                  <Badge
                    variant={m.status === "loaded" ? "complete" : m.status === "warm" ? "partial" : "queued"}
                    label={m.status.toUpperCase()}
                    size="sm"
                  />
                </td>
                <td className="py-3 text-right">
                  <button
                    onClick={() => onSelectModel?.(m)}
                    className="px-2.5 py-1 rounded-lg bg-surface-2 hover:bg-surface border border-border text-[11px] text-text font-medium transition-colors cursor-pointer"
                  >
                    Inspect
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
