"use client";

import { useEffect, useState } from "react";
import { connectToTaskStream } from "@/app/services/sse";
import type { SubTaskItem, ToolCallEvent, ArtifactItem, EvidenceReference } from "@/app/types";

interface UseTaskStreamOptions {
  onTaskCompleted?: () => void;
  onHitlRequired?: () => void;
}

export function useTaskStream(taskId: string | null, options?: UseTaskStreamOptions) {
  const [plan, setPlan] = useState<SubTaskItem[]>([]);
  const [toolCalls, setToolCalls] = useState<ToolCallEvent[]>([]);
  const [reasoning, setReasoning] = useState<string>("");
  const [artifacts, setArtifacts] = useState<ArtifactItem[]>([]);
  const [citations, setCitations] = useState<EvidenceReference[]>([]);
  const [hitlPrompt, setHitlPrompt] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!taskId) return;

    setIsStreaming(true);
    setError(null);

    const conn = connectToTaskStream(taskId, {
      onPlanCreated: (newPlan) => {
        setPlan(newPlan);
      },
      onSubtaskStarted: ({ subtask_id, model }) => {
        setPlan((prev) =>
          prev.map((s) => (s.id === subtask_id ? { ...s, status: "running", assigned_model: model || s.assigned_model } : s))
        );
      },
      onSubtaskCompleted: ({ subtask_id, duration_ms }) => {
        setPlan((prev) =>
          prev.map((s) => (s.id === subtask_id ? { ...s, status: "done", duration_ms } : s))
        );
      },
      onSubtaskFailed: ({ subtask_id, error: err }) => {
        setPlan((prev) =>
          prev.map((s) => (s.id === subtask_id ? { ...s, status: "failed", error: err } : s))
        );
      },
      onToolCallStarted: (tc) => {
        setToolCalls((prev) => {
          const idx = prev.findIndex((p) => p.id === tc.id);
          if (idx >= 0) {
            const copy = [...prev];
            copy[idx] = tc;
            return copy;
          }
          return [...prev, tc];
        });
      },
      onToolCallResult: (tc) => {
        setToolCalls((prev) => {
          const idx = prev.findIndex((p) => p.id === tc.id);
          if (idx >= 0) {
            const copy = [...prev];
            copy[idx] = tc;
            return copy;
          }
          return [...prev, tc];
        });
      },
      onOutputDelta: (delta) => {
        setReasoning((prev) => prev + delta);
      },
      onArtifactCreated: (art) => {
        setArtifacts((prev) => {
          if (prev.some((p) => p.id === art.id)) return prev;
          return [...prev, art];
        });
      },
      onCitationAdded: (cit) => {
        setCitations((prev) => {
          if (prev.some((c) => c.source_id === cit.source_id)) return prev;
          return [...prev, cit];
        });
      },
      onHitlRequired: (data) => {
        setHitlPrompt(data.prompt || "Human review requested");
        options?.onHitlRequired?.();
      },
      onTaskCompleted: () => {
        setIsStreaming(false);
        options?.onTaskCompleted?.();
      },
      onTaskFailed: ({ error: err }) => {
        setIsStreaming(false);
        setError(err);
      },
      onError: () => {
        setIsStreaming(false);
      },
    });

    return () => {
      conn.close();
    };
  }, [taskId]);

  return {
    plan,
    toolCalls,
    reasoning,
    artifacts,
    citations,
    hitlPrompt,
    isStreaming,
    error,
  };
}
