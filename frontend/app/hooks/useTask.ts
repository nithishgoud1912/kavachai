"use client";

import { useState, useEffect, useCallback } from "react";
import { getTask, submitTaskReview, sendTaskFollowUp } from "@/app/services/api";
import type { WorkbenchTask } from "@/app/types";

export function useTask(taskId: string | null) {
  const [task, setTask] = useState<WorkbenchTask | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTask = useCallback(async () => {
    if (!taskId) return;
    try {
      const data = await getTask(taskId);
      setTask(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load task");
    } finally {
      setLoading(false);
    }
  }, [taskId]);

  useEffect(() => {
    const timer = setTimeout(() => void fetchTask(), 0);
    return () => clearTimeout(timer);
  }, [fetchTask]);

  const reviewTask = async (action: "approve" | "revise" | "reject", comments?: string) => {
    if (!taskId) return;
    try {
      const updated = await submitTaskReview(taskId, action, comments, task?.version);
      setTask(updated);
      return updated;
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to submit review");
      throw err;
    }
  };

  const followUp = async (message: string) => {
    if (!taskId) return;
    try {
      const res = await sendTaskFollowUp(taskId, message);
      await fetchTask();
      return res;
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to send follow-up");
      throw err;
    }
  };

  return { task, setTask, loading, error, reload: fetchTask, reviewTask, followUp };
}
