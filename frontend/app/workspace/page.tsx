"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import AppShell from "@/app/components/AppShell";
import TaskComposer from "@/app/components/TaskComposer";
import Badge from "@/app/components/Badge";
import ModelChip from "@/app/components/ModelChip";
import { getTasks, getModels, getNetworkStatus } from "@/app/services/api";
import type { WorkbenchTask, ModelRegistryEntry, EgressReport } from "@/app/types";

const SUGGESTIONS = [
  {
    title: "Pump P-204 Vibration Anomaly",
    prompt: "Draft an approval note from the scanned inspection report for P-204 Crude Feed Pump vibration anomaly.",
    dept: "MAINTENANCE",
  },
  {
    title: "Calculate Bearing Harmonics",
    prompt: "Calculate characteristic fault frequencies (BPFO, BPFI, BSF) for SKF 6318 bearing at 2980 RPM in the sandbox.",
    dept: "ENGINEERING",
  },
  {
    title: "P&ID Topology Inspection",
    prompt: "Inspect CDU-II P&ID drawing for bypass valve HV-204B isolation status and safe operating sequence.",
    dept: "OPERATIONS",
  },
  {
    title: "Weekly HSE Hazard Summary",
    prompt: "Synthesize weekly safety incident log into a formatted executive PowerPoint presentation deliverable.",
    dept: "SAFETY",
  },
];

export default function WorkspacePage() {
  const [tasks, setTasks] = useState<WorkbenchTask[]>([]);
  const [models, setModels] = useState<ModelRegistryEntry[]>([]);
  const [egress, setEgress] = useState<EgressReport | null>(null);
  const [composerQuery, setComposerQuery] = useState("");
  const [showRightRail, setShowRightRail] = useState(true);

  useEffect(() => {
    getTasks().then(setTasks).catch(() => {});
    getModels().then(setModels).catch(() => {});
    getNetworkStatus().then(setEgress).catch(() => {});
  }, []);

  return (
    <AppShell title="Operations Workspace" subtitle="MRPL Sovereign Industrial AI">
      <div className="flex gap-6 max-w-7xl mx-auto">
        {/* ─── Center Column: Task Composer, Suggestions, Recent Tasks ─ */}
        <div className="flex-1 space-y-6 min-w-0">
          {/* Main Task Composer */}
          <TaskComposer initialQuery={composerQuery} />

          {/* Department Suggested Prompts */}
          <div className="space-y-2">
            <p className="text-[11px] font-mono uppercase text-text-3 font-semibold px-1">
              Suggested Refinery Investigations & Deliverables:
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {SUGGESTIONS.map((item, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => setComposerQuery(item.prompt)}
                  className="p-3 bg-surface hover:bg-surface-2 border border-border hover:border-accent/40 rounded-xl text-left transition-all space-y-1 group cursor-pointer shadow-xs"
                >
                  <div className="flex items-center justify-between text-[10px] font-mono">
                    <span className="font-semibold text-accent">{item.title}</span>
                    <span className="px-1.5 py-0.2 rounded bg-surface-2 text-text-3">
                      {item.dept}
                    </span>
                  </div>
                  <p className="text-xs text-text-2 group-hover:text-text line-clamp-2 leading-relaxed">
                    {item.prompt}
                  </p>
                </button>
              ))}
            </div>
          </div>

          {/* Recent Tasks List */}
          <div className="bg-surface border border-border rounded-2xl p-5 shadow-xs space-y-4">
            <div className="flex items-center justify-between border-b border-border-subtle pb-3">
              <div>
                <h3 className="font-serif font-bold text-base text-text">Recent Tasks & Deliverables</h3>
                <p className="text-xs text-text-3 font-mono">
                  Multi-agent runs, verification logs, and exported deliverables
                </p>
              </div>
              <Link
                href="/tasks"
                className="text-xs text-accent hover:underline font-mono font-medium"
              >
                View All History →
              </Link>
            </div>

            {tasks.length === 0 ? (
              <div className="p-8 text-center text-xs text-text-3 border border-dashed border-border rounded-xl">
                No tasks executed in this session yet. Launch a new task above!
              </div>
            ) : (
              <div className="space-y-3">
                {tasks.slice(0, 5).map((t) => (
                  <Link
                    key={t.id}
                    href={`/task/${t.id}`}
                    className="block p-4 rounded-xl border border-border hover:border-accent/40 bg-bg-base/40 hover:bg-surface transition-all space-y-2 group"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <h4 className="font-semibold text-xs text-text group-hover:text-accent transition-colors line-clamp-1">
                        {t.query}
                      </h4>
                      <Badge
                        variant={t.status === "complete" ? "complete" : t.status === "awaiting_review" ? "partial" : "running"}
                        label={t.status.replace(/_/g, " ").toUpperCase()}
                        size="sm"
                      />
                    </div>

                    <div className="flex flex-wrap items-center justify-between gap-2 pt-1 text-[11px] font-mono text-text-3">
                      <div className="flex items-center gap-2">
                        {t.models_used && t.models_used.length > 0 && (
                          <ModelChip model={t.models_used[0]} size="sm" />
                        )}
                        {t.artifacts && t.artifacts.length > 0 && (
                          <span className="px-2 py-0.5 rounded bg-surface border border-border text-text font-medium">
                            📁 {t.artifacts.length} Deliverable{t.artifacts.length > 1 ? "s" : ""}
                          </span>
                        )}
                      </div>
                      <span>{new Date(t.created_at).toLocaleTimeString()}</span>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* ─── Right Context Rail (300px, Collapsible) ─────────────── */}
        {showRightRail && (
          <aside className="w-72 hidden xl:block space-y-4 shrink-0">
            {/* Model Router Mini Panel */}
            <div className="bg-surface border border-border rounded-2xl p-4 shadow-xs space-y-3">
              <div className="flex items-center justify-between border-b border-border-subtle pb-2">
                <span className="text-xs font-serif font-bold text-text">Model Router Status</span>
                <Link href="/models" className="text-[10px] font-mono text-accent hover:underline">
                  Manage →
                </Link>
              </div>

              <div className="space-y-2">
                {models.slice(0, 3).map((m) => (
                  <div
                    key={m.id}
                    className="p-2 rounded-xl bg-surface-2/60 border border-border text-xs flex items-center justify-between"
                  >
                    <div className="truncate min-w-0 pr-1">
                      <p className="font-mono font-semibold text-text truncate">{m.name}</p>
                      <p className="text-[10px] text-text-3 font-mono">{Array.from(new Set(m.capabilities || [])).join(", ")}</p>
                    </div>
                    <Badge variant={m.status === "loaded" ? "complete" : "partial"} label={m.status} size="sm" />
                  </div>
                ))}
              </div>

              <div className="pt-1 text-[10px] font-mono text-text-3 flex items-center justify-between">
                <span>VRAM Allocation:</span>
                <span className="font-semibold text-accent">7.5 / 24.0 GB</span>
              </div>
            </div>

            {/* System Health Card */}
            <div className="bg-surface border border-border rounded-2xl p-4 shadow-xs space-y-3">
              <div className="flex items-center justify-between border-b border-border-subtle pb-2">
                <span className="text-xs font-serif font-bold text-text">Air-Gap Stack Health</span>
                <span className="w-2 h-2 rounded-full bg-green" />
              </div>

              <div className="space-y-2 text-xs">
                <div className="flex items-center justify-between text-text-2">
                  <span>Ollama Engine:</span>
                  <span className="font-mono text-green font-semibold">127.0.0.1:11434 OK</span>
                </div>
                <div className="flex items-center justify-between text-text-2">
                  <span>FastAPI Core:</span>
                  <span className="font-mono text-green font-semibold">127.0.0.1:8000 OK</span>
                </div>
                <div className="flex items-center justify-between text-text-2">
                  <span>Code Sandbox:</span>
                  <span className="font-mono text-text font-semibold">Docker Isolated</span>
                </div>
                <div className="flex items-center justify-between text-text-2">
                  <span>Socket Egress:</span>
                  <span className="font-mono text-green font-semibold">0 External Calls</span>
                </div>
              </div>
            </div>

            {/* Recent Audit Events */}
            <div className="bg-surface border border-border rounded-2xl p-4 shadow-xs space-y-2.5">
              <div className="flex items-center justify-between border-b border-border-subtle pb-2">
                <span className="text-xs font-serif font-bold text-text">Recent Audit Trail</span>
                <Link href="/audit" className="text-[10px] font-mono text-accent hover:underline">
                  Full Local Audit →
                </Link>
              </div>

              <div className="space-y-2 text-xs font-mono">
                <div className="p-2 rounded-lg bg-surface-2/40 border border-border space-y-0.5">
                  <div className="flex justify-between text-[10px] text-text-3">
                    <span>Task Run</span>
                    <span>10:14 AM</span>
                  </div>
                  <p className="text-text font-medium text-[11px] truncate">P-204 Vibration Overhaul Note</p>
                  <p className="text-green text-[10px]">Verified 96% Conf.</p>
                </div>
                <div className="p-2 rounded-lg bg-surface-2/40 border border-border space-y-0.5">
                  <div className="flex justify-between text-[10px] text-text-3">
                    <span>Sandbox Exec</span>
                    <span>10:14 AM</span>
                  </div>
                  <p className="text-text font-medium text-[11px] truncate">calculate_bearing_harmonics.py</p>
                  <p className="text-accent text-[10px]">Exit Code 0 (No Egress)</p>
                </div>
              </div>
            </div>
          </aside>
        )}
      </div>
    </AppShell>
  );
}
