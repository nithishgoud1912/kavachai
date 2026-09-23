"use client";

import React, { useState } from "react";
import Link from "next/link";
import AppShell from "@/app/components/AppShell";
import { useSession } from "@/app/hooks/useSession";
import SovereignBadge from "@/app/components/SovereignBadge";

export default function SettingsPage() {
  const { session, logout } = useSession();
  const [notifyComplete, setNotifyComplete] = useState(true);
  const [notifyHitl, setNotifyHitl] = useState(true);
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  return (
    <AppShell
      title="User & Station Settings"
      subtitle="Operational Profile & Preferences"
      breadcrumbs={[
        { label: "Workspace", href: "/workspace" },
        { label: "Settings" },
      ]}
    >
      <div className="space-y-6 max-w-4xl mx-auto pb-12">
        {/* Profile Card */}
        <div className="p-6 bg-surface border border-border rounded-2xl shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-border-subtle pb-3">
            <div>
              <h3 className="font-serif font-bold text-base text-text">Session Profile</h3>
              <p className="text-xs text-text-3 font-mono">
                Authenticated Station Operator (MRPL Air-Gapped RBAC)
              </p>
            </div>
            <SovereignBadge size="sm" />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-mono">
            <div className="p-3 bg-surface-2/40 border border-border rounded-xl space-y-1">
              <span className="text-[10px] text-text-3 uppercase">Operator Name</span>
              <p className="font-bold text-text text-sm">{session?.name || "Refinery Engineer"}</p>
            </div>
            <div className="p-3 bg-surface-2/40 border border-border rounded-xl space-y-1">
              <span className="text-[10px] text-text-3 uppercase">Department Unit</span>
              <p className="font-bold text-accent text-sm">{session?.department || "OPERATIONS"}</p>
            </div>
          </div>
        </div>

        {/* Notifications */}
        <div className="p-6 bg-surface border border-border rounded-2xl shadow-xs space-y-4">
          <h3 className="font-serif font-bold text-base text-text">Desktop Alert Preferences</h3>

          <div className="space-y-3 text-xs">
            <label className="flex items-center justify-between p-3 rounded-xl bg-bg-base/60 border border-border cursor-pointer">
              <div>
                <p className="font-semibold text-text">Task Completion Notification</p>
                <p className="text-text-3 text-[11px]">Display toast alert when an agentic deliverable finishes.</p>
              </div>
              <input
                type="checkbox"
                checked={notifyComplete}
                onChange={(e) => setNotifyComplete(e.target.checked)}
                className="w-4 h-4 accent-accent rounded cursor-pointer"
              />
            </label>

            <label className="flex items-center justify-between p-3 rounded-xl bg-bg-base/60 border border-border cursor-pointer">
              <div>
                <p className="font-semibold text-text">HITL Sign-Off Required Notification</p>
                <p className="text-text-3 text-[11px]">Immediate visual ping when a document requires safety endorsement.</p>
              </div>
              <input
                type="checkbox"
                checked={notifyHitl}
                onChange={(e) => setNotifyHitl(e.target.checked)}
                className="w-4 h-4 accent-accent rounded cursor-pointer"
              />
            </label>
          </div>

          <div className="flex justify-end pt-2">
            <button
              onClick={handleSave}
              className="px-4 py-2 rounded-xl bg-accent text-white hover:bg-accent-hover text-xs font-semibold shadow-xs transition-colors cursor-pointer"
            >
              {saved ? "✓ Preferences Saved" : "Save Preferences"}
            </button>
          </div>
        </div>

        {/* Admin Navigation Shortcut */}
        <div className="p-6 bg-surface border border-border rounded-2xl shadow-xs flex items-center justify-between">
          <div>
            <h4 className="font-serif font-bold text-sm text-text">System Governance & Admin Console</h4>
            <p className="text-xs text-text-3 font-mono">
              Model weight registration, KB source management & sandbox resource caps
            </p>
          </div>
          <Link
            href="/settings/admin"
            className="px-4 py-2 rounded-xl bg-surface-2 hover:bg-surface border border-border text-text font-semibold text-xs transition-colors"
          >
            Access Admin Console →
          </Link>
        </div>
      </div>
    </AppShell>
  );
}
