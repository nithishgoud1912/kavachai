"use client";

import React from "react";
import Link from "next/link";

interface SandboxResultPreviewProps {
  exitCode: number;
  stdout: string;
  stderr?: string;
  durationMs: number;
  memoryMb?: number;
  className?: string;
}

export default function SandboxResultPreview({
  exitCode,
  stdout,
  stderr,
  durationMs,
  memoryMb,
  className = "",
}: SandboxResultPreviewProps) {
  const isSuccess = exitCode === 0;

  return (
    <div
      className={`rounded-xl border p-3 font-mono text-[11px] space-y-1.5 ${
        isSuccess
          ? "bg-[#E9F0EC]/40 border-[#2D794D]/25"
          : "bg-[#F2E6E3]/40 border-[#B83838]/25"
      } ${className}`}
    >
      <div className="flex items-center justify-between text-text-3 pb-1 border-b border-border/50">
        <div className="flex items-center gap-2">
          <span
            className={`w-2 h-2 rounded-full ${isSuccess ? "bg-green" : "bg-red"}`}
          />
          <span className="font-semibold text-text">
            {isSuccess ? "Exit Code 0 (Success)" : `Exit Code ${exitCode} (Failed)`}
          </span>
          <span className="text-[10px]">· {durationMs}ms</span>
          {memoryMb && <span className="text-[10px]">· {memoryMb}MB RAM</span>}
        </div>
        <Link
          href="/sandbox"
          className="text-accent hover:underline text-[10px] font-sans font-medium"
        >
          Open in Sandbox Console →
        </Link>
      </div>

      <pre className="text-text whitespace-pre-wrap max-h-32 overflow-y-auto leading-relaxed">
        {stdout || stderr || "Execution finished with empty output."}
      </pre>
    </div>
  );
}
