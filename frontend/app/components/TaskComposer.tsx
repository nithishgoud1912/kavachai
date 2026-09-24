"use client";

import React, { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import { createTask } from "@/app/services/api";
import type { TaskMode, DeliverableType, AttachmentItem } from "@/app/types";
import TaskModeSelector from "./TaskModeSelector";
import AttachmentDropzone from "./AttachmentDropzone";

interface TaskComposerProps {
  initialQuery?: string;
  className?: string;
}

const DELIVERABLES: { id: DeliverableType; label: string; ext: string }[] = [
  { id: "word", label: "Word Doc", ext: ".docx" },
  { id: "ppt", label: "Slides", ext: ".pptx" },
  { id: "excel", label: "Spreadsheet", ext: ".xlsx" },
  { id: "code", label: "Python Script", ext: ".py" },
  { id: "chat", label: "Direct Answer", ext: "chat" },
];

export default function TaskComposer({
  initialQuery = "",
  className = "",
}: TaskComposerProps) {
  const router = useRouter();
  const [query, setQuery] = useState(initialQuery);
  const [mode, setMode] = useState<TaskMode>("auto");
  const [deliverableType, setDeliverableType] = useState<DeliverableType>("word");
  const [attachments, setAttachments] = useState<AttachmentItem[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!query.trim() || submitting) return;

    setSubmitting(true);
    setError(null);
    try {
      const task = await createTask(query.trim(), mode, deliverableType, attachments);
      router.push(`/task/${task.id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to initiate sovereign agentic task");
      setSubmitting(false);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className={`bg-surface border border-border rounded-2xl p-5 shadow-sm space-y-4 ${className}`}
    >
      <div className="space-y-2">
        <label className="block text-xs font-mono font-semibold uppercase tracking-wider text-text-3">
          Sovereign Agentic Task Composer
        </label>
        <textarea
          rows={3}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Draft an approval note from the scanned inspection report for P-204 crude feed pump, or calculate bearing vibration harmonics..."
          className="w-full rounded-xl border border-border bg-bg-base/50 p-3.5 text-sm text-text placeholder:text-text-3 focus:bg-surface focus:outline-none focus:ring-1 focus:ring-accent font-sans resize-none transition-colors"
        />
      </div>

      {/* Attachments Dropzone */}
      <AttachmentDropzone attachments={attachments} onChange={setAttachments} />

      {/* Selectors Bar: Mode & Deliverable */}
      <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-border-subtle">
        {/* Task Mode Chips */}
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-mono text-text-3 uppercase">Mode:</span>
          <TaskModeSelector selectedMode={mode} onChange={setMode} />
        </div>

        {/* Deliverable Type Picker */}
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-mono text-text-3 uppercase">Deliverable:</span>
          <div className="flex items-center gap-1 bg-surface-2 p-1 rounded-xl border border-border">
            {DELIVERABLES.map((del) => {
              const isSelected = deliverableType === del.id;
              return (
                <button
                  key={del.id}
                  type="button"
                  onClick={() => setDeliverableType(del.id)}
                  className={`px-2.5 py-0.5 rounded-lg text-xs font-medium transition-all ${
                    isSelected
                      ? "bg-surface text-accent shadow-xs font-semibold"
                      : "text-text-3 hover:text-text"
                  }`}
                >
                  {del.label}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {error && <p className="text-xs text-red font-medium">{error}</p>}

      {/* Submit Action */}
      <div className="flex items-center justify-between pt-1">
        <div className="flex items-center gap-2 text-[11px] text-text-3 font-mono">
          <span className="w-2 h-2 rounded-full bg-green" />
          <span>Local LLM Multi-Agent Auto-Routing Enabled</span>
        </div>

        <button
          type="submit"
          disabled={!query.trim() || submitting}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-semibold tracking-wide transition-all shadow-sm ${
            !query.trim() || submitting
              ? "bg-surface-2 text-text-3 cursor-not-allowed border border-border"
              : "bg-accent text-white hover:bg-accent-hover hover:shadow cursor-pointer"
          }`}
        >
          {submitting ? (
            <>
              <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              <span>Planning Agentic Workflow...</span>
            </>
          ) : (
            <>
              <span>Run Task</span>
              <span>→</span>
            </>
          )}
        </button>
      </div>
    </form>
  );
}
