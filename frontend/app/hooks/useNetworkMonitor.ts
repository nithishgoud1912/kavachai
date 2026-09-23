"use client";

import { useState, useEffect, useCallback } from "react";
import { getNetworkStatus, getNetworkConnections } from "@/app/services/api";
import type { EgressReport, NetworkConnectionEntry } from "@/app/types";

export function useNetworkMonitor() {
  const [report, setReport] = useState<EgressReport | null>(null);
  const [connections, setConnections] = useState<NetworkConnectionEntry[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchStatus = useCallback(async () => {
    try {
      const [r, c] = await Promise.all([
        getNetworkStatus().catch(() => null),
        getNetworkConnections().catch(() => []),
      ]);
      if (r) setReport(r);
      if (c) setConnections(c);
    } catch {
      // Keep existing state
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  return { report, connections, loading, reload: fetchStatus };
}
