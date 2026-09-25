"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import AppShell from "@/app/components/AppShell";
import Badge from "@/app/components/Badge";
import ModelChip from "@/app/components/ModelChip";
import { getTasks } from "@/app/services/api";
import type { WorkbenchTask } from "@/app/types";

export default function TasksHistoryPage() {
  const [tasks, setTasks] = useState<WorkbenchTask[]>([]);
  const [search, setSearch] = useState("");
  const [filterMode, setFilterMode] = useState<string>("all");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getTasks()
      .then(setTasks)
      .finally(() => setLoading(false));
  }, []);

  const filtered = tasks.filter((t) => {
    const matchesSearch = t.query.toLowerCase().includes(search.toLowerCase());
    const matchesMode = filterMode === "all" || t.mode === filterMode;
    return matchesSearch && matchesMode;
  });

  return (
    <AppShell
      title="Task History & Deliverables"
      subtitle="Searchable Audit Trail of Agentic Workflows"
      breadcrumbs={[
        { label: "Workspace", href: "/workspace" },
        { label: "Tasks" },
      ]}
    >
      <div className="space-y-6 max-w-7xl mx-auto pb-12">
        {/* Search & Filters */}
        <div className="flex flex-wrap items-center justify-between gap-3 p-4 bg-surface border border-border rounded-2xl shadow-xs">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search tasks by query, asset tag, or keyword..."
            className="flex-1 min-w-[240px] text-xs p-2.5 rounded-xl border border-border bg-bg-base focus:bg-surface focus:outline-none focus:ring-1 focus:ring-accent font-sans"
          />

          <div className="flex items-center gap-2 text-xs font-mono">
            <span className="text-text-3">Mode:</span>
            <select
              value={filterMode}
              onChange={(e) => setFilterMode(e.target.value)}
              className="bg-surface-2 border border-border px-2.5 py-1.5 rounded-xl text-text font-semibold focus:outline-none"
            >
              <option value="all">All Modes</option>
              <option value="auto">Auto-Route</option>
              <option value="code">Code / Script</option>
              <option value="vision">Vision / P&ID</option>
              <option value="document">Document</option>
            </select>
          </div>
        </div>

        {/* Tasks Table */}
        <div className="bg-surface border border-border rounded-2xl overflow-hidden shadow-xs p-5 space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-border-subtle">
            <h3 className="font-serif font-bold text-base text-text">Executed Tasks ({filtered.length})</h3>
            <span className="text-xs font-mono text-text-3">Stored On-Premise Local Audit Database</span>
          </div>

          {loading ? (
            <div className="p-8 text-center text-xs text-text-3">Loading task repository...</div>
          ) : filtered.length === 0 ? (
            <div className="p-8 text-center text-xs text-text-3 border border-dashed border-border rounded-xl">
              No tasks matched your search filter.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-sans border-collapse">
                <thead>
                  <tr className="border-b border-border text-text-3 font-mono text-[11px] uppercase">
                    <th className="pb-2.5">Task Description / Query</th>
                    <th className="pb-2.5">Mode</th>
                    <th className="pb-2.5">Assigned Model(s)</th>
                    <th className="pb-2.5">Deliverables</th>
                    <th className="pb-2.5">Status</th>
                    <th className="pb-2.5">Timestamp</th>
                    <th className="pb-2.5 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/60">
                  {filtered.map((t) => (
                    <tr key={t.id} className="hover:bg-bg-base/70 transition-colors">
                      <td className="py-3 pr-4 max-w-sm">
                        <Link
                          href={`/task/${t.id}`}
                          className="font-semibold text-text hover:text-accent line-clamp-1"
                        >
                          {t.query}
                        </Link>
                        <span className="text-[10px] text-text-3 font-mono">ID: {t.id}</span>
                      </td>
                      <td className="py-3 font-mono uppercase text-[11px] text-text-2">
                        {t.mode}
                      </td>
                      <td className="py-3">
                        <div className="flex flex-wrap gap-1">
                          {t.models_used && t.models_used.map((m, i) => (
                            <ModelChip key={i} model={m} size="sm" />
                          ))}
                        </div>
                      </td>
                      <td className="py-3 font-mono text-xs text-text-2">
                        {t.artifacts && t.artifacts.length > 0 ? (
                          <span className="px-2 py-0.5 rounded bg-surface-2 border border-border">
                            {t.artifacts.length} File{t.artifacts.length > 1 ? "s" : ""}
                          </span>
                        ) : (
                          <span className="text-text-3">None</span>
                        )}
                      </td>
                      <td className="py-3">
                        <Badge
                          variant={t.status === "complete" ? "complete" : t.status === "awaiting_review" ? "partial" : "running"}
                          label={t.status.toUpperCase()}
                          size="sm"
                        />
                      </td>
                      <td className="py-3 font-mono text-[11px] text-text-3">
                        {new Date(t.created_at).toLocaleDateString()} {new Date(t.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </td>
                      <td className="py-3 text-right">
                        <Link
                          href={`/task/${t.id}`}
                          className="px-3 py-1 rounded-lg bg-surface-2 hover:bg-surface border border-border text-[11px] text-text font-medium transition-colors"
                        >
                          Open Workspace →
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
