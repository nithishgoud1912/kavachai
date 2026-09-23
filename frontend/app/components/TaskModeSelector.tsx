"use client";

import React from "react";
import type { TaskMode } from "@/app/types";

interface TaskModeSelectorProps {
  selectedMode: TaskMode;
  onChange: (mode: TaskMode) => void;
  className?: string;
}

const MODES: { id: TaskMode; label: string; icon: string; description: string }[] = [
  { id: "auto", label: "Auto-Route", icon: "✨", description: "Model Router selects optimal local LLM" },
  { id: "document", label: "Document", icon: "📄", description: "Reports, SOPs & compliance synthesis" },
  { id: "code", label: "Code", icon: "💻", description: "Engineering math & sandbox execution" },
  { id: "vision", label: "Vision / P&ID", icon: "👁️", description: "P&ID topology & defect inspection" },
  { id: "spreadsheet", label: "Spreadsheet", icon: "📊", description: "Telemetry, formulas & financial tables" },
];

export default function TaskModeSelector({
  selectedMode,
  onChange,
  className = "",
}: TaskModeSelectorProps) {
  return (
    <div className={`flex flex-wrap items-center gap-1.5 ${className}`}>
      {MODES.map((m) => {
        const isSelected = selectedMode === m.id;
        return (
          <button
            key={m.id}
            type="button"
            onClick={() => onChange(m.id)}
            title={m.description}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium transition-all ${
              isSelected
                ? "bg-accent text-white shadow-xs"
                : "bg-surface-2 text-text-2 hover:bg-surface hover:text-text border border-border"
            }`}
          >
            <span>{m.icon}</span>
            <span>{m.label}</span>
          </button>
        );
      })}
    </div>
  );
}
