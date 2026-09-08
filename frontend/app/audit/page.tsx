"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Header from "@/app/components/Header";
import VerificationBadge from "@/app/components/VerificationBadge";
import { useSession } from "@/app/hooks/useSession";
import { getAuditLog } from "@/app/services/api";
import { AGENT_DISPLAY_NAMES } from "@/app/types";
import type { AuditEntry, AgentName } from "@/app/types";

export default function AuditLogPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading: sessionLoading } = useSession();
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [offset, setOffset] = useState(0);
  const limit = 50;

  useEffect(() => {
    if (!sessionLoading && !isAuthenticated) {
      router.push("/");
      return;
    }

    if (isAuthenticated) {
      async function fetchAudit() {
        setLoading(true);
        try {
          const data = await getAuditLog(limit, offset);
          setEntries(data.entries);
          setTotal(data.total);
        } catch (err) {
          setError(err instanceof Error ? err.message : "Failed to load audit log");
        } finally {
          setLoading(false);
        }
      }

      fetchAudit();
    }
  }, [isAuthenticated, sessionLoading, router, offset]);

  if (sessionLoading) {
    return (
      <div className="min-h-screen bg-bg flex flex-col">
        <Header showBackToWorkspace showAuditLink={false} />
        <main className="flex-1 max-w-6xl mx-auto w-full px-6 py-10">
          <div className="space-y-6 animate-pulse">
            <div className="h-8 bg-surface-2 rounded w-48" />
            <div className="h-64 bg-surface rounded-xl border border-border" />
          </div>
        </main>
      </div>
    );
  }

  if (!isAuthenticated) return null;

  return (
    <div className="min-h-screen bg-bg flex flex-col">
      <Header showBackToWorkspace showAuditLink={false} />

      <main className="flex-1 max-w-6xl mx-auto w-full px-6 section-padding">
        <div className="animate-fade-in-up">
          <h1 className="font-[family-name:var(--font-playfair)] font-serif text-3xl text-text font-normal mb-2 tracking-tight">
            Audit Log
          </h1>
          <p className="text-text-3 text-sm mb-8">
            Append-only record of all investigations
          </p>
        </div>

        {loading && (
          <div className="space-y-3 animate-pulse">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-16 bg-surface-2 rounded-lg" />
            ))}
          </div>
        )}

        {error && (
          <div className="text-red text-sm bg-red/10 border border-red/20 rounded-lg px-4 py-3">
            {error}
          </div>
        )}

        {!loading && !error && (
          <>
            <div className="overflow-x-auto rounded-xl border border-border bg-surface card-shadow">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-surface-2">
                    <th className="text-left py-3 px-4 text-text-3 text-xs font-medium font-[family-name:var(--font-mono)]">
                      Timestamp
                    </th>
                    <th className="text-left py-3 px-4 text-text-3 text-xs font-medium">
                      User
                    </th>
                    <th className="text-left py-3 px-4 text-text-3 text-xs font-medium">
                      Dept
                    </th>
                    <th className="text-left py-3 px-4 text-text-3 text-xs font-medium">
                      Query
                    </th>
                    <th className="text-left py-3 px-4 text-text-3 text-xs font-medium">
                      Agents
                    </th>
                    <th className="text-left py-3 px-4 text-text-3 text-xs font-medium">
                      Verification
                    </th>
                    <th className="text-right py-3 px-4 text-text-3 text-xs font-medium font-[family-name:var(--font-mono)]">
                      Conf.
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {entries.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="py-12 text-center text-text-3 text-sm">
                        No audit entries yet
                      </td>
                    </tr>
                  ) : (
                    entries.map((entry, i) => (
                      <tr
                        key={entry.investigation_id + i}
                        className="border-t border-border/50 hover:bg-teal/5 transition-colors cursor-pointer"
                        onClick={() => router.push(`/report/${entry.investigation_id}`)}
                      >
                        <td className="py-3 px-4 font-[family-name:var(--font-mono)] text-text-2 text-xs whitespace-nowrap">
                          {formatTimestamp(entry.timestamp)}
                        </td>
                        <td className="py-3 px-4 text-text text-xs">
                          {entry.user}
                        </td>
                        <td className="py-3 px-4 font-[family-name:var(--font-mono)] text-text-3 text-xs">
                          {entry.department}
                        </td>
                        <td className="py-3 px-4 text-text-2 text-xs max-w-xs truncate">
                          {entry.query}
                        </td>
                        <td className="py-3 px-4 text-text-3 text-xs">
                          <div className="flex flex-wrap gap-1">
                            {entry.agents_invoked.map((agent) => (
                              <span
                                key={agent}
                                className="font-[family-name:var(--font-mono)] text-[10px] bg-surface-3 px-1.5 py-0.5 rounded"
                              >
                                {AGENT_DISPLAY_NAMES[agent as AgentName]?.split(" ")[0]?.toLowerCase() || agent}
                              </span>
                            ))}
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <VerificationBadge status={entry.verification_status} size="sm" />
                        </td>
                        <td className="py-3 px-4 font-[family-name:var(--font-mono)] text-accent text-xs text-right font-medium">
                          {entry.confidence}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {total > limit && (
              <div className="flex items-center justify-between mt-6">
                <p className="text-text-3 text-xs font-[family-name:var(--font-mono)]">
                  {offset + 1}–{Math.min(offset + limit, total)} of {total}
                </p>
                <div className="flex gap-2">
                  <button
                    onClick={() => setOffset(Math.max(0, offset - limit))}
                    disabled={offset === 0}
                    className="text-sm text-text-3 hover:text-teal px-3 py-1.5 rounded-lg border border-border
                               hover:border-teal/30 transition-all disabled:opacity-30 disabled:cursor-not-allowed"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => setOffset(offset + limit)}
                    disabled={offset + limit >= total}
                    className="text-sm text-text-3 hover:text-teal px-3 py-1.5 rounded-lg border border-border
                               hover:border-teal/30 transition-all disabled:opacity-30 disabled:cursor-not-allowed"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}

function formatTimestamp(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleString("en-IN", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    });
  } catch {
    return iso;
  }
}
