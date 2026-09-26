"use client";

import React, { useState, useMemo } from "react";
import type { NetworkConnectionEntry } from "@/app/types";
import Badge from "./Badge";

interface LiveConnectionFeedProps {
  connections: NetworkConnectionEntry[];
  className?: string;
}

export default function LiveConnectionFeed({
  connections = [],
  className = "",
}: LiveConnectionFeedProps) {
  const [filter, setFilter] = useState<"all" | "allowed" | "blocked">("all");
  const [search, setSearch] = useState("");

  const allowedCount = useMemo(() => connections.filter((c) => c.status === "allowed").length, [connections]);
  const blockedCount = useMemo(() => connections.filter((c) => c.status === "blocked").length, [connections]);

  const filteredConnections = useMemo(() => {
    return connections
      .filter((c) => {
        if (filter === "allowed") return c.status === "allowed";
        if (filter === "blocked") return c.status === "blocked";
        return true;
      })
      .filter((c) => {
        if (!search.trim()) return true;
        const q = search.toLowerCase();
        return (
          c.destination.toLowerCase().includes(q) ||
          String(c.port).includes(q) ||
          c.service.toLowerCase().includes(q) ||
          c.method.toLowerCase().includes(q)
        );
      });
  }, [connections, filter, search]);

  return (
    <div className={`bg-surface border border-border rounded-2xl overflow-hidden shadow-xs space-y-4 p-5 ${className}`}>
      {/* ─── Header & Controls ─── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-border-subtle gap-3">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="font-serif font-bold text-base text-text">Real-Time Socket Egress Audit Feed</h3>
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-green" />
            </span>
          </div>
          <p className="text-xs text-text-3 font-mono">
            Intercepted at socket.getaddrinfo DNS and TCP loopback layer
          </p>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          {/* Status Filter Tabs */}
          <div className="inline-flex rounded-lg border border-border bg-bg-base/70 p-0.5 text-xs font-mono">
            <button
              onClick={() => setFilter("all")}
              className={`px-2.5 py-1 rounded-md transition-colors ${
                filter === "all" ? "bg-surface text-text font-bold shadow-xs" : "text-text-3 hover:text-text"
              }`}
            >
              All ({connections.length})
            </button>
            <button
              onClick={() => setFilter("allowed")}
              className={`px-2.5 py-1 rounded-md transition-colors ${
                filter === "allowed" ? "bg-surface text-green font-bold shadow-xs" : "text-text-3 hover:text-green"
              }`}
            >
              Allowed ({allowedCount})
            </button>
            <button
              onClick={() => setFilter("blocked")}
              className={`px-2.5 py-1 rounded-md transition-colors ${
                filter === "blocked" ? "bg-surface text-red font-bold shadow-xs" : "text-text-3 hover:text-red"
              }`}
            >
              Blocked ({blockedCount})
            </button>
          </div>
        </div>
      </div>

      {/* ─── Search Bar ─── */}
      <div className="relative">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Filter by host, port, method or service..."
          className="w-full text-xs font-mono bg-bg-base/70 border border-border rounded-xl px-3.5 py-2 text-text placeholder:text-text-3 focus:outline-none focus:border-accent"
        />
        {search && (
          <button
            onClick={() => setSearch("")}
            className="absolute right-3 top-2.5 text-text-3 hover:text-text text-xs"
          >
            ✕
          </button>
        )}
      </div>

      {/* ─── Table ─── */}
      <div className="overflow-x-auto max-h-[380px] overflow-y-auto">
        <table className="w-full text-left text-xs font-mono border-collapse">
          <thead className="sticky top-0 bg-surface z-10">
            <tr className="border-b border-border text-text-3 text-[11px] uppercase tracking-wider">
              <th className="pb-2.5">Timestamp</th>
              <th className="pb-2.5">Destination Host & Port</th>
              <th className="pb-2.5">Process / Service</th>
              <th className="pb-2.5">Method</th>
              <th className="pb-2.5">Latency</th>
              <th className="pb-2.5 text-right">Air-Gap Policy</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/60">
            {filteredConnections.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-8 text-center text-xs text-text-3 space-y-1">
                  <p className="font-semibold text-text-2">
                    {connections.length === 0
                      ? "Listening for socket events..."
                      : "No socket connections match current filter."}
                  </p>
                  <p className="text-[11px]">
                    All system communication is strictly confined to local loopback addresses.
                  </p>
                </td>
              </tr>
            ) : (
              filteredConnections.map((c) => (
                <tr
                  key={c.id}
                  className={`transition-colors ${
                    c.status === "blocked"
                      ? "bg-red/10 hover:bg-red/15"
                      : "hover:bg-bg-base/70"
                  }`}
                >
                  <td className="py-2.5 text-text-3 whitespace-nowrap">
                    {new Date(c.timestamp).toLocaleTimeString()}
                  </td>
                  <td className="py-2.5 font-bold text-text whitespace-nowrap">
                    {c.destination}
                    {c.port ? `:${c.port}` : ""}
                  </td>
                  <td className="py-2.5 text-text-2 font-sans font-medium text-xs">
                    {c.service || (c.port === 11434 ? "Ollama Inference Runtime" : "FastAPI Backend")}
                  </td>
                  <td className="py-2.5 text-text-3 whitespace-nowrap">{c.method}</td>
                  <td className="py-2.5 text-text-3 whitespace-nowrap">{c.latency_ms ?? 0.1}ms</td>
                  <td className="py-2.5 text-right whitespace-nowrap">
                    <Badge
                      variant={c.status === "allowed" ? "complete" : "failed"}
                      label={c.status === "allowed" ? "LOCAL_LOOPBACK" : "BLOCKED"}
                      size="sm"
                    />
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* ─── Footer Stats ─── */}
      <div className="flex items-center justify-between text-[11px] font-mono text-text-3 pt-2 border-t border-border-subtle">
        <span>Showing {filteredConnections.length} of {connections.length} socket events</span>
        <span className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-green" />
          <span>Continuous audit hook active</span>
        </span>
      </div>
    </div>
  );
}
