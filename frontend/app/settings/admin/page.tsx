"use client";

import React, { useState } from "react";
import AppShell from "@/app/components/AppShell";
import AdminGuard from "@/app/components/AdminGuard";
import SovereignBadge from "@/app/components/SovereignBadge";

export default function AdminSettingsPage() {
  const [ramCap, setRamCap] = useState("512");
  const [timeoutSec, setTimeoutSec] = useState("5");
  const [retentionDays, setRetentionDays] = useState("365");
  const [saved, setSaved] = useState(false);

  const handleSaveCaps = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <AppShell
      title="Admin System Governance"
      subtitle="Air-Gap Security & Compute Caps"
      breadcrumbs={[
        { label: "Workspace", href: "/workspace" },
        { label: "Settings", href: "/settings" },
        { label: "Admin Governance" },
      ]}
    >
      <AdminGuard>
        <div className="space-y-6 max-w-4xl mx-auto pb-12">
          {/* Header */}
          <div className="p-6 bg-surface border border-border rounded-2xl shadow-xs space-y-2">
            <div className="flex items-center justify-between">
              <h2 className="font-serif text-xl font-bold text-text">
                MRPL Sovereign Workbench Governance
              </h2>
              <SovereignBadge size="sm" showSubtitle={true} />
            </div>
            <p className="text-xs text-text-3 font-mono">
              Enforce physical container constraints, audit retention schedules, and AST import policies.
            </p>
          </div>

          {/* Sandbox Resource Caps */}
          <div className="p-6 bg-surface border border-border rounded-2xl shadow-xs space-y-4">
            <h3 className="font-serif font-bold text-base text-text">
              Sandbox Container Hardening & Resource Caps
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
              <div className="space-y-1.5">
                <label className="font-semibold text-text-2 font-mono uppercase text-[11px]">
                  Memory Cap (MB)
                </label>
                <input
                  type="number"
                  value={ramCap}
                  onChange={(e) => setRamCap(e.target.value)}
                  className="w-full p-2.5 rounded-xl border border-border bg-bg-base font-mono focus:bg-surface focus:outline-none"
                />
              </div>

              <div className="space-y-1.5">
                <label className="font-semibold text-text-2 font-mono uppercase text-[11px]">
                  Execution Timeout (Seconds)
                </label>
                <input
                  type="number"
                  value={timeoutSec}
                  onChange={(e) => setTimeoutSec(e.target.value)}
                  className="w-full p-2.5 rounded-xl border border-border bg-bg-base font-mono focus:bg-surface focus:outline-none"
                />
              </div>

              <div className="space-y-1.5">
                <label className="font-semibold text-text-2 font-mono uppercase text-[11px]">
                  WORM Audit Retention (Days)
                </label>
                <input
                  type="number"
                  value={retentionDays}
                  onChange={(e) => setRetentionDays(e.target.value)}
                  className="w-full p-2.5 rounded-xl border border-border bg-bg-base font-mono focus:bg-surface focus:outline-none"
                />
              </div>
            </div>

            <div className="p-3 bg-surface-2/60 border border-border rounded-xl text-xs space-y-1 font-mono text-text-2">
              <span className="font-bold text-accent">Active Docker Parameters:</span>
              <p className="text-[11px] text-text-3">
                --network none --security-opt=no-new-privileges --read-only --pids-limit 64 --memory {ramCap}m
              </p>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={handleSaveCaps}
                className="px-4 py-2 rounded-xl bg-accent text-white hover:bg-accent-hover text-xs font-semibold shadow-xs transition-colors cursor-pointer"
              >
                {saved ? "✓ Governance Parameters Updated" : "Apply Security Policy"}
              </button>
            </div>
          </div>
        </div>
      </AdminGuard>
    </AppShell>
  );
}
