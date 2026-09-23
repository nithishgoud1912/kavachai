"use client";

import { useState, useEffect, useCallback } from "react";
import { getModels, getRoutingRules, getLiveRoutingLogs, saveRoutingRule } from "@/app/services/api";
import type { ModelRegistryEntry, RoutingRule, RoutingDecisionLog } from "@/app/types";

export function useModels() {
  const [models, setModels] = useState<ModelRegistryEntry[]>([]);
  const [rules, setRules] = useState<RoutingRule[]>([]);
  const [logs, setLogs] = useState<RoutingDecisionLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const [m, r, l] = await Promise.all([
        getModels().catch(() => []),
        getRoutingRules().catch(() => []),
        getLiveRoutingLogs().catch(() => []),
      ]);
      setModels(m);
      setRules(r);
      setLogs(l);
    } catch (err: any) {
      setError(err.message || "Failed to load models");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 15000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const updateRule = async (rule: RoutingRule) => {
    try {
      const saved = await saveRoutingRule(rule);
      setRules((prev) => prev.map((r) => (r.id === saved.id ? saved : r)));
      return saved;
    } catch (err: any) {
      setError(err.message || "Failed to save rule");
      throw err;
    }
  };

  return { models, rules, logs, loading, error, reload: fetchData, updateRule };
}
