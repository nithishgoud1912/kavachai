"use client";

import { useState, useEffect, useCallback } from "react";
import type { KnowledgeBaseSummary } from "@/app/types";
import { getKnowledgeBaseSummary } from "@/app/services/api";

interface KnowledgeBaseState {
  summary: KnowledgeBaseSummary | null;
  loading: boolean;
  error: string | null;
  refresh: () => void;
}

export function useKnowledgeBase(): KnowledgeBaseState {
  const [summary, setSummary] = useState<KnowledgeBaseSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSummary = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getKnowledgeBaseSummary();
      setSummary(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load knowledge base");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSummary();
  }, [fetchSummary]);

  return { summary, loading, error, refresh: fetchSummary };
}
