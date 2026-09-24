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
      setReport(r);
      if (c) setConnections(c);
    } catch {
      setReport(null);
      setConnections([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const initial = setTimeout(fetchStatus, 0);
    const interval = setInterval(fetchStatus, 5000);
    return () => { clearTimeout(initial); clearInterval(interval); };
  }, [fetchStatus]);

  return { report, connections, loading, reload: fetchStatus };
}
