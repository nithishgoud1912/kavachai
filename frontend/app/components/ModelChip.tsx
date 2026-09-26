"use client";

import React from "react";
import { getModelDisplayName } from "@/app/utils/modelNames";

interface ModelChipProps {
  model: string;
  taskType?: string;
  size?: "sm" | "md";
  className?: string;
}

export default function ModelChip({
  model,
  taskType,
  size = "md",
  className = "",
}: ModelChipProps) {
  const displayName = getModelDisplayName(model);
  // Extract icon based on taskType, model name or displayName
  const lower = (model + " " + displayName + " " + (taskType || "")).toLowerCase();
  let icon = "⚡";
  let role = "reasoning";

  if (lower.includes("vision") || lower.includes("vl") || lower.includes("image") || lower.includes("pid")) {
    icon = "👁️";
    role = "vision";
  } else if (lower.includes("code") || lower.includes("coder") || lower.includes("sandbox") || lower.includes("python")) {
    icon = "💻";
    role = "code";
  } else if (lower.includes("embed") || lower.includes("nomic")) {
    icon = "🔍";
    role = "embedding";
  } else if (lower.includes("ocr") || lower.includes("document") || lower.includes("tesseract")) {
    icon = "📄";
    role = "OCR";
  }

  const isSm = size === "sm";

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-mono rounded-md border border-border bg-surface-2 text-text font-medium ${
        isSm ? "px-2 py-0.5 text-[11px]" : "px-2.5 py-1 text-xs"
      } ${className}`}
      title={`Served locally via on-premise Ollama runtime (${model})`}
    >
      <span className="text-xs">{icon}</span>
      <span className="font-semibold text-text">{displayName}</span>
      {taskType && (
        <>
          <span className="text-text-3 font-normal">·</span>
          <span className="text-text-2 font-sans capitalize">{taskType.replace(/_/g, " ")}</span>
        </>
      )}
    </span>
  );
}
