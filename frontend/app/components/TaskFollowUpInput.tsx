"use client";

import React, { useState, FormEvent } from "react";

interface TaskFollowUpInputProps {
  onSend: (message: string) => Promise<void>;
  disabled?: boolean;
  className?: string;
}

export default function TaskFollowUpInput({
  onSend,
  disabled = false,
  className = "",
}: TaskFollowUpInputProps) {
  const [input, setInput] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!input.trim() || submitting || disabled) return;

    setSubmitting(true);
    try {
      await onSend(input.trim());
      setInput("");
    } catch {
      // Handled in parent
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className={`p-3 bg-surface border border-border rounded-xl shadow-xs flex items-center gap-2 ${className}`}
    >
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Ask a grounded follow-up question in this task context..."
        disabled={disabled || submitting}
        className="flex-1 bg-transparent text-xs text-text placeholder:text-text-3 focus:outline-none px-2"
      />
      <button
        type="submit"
        disabled={!input.trim() || submitting || disabled}
        className="px-3.5 py-1.5 rounded-lg bg-accent text-white text-xs font-semibold hover:bg-accent-hover disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-xs"
      >
        {submitting ? "Evaluating..." : "Send"}
      </button>
    </form>
  );
}
