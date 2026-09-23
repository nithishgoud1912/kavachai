"use client";

import React, { use, useState } from "react";
import AppShell from "@/app/components/AppShell";
import Badge from "@/app/components/Badge";
import SovereignBadge from "@/app/components/SovereignBadge";

export default function ModelDetailPage({
  params,
}: {
  params: Promise<{ modelId: string }>;
}) {
  const { modelId } = use(params);
  const [testPrompt, setTestPrompt] = useState("Summarize crude oil distillation temperature ranges.");
  const [testResponse, setTestResponse] = useState<string | null>(null);
  const [testing, setTesting] = useState(false);

  const handleTestInference = () => {
    setTesting(true);
    setTimeout(() => {
      setTestResponse(
        `[Local Inference Response from ${modelId}]\nIn crude distillation units (CDU), atmospheric distillation separates crude into fractions based on boiling points:\n- Light Naphtha: < 90°C\n- Heavy Naphtha: 90°C - 160°C\n- Kerosene / Jet Fuel: 160°C - 240°C\n- Diesel / Gas Oil: 240°C - 360°C\n- Atmospheric Residue: > 360°C\n\nLatency: 118ms · Generated completely on-premise without external API egress.`
      );
      setTesting(false);
    }, 850);
  };

  return (
    <AppShell
      title={`Model: ${modelId}`}
      subtitle="Local Inference & Health"
      breadcrumbs={[
        { label: "Workspace", href: "/workspace" },
        { label: "Model Router", href: "/models" },
        { label: modelId },
      ]}
    >
      <div className="space-y-6 max-w-4xl mx-auto pb-12">
        {/* Model Spec Card */}
        <div className="p-6 bg-surface border border-border rounded-2xl shadow-xs space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <span className="text-3xl">🔀</span>
              <div>
                <h2 className="font-serif text-lg font-bold text-text">{modelId}</h2>
                <p className="text-xs font-mono text-text-3">On-Premise Ollama / vLLM Engine</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <SovereignBadge size="sm" />
              <Badge variant="complete" label="STATUS: WARM / LOADED" />
            </div>
          </div>

          <div className="pt-2 border-t border-border-subtle grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-mono">
            <div>
              <span className="text-text-3 block text-[10px] uppercase">Quantization</span>
              <span className="text-text font-semibold">Q4_K_M (Fast INT4)</span>
            </div>
            <div>
              <span className="text-text-3 block text-[10px] uppercase">Context Window</span>
              <span className="text-text font-semibold">32,768 tokens</span>
            </div>
            <div>
              <span className="text-text-3 block text-[10px] uppercase">VRAM In Use</span>
              <span className="text-accent font-semibold">2.2 GB / 24 GB</span>
            </div>
            <div>
              <span className="text-text-3 block text-[10px] uppercase">Endpoint</span>
              <span className="text-green font-semibold">127.0.0.1:11434</span>
            </div>
          </div>
        </div>

        {/* Isolation Test Box */}
        <div className="p-6 bg-surface border border-border rounded-2xl shadow-xs space-y-4">
          <div>
            <h3 className="font-serif font-bold text-sm text-text">
              Direct Model Verification Sandbox
            </h3>
            <p className="text-xs text-text-3 font-mono">
              Execute test prompts directly against this specific model weight in isolation
            </p>
          </div>

          <div className="space-y-2">
            <textarea
              rows={3}
              value={testPrompt}
              onChange={(e) => setTestPrompt(e.target.value)}
              className="w-full text-xs font-mono p-3 rounded-xl border border-border bg-bg-base focus:bg-surface focus:outline-none focus:ring-1 focus:ring-accent"
            />
            <div className="flex justify-end">
              <button
                onClick={handleTestInference}
                disabled={testing}
                className="px-4 py-2 rounded-xl bg-accent text-white hover:bg-accent-hover text-xs font-semibold shadow-xs transition-colors cursor-pointer"
              >
                {testing ? "Running Local Inference..." : "Test Local Inference"}
              </button>
            </div>
          </div>

          {testResponse && (
            <div className="p-4 rounded-xl bg-bg-base border border-border space-y-1 font-mono text-xs">
              <span className="text-[10px] uppercase font-bold text-text-3">Raw Output Stream:</span>
              <pre className="text-text whitespace-pre-wrap leading-relaxed">
                {testResponse}
              </pre>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
