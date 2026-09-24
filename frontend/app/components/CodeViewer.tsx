"use client";

import React, { useState, useEffect } from "react";
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

  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    fetch(artifact.download_url, { credentials: "include", cache: "no-store" }).then(async response => {
      if (!response.ok) throw new Error("Artifact unavailable");
      const text = await response.text();
      if (active) setCode(text);
    }).catch(error => { if (active) setError(String(error)); });
    return () => { active = false; };
  }, [artifact.download_url]);

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
      {error && <p role="alert">{error}</p>}
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
