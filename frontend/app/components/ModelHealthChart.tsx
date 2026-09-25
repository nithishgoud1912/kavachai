"use client";
import type { ModelRegistryEntry } from "@/app/types";
export default function ModelHealthChart({ models, className = "" }: { models: ModelRegistryEntry[]; className?: string }) {
  const loaded = models.filter(m => m.status === "loaded");
  const cards = [
    ["Loaded models", String(loaded.length), "Reported by the local model service"],
    ["Model VRAM allocation", `${loaded.reduce((n, m) => n + (m.vram_usage_gb || 0), 0).toFixed(2)} GB`, "Model allocations only; device capacity not measured"],
    ["Deployment network verification", "Not measured", "Requires host and container packet capture"],
  ];
  return <div className={`grid grid-cols-1 sm:grid-cols-3 gap-4 ${className}`}>
    {cards.map(([label, value, detail]) => <div key={label} className="p-4 rounded-2xl bg-surface border border-border space-y-2">
      <p className="text-xs text-text-3">{label}</p><p className="text-xl font-semibold">{value}</p><p className="text-xs text-text-3">{detail}</p>
    </div>)}
  </div>;
}
