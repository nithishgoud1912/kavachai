"use client";

import { useState, useEffect, useCallback } from "react";
import { getNetworkStatus, getNetworkConnections, testEgressProbe } from "@/app/services/api";
import type { EgressReport, NetworkConnectionEntry } from "@/app/types";

export function useNetworkMonitor() {
  const [report, setReport] = useState<EgressReport | null>(null);
  const [connections, setConnections] = useState<NetworkConnectionEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [probing, setProbing] = useState(false);

  const fetchStatus = useCallback(async () => {
    try {
      const [r, c] = await Promise.all([
        getNetworkStatus().catch(() => null),
        getNetworkConnections().catch(() => []),
      ]);
      if (r) setReport(r);
      if (c && Array.isArray(c)) setConnections(c);
    } catch {
      // Keep previous state if temporary network drop
    } finally {
      setLoading(false);
    }
  }, []);

  const triggerProbe = useCallback(async () => {
    setProbing(true);
    try {
      const result = await testEgressProbe();
      await fetchStatus();
      return result;
    } catch (err) {
      await fetchStatus();
      throw err;
    } finally {
      setProbing(false);
    }
  }, [fetchStatus]);

  useEffect(() => {
    const initial = setTimeout(fetchStatus, 0);
    const interval = setInterval(fetchStatus, 4000);
    return () => { clearTimeout(initial); clearInterval(interval); };
  }, [fetchStatus]);

  return { report, connections, loading, probing, reload: fetchStatus, triggerProbe };
}
