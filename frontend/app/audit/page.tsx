"use client";

import { useEffect, useState } from "react";
import AppShell from "@/app/components/AppShell";
import VerificationBadge from "@/app/components/VerificationBadge";
import SovereignBadge from "@/app/components/SovereignBadge";
import Badge from "@/app/components/Badge";
import { getAuditLog } from "@/app/services/api";
import { downloadJson } from "@/app/services/fileDownload";
import type { AuditEntry } from "@/app/types";

export default function AuditLogPage() {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedEntry, setSelectedEntry] = useState<AuditEntry | null>(null);
  const [deptFilter, setDeptFilter] = useState("all");

  useEffect(() => {
    async function fetchAudit() {
      setLoading(true);
      try {
        const data = await getAuditLog(50, 0);
        setEntries(data.entries);
        setTotal(data.total);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Audit records unavailable");
        setEntries([]);
        setTotal(0);
      } finally {
        setLoading(false);
      }
    }

    fetchAudit();
  }, []);

  const filtered = entries.filter((e) => deptFilter === "all" || e.department === deptFilter);

  const handleExport = () => {
    downloadJson("local-audit-records.json", {
      type: "LOCAL_AUDIT_LOG_EXPORT",
      total_records: filtered.length,
      exported_at: new Date().toISOString(),
      compliance: "Application audit records; not independently immutable storage",
      records: filtered,
    });
  };

  return (
    <AppShell
      title="Local Audit Trail"
      subtitle="Application and security events"
      breadcrumbs={[
        { label: "Workspace", href: "/workspace" },
        { label: "Audit Trail" },
      ]}
    >
      <div className="space-y-6 max-w-7xl mx-auto pb-12">
        {/* Header Notice */}
        <div className="p-6 bg-surface border border-border rounded-2xl shadow-xs space-y-2">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="font-serif text-xl font-bold text-text">
                Statutory Regulatory & Operational Audit Trail
              </h2>
              <p className="text-xs text-text-3 font-mono">
                Application audit records. Off-host immutable retention must be configured separately.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <SovereignBadge size="sm" />
              <button
                onClick={handleExport}
                className="px-4 py-2 rounded-xl bg-accent text-white hover:bg-accent-hover text-xs font-semibold shadow-xs transition-colors cursor-pointer"
              >
                Export Audit (.JSON / CSV)
              </button>
            </div>
          </div>
        </div>

        {error && (
          <div className="p-4 bg-amber-500/10 border border-amber-500/20 rounded-2xl flex items-center gap-3 text-xs font-mono text-amber-700">
            <span className="text-base">🛡️</span>
            <span>{error}</span>
          </div>
        )}

        {/* Filter Bar */}
        <div className="flex items-center justify-between p-4 bg-surface border border-border rounded-2xl shadow-xs text-xs font-mono">
          <div className="flex items-center gap-2">
            <span className="text-text-3 uppercase">Filter Department:</span>
            <select
              value={deptFilter}
              onChange={(e) => setDeptFilter(e.target.value)}
              className="bg-surface-2 border border-border px-2.5 py-1.5 rounded-xl text-text font-semibold focus:outline-none"
            >
              <option value="all">All Departments</option>
              <option value="OPERATIONS">OPERATIONS</option>
              <option value="MAINTENANCE">MAINTENANCE</option>
              <option value="SAFETY">SAFETY (HSE)</option>
              <option value="ENGINEERING">ENGINEERING</option>
              <option value="AUDIT">AUDIT</option>
            </select>
          </div>

          <span className="text-text-3">
            Showing {filtered.length} of {total} records
          </span>
        </div>

        {/* Table */}
        <div className="bg-surface border border-border rounded-2xl overflow-hidden shadow-xs p-5 space-y-3">
          {loading ? (
            <div className="p-8 text-center text-xs text-text-3">Loading WORM ledger...</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-sans border-collapse">
                <thead>
                  <tr className="border-b border-border text-text-3 font-mono text-[11px] uppercase">
                    <th className="pb-2.5">Task / Audit ID</th>
                    <th className="pb-2.5">User</th>
                    <th className="pb-2.5">Department</th>
                    <th className="pb-2.5">Query Description</th>
                    <th className="pb-2.5">Agents Invoked</th>
                    <th className="pb-2.5">Confidence</th>
                    <th className="pb-2.5">Verification</th>
                    <th className="pb-2.5 text-right">Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/60">
                  {filtered.map((entry, idx) => (
                    <tr
                      key={idx}
                      onClick={() => setSelectedEntry(entry)}
                      className="hover:bg-bg-base/70 transition-colors cursor-pointer"
                    >
                      <td className="py-3 font-mono font-bold text-accent">
                        {entry.investigation_id}
                      </td>
                      <td className="py-3 font-semibold text-text">{entry.user}</td>
                      <td className="py-3 font-mono text-[11px] text-text-2">
                        <span className="px-2 py-0.5 rounded bg-surface-2 border border-border">
                          {entry.department}
                        </span>
                      </td>
                      <td className="py-3 font-medium text-text max-w-xs truncate">
                        {entry.query}
                      </td>
                      <td className="py-3">
                        <div className="flex flex-wrap gap-1">
                          {entry.agents_invoked.map((a) => (
                            <span
                              key={a}
                              className="px-1.5 py-0.2 rounded bg-surface-2 border border-border text-[10px] font-mono text-text-3"
                            >
                              {a.replace("_agent", "")}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="py-3 font-mono font-semibold text-text">
                        {Math.round(entry.confidence * 100)}%
                      </td>
                      <td className="py-3">
                        <VerificationBadge status={entry.verification_status} size="sm" />
                      </td>
                      <td className="py-3 text-right">
                        <span className="text-text-3 hover:text-accent font-mono text-[11px]">
                          Inspect →
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Read-Only WORM Detail Drawer */}
        {selectedEntry && (
          <div className="fixed inset-0 bg-black/40 backdrop-blur-xs flex items-center justify-end z-50 p-4">
            <div className="bg-surface border border-border rounded-2xl p-6 max-w-lg w-full h-[90vh] shadow-xl flex flex-col justify-between space-y-4 overflow-y-auto">
              <div className="space-y-4">
                <div className="flex items-center justify-between border-b border-border pb-3">
                  <div>
                    <h3 className="font-serif font-bold text-base text-text">
                      WORM Audit Record Details
                    </h3>
                    <span className="font-mono text-xs text-accent">
                      {selectedEntry.investigation_id}
                    </span>
                  </div>
                  <button
                    onClick={() => setSelectedEntry(null)}
                    className="p-1 rounded-lg text-text-3 hover:text-text"
                  >
                    ✕
                  </button>
                </div>

                <div className="space-y-3 text-xs font-mono">
                  <div className="p-3 bg-surface-2/50 rounded-xl space-y-1">
                    <span className="text-[10px] text-text-3 uppercase">Operator</span>
                    <p className="font-bold text-text text-sm">
                      {selectedEntry.user} ({selectedEntry.department})
                    </p>
                  </div>

                  <div className="p-3 bg-surface-2/50 rounded-xl space-y-1">
                    <span className="text-[10px] text-text-3 uppercase">Timestamp</span>
                    <p className="text-text">{selectedEntry.timestamp}</p>
                  </div>

                  <div className="p-3 bg-surface-2/50 rounded-xl space-y-1">
                    <span className="text-[10px] text-text-3 uppercase">Query</span>
                    <p className="text-text font-sans font-medium text-xs">{selectedEntry.query}</p>
                  </div>

                  <div className="p-3 bg-surface-2/50 rounded-xl space-y-1">
                    <span className="text-[10px] text-text-3 uppercase">Agents & Tools Invoked</span>
                    <div className="flex flex-wrap gap-1 pt-1">
                      {selectedEntry.agents_invoked.map((a) => (
                        <span key={a} className="px-2 py-0.5 rounded bg-surface border border-border text-text">
                          {a}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="p-3 bg-surface-2/50 rounded-xl space-y-1">
                    <span className="text-[10px] text-text-3 uppercase">Verification & Confidence</span>
                    <div className="flex items-center gap-3 pt-1">
                      <VerificationBadge status={selectedEntry.verification_status} />
                      <span className="font-bold text-text">
                        {(selectedEntry.confidence * 100).toFixed(0)}% Statistical Confidence
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="pt-4 border-t border-border flex items-center justify-between text-xs text-text-3 font-mono">
                <span>Read-Only Compliance Record</span>
                <button
                  onClick={() => setSelectedEntry(null)}
                  className="px-4 py-2 rounded-xl bg-surface-2 hover:bg-surface border border-border text-text font-medium cursor-pointer"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
