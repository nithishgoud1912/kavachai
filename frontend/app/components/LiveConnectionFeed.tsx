"use client";

import React from "react";
import type { NetworkConnectionEntry } from "@/app/types";
import Badge from "./Badge";

interface LiveConnectionFeedProps {
  connections: NetworkConnectionEntry[];
  className?: string;
}

export default function LiveConnectionFeed({
  connections,
  className = "",
}: LiveConnectionFeedProps) {
  return (
    <div className={`bg-surface border border-border rounded-2xl overflow-hidden shadow-xs space-y-3 p-5 ${className}`}>
      <div className="flex items-center justify-between pb-2 border-b border-border-subtle">
        <div>
          <h3 className="font-serif font-bold text-base text-text">Real-Time Socket Egress Audit Feed</h3>
          <p className="text-xs text-text-3 font-mono">
            Intercepted at socket.getaddrinfo DNS and TCP loopback layer
          </p>
        </div>
        <span className="text-xs font-mono text-text-3 flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-green" />
          <span>Active Kernel Monitor</span>
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs font-mono border-collapse">
          <thead>
            <tr className="border-b border-border text-text-3 text-[11px] uppercase">
              <th className="pb-2.5">Timestamp</th>
              <th className="pb-2.5">Destination Host & Port</th>
              <th className="pb-2.5">Process / Service</th>
              <th className="pb-2.5">Method</th>
              <th className="pb-2.5">Latency</th>
              <th className="pb-2.5 text-right">Air-Gap Policy</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/60">
            {connections.map((c) => (
              <tr key={c.id} className="hover:bg-bg-base/70 transition-colors">
                <td className="py-2.5 text-text-3">
                  {new Date(c.timestamp).toLocaleTimeString()}
                </td>
                <td className="py-2.5 font-bold text-text">{c.destination}</td>
                <td className="py-2.5 text-text-2 font-sans font-medium">{c.service}</td>
                <td className="py-2.5 text-text-3">{c.method}</td>
                <td className="py-2.5 text-text-3">{c.latency_ms}ms</td>
                <td className="py-2.5 text-right">
                  <Badge
                    variant={c.status === "allowed" ? "complete" : "failed"}
                    label={c.status === "allowed" ? "LOCAL_LOOPBACK" : "BLOCKED"}
                    size="sm"
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
