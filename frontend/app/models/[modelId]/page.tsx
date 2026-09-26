"use client";
import React, { use } from "react";
import Link from "next/link";
import AppShell from "@/app/components/AppShell";
import { useModels } from "@/app/hooks/useModels";
export default function ModelDetailPage({ params }: { params: Promise<{ modelId: string }> }) {
  const { modelId } = use(params);
  const { models, loading, error, reload } = useModels();
  const model = models.find(m => m.id === decodeURIComponent(modelId));
  return <AppShell title={`Model: ${decodeURIComponent(modelId)}`} subtitle="Observed local model registry" breadcrumbs={[{ label: "Models", href: "/models" }, { label: "Details" }]}>
    <div className="space-y-4 max-w-4xl mx-auto p-6 bg-surface border border-border rounded-xl">
      <button onClick={() => void reload()}>Refresh observed state</button>
      {loading && <p>Loading model registry…</p>}
      {error && <p role="alert">{error}</p>}
      {!loading && !error && !model && <p>This model is not present in the local registry.</p>}
      {!error && model && <><h2 className="font-bold">{model.name}</h2><p>Status: {model.status}</p>
        <p>Configured capabilities: {model.capabilities.join(", ") || "None assigned"}</p>
        <p>Quantization: {model.quantization || "Not reported"}</p>
        <p>Loaded context: {model.context_length > 0 ? `${model.context_length} tokens` : "Not reported"}</p>
        <p>Loaded VRAM: {model.status === "loaded" ? `${model.vram_usage_gb.toFixed(2)} GB` : "Model not loaded"}</p>
        <p>GPU capacity: not measured by this endpoint.</p><p>Endpoint: {model.endpoint}</p>
        <p>No inference benchmark has been run on this screen.</p>
        <Link className="text-accent underline" href="/workspace">Run a task and inspect its actual model selection and results</Link></>}
    </div>
  </AppShell>;
}
