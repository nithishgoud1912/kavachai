"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter, useParams } from "next/navigation";
import Header from "@/app/components/Header";
import FindingCard from "@/app/components/FindingCard";
import ConfidenceRing from "@/app/components/ConfidenceRing";
import VerificationBadge from "@/app/components/VerificationBadge";
import PidRelationship from "@/app/components/PidRelationship";
import DataTrend from "@/app/components/DataTrend";
import ConclusionSection from "@/app/components/ConclusionSection";
import ReportActions from "@/app/components/ReportActions";
import SourceViewer from "@/app/components/SourceViewer";
import { useSession } from "@/app/hooks/useSession";
import { getReport } from "@/app/services/api";
import type { Report, OverallStatus } from "@/app/types";

const STATUS_CONFIG: Record<
  OverallStatus,
  { label: string; color: string; bg: string; icon: string }
> = {
  attention_required: {
    label: "ATTENTION REQUIRED",
    color: "text-orange",
    bg: "bg-orange/10 border-orange/30",
    icon: "⚠",
  },
  normal: {
    label: "NORMAL",
    color: "text-green",
    bg: "bg-green/10 border-green/30",
    icon: "✓",
  },
  critical: {
    label: "CRITICAL",
    color: "text-red",
    bg: "bg-red/10 border-red/30",
    icon: "✕",
  },
};

export default function ReportPage() {
  const router = useRouter();
  const routeParams = useParams();
  const id = (routeParams?.id as string) || "";
  const { isAuthenticated, isLoading: sessionLoading } = useSession();
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeSourceId, setActiveSourceId] = useState<string | null>(null);

  useEffect(() => {
    if (!sessionLoading && !isAuthenticated) {
      router.push("/");
      return;
    }

    if (isAuthenticated && id) {
      let isCancelled = false;
      async function fetchReport() {
        try {
          const data = await getReport(id);
          if (!isCancelled) {
            setReport(data);
          }
        } catch (err) {
          if (!isCancelled) {
            setError(err instanceof Error ? err.message : "Failed to load report");
          }
        } finally {
          if (!isCancelled) {
            setLoading(false);
          }
        }
      }

      fetchReport();
      return () => {
        isCancelled = true;
      };
    }
  }, [id, isAuthenticated, sessionLoading, router]);

  const handleCitationClick = useCallback((sourceId: string) => {
    setActiveSourceId(sourceId);
  }, []);

  const handleCloseSourceViewer = useCallback(() => {
    setActiveSourceId(null);
  }, []);

  // Loading skeleton (renders during SSR and client loading to avoid hydration mismatch)
  if (sessionLoading || loading) {
    return (
      <div className="min-h-screen bg-bg flex flex-col">
        <Header showBackToWorkspace />
        <main className="flex-1 max-w-4xl mx-auto w-full px-6 py-10">
          <div className="space-y-6 animate-pulse">
            <div className="h-8 bg-surface-2 rounded w-2/3" />
            <div className="h-5 bg-surface-2 rounded w-1/3" />
            <div className="space-y-4 mt-8">
              <div className="h-28 bg-surface-2 rounded-lg" />
              <div className="h-28 bg-surface-2 rounded-lg" />
              <div className="h-28 bg-surface-2 rounded-lg" />
            </div>
            <div className="h-24 bg-surface-2 rounded-lg mt-8" />
            <div className="flex gap-4 mt-6">
              <div className="h-20 w-20 bg-surface-2 rounded-full" />
              <div className="h-8 bg-surface-2 rounded w-40 self-center" />
            </div>
          </div>
        </main>
      </div>
    );
  }

  if (!isAuthenticated) return null;

  if (error || !report) {
    return (
      <div className="min-h-screen bg-bg flex flex-col">
        <Header showBackToWorkspace />
        <main className="flex-1 flex items-center justify-center">
          <div className="text-center space-y-4">
            <p className="text-red text-sm">{error || "Report not found"}</p>
            <button
              onClick={() => router.push("/workspace")}
              className="text-teal text-sm hover:text-accent transition-colors cursor-pointer"
            >
              ← Back to Workspace
            </button>
          </div>
        </main>
      </div>
    );
  }

  const statusConfig = STATUS_CONFIG[report.overall_status] || STATUS_CONFIG.attention_required;
  const highlightedEquipment = report.query.match(/P-\d+/)?.[0] || "P-102";
  const hasVibration = report.findings.some(
    (f) =>
      f.title.toLowerCase().includes("vibration") ||
      f.detail.toLowerCase().includes("mm/s")
  );

  const trendData = [
    { label: "Jan 10", value: 2.1 },
    { label: "Apr 11", value: 2.8 },
    { label: "Jul 09", value: 3.7 },
  ];

  return (
    <div className="min-h-screen bg-bg flex flex-col">
      <Header showBackToWorkspace />

      <main className="flex-1 max-w-4xl mx-auto w-full px-6 py-10">
        <div className="space-y-8">
          {/* ─── Report Header ────────────────────────────────────────── */}
          <div className="animate-fade-in-up">
            <div className="flex items-start justify-between flex-wrap gap-4 mb-4">
              <div>
                <h1 className="font-[family-name:var(--font-fraunces)] text-2xl md:text-3xl text-text font-light tracking-wide">
                  {report.query.includes("P-102")
                    ? "P-102 INVESTIGATION"
                    : "INVESTIGATION REPORT"}
                </h1>
                <p className="font-[family-name:var(--font-mono)] text-text-3 text-xs mt-2">
                  {report.generated_at}
                </p>
              </div>
              <span
                className={`text-xs font-semibold px-3 py-1.5 rounded-full border
                            ${statusConfig.bg} ${statusConfig.color} flex items-center gap-1.5`}
              >
                <span>{statusConfig.icon}</span>
                {statusConfig.label}
              </span>
            </div>

            {/* Condition Summary */}
            <div className="bg-surface border border-border rounded-xl px-6 py-4">
              <p className="text-text-3 text-xs uppercase tracking-wider mb-1">Condition</p>
              <p className="text-text text-lg font-light">{report.condition_summary}</p>
            </div>
          </div>

          {/* ─── Key Findings ─────────────────────────────────────────── */}
          <div className="animate-fade-in-up" style={{ animationDelay: "100ms" }}>
            <h2 className="font-[family-name:var(--font-fraunces)] text-sm font-semibold text-text-2 tracking-widest uppercase mb-4">
              Key Findings
            </h2>
            <div className="space-y-3">
              {report.findings.map((finding, i) => (
                <FindingCard
                  key={finding.id}
                  finding={finding}
                  index={i}
                  onCitationClick={handleCitationClick}
                />
              ))}
            </div>
          </div>

          {/* ─── Vibration Telemetry Trend ────────────────────────────── */}
          {hasVibration && (
            <div className="animate-fade-in-up" style={{ animationDelay: "150ms" }}>
              <DataTrend
                title="Pump P-102 Vibration Telemetry (Deterministic Sensor Log)"
                data={trendData}
                unit="mm/s"
                threshold={3.0}
                thresholdLabel="Spec Advisory Limit (3.0 mm/s)"
              />
            </div>
          )}

          {/* ─── P&ID Relationship ────────────────────────────────────── */}
          {report.pid_relationship && report.pid_relationship.length > 0 && (
            <div className="animate-fade-in-up" style={{ animationDelay: "200ms" }}>
              <PidRelationship
                components={report.pid_relationship}
                highlighted={highlightedEquipment}
              />
            </div>
          )}

          {/* ─── Conclusion ───────────────────────────────────────────── */}
          <div className="animate-fade-in-up" style={{ animationDelay: "300ms" }}>
            <ConclusionSection conclusion={report.conclusion} />
          </div>

          {/* ─── Confidence + Verification ────────────────────────────── */}
          <div
            className="flex items-center gap-8 flex-wrap animate-fade-in-up"
            style={{ animationDelay: "400ms" }}
          >
            <ConfidenceRing confidence={report.confidence} />
            <div className="space-y-2">
              <p className="text-text-3 text-xs">Verification</p>
              <VerificationBadge status={report.verification_status} />
            </div>
          </div>

          {/* ─── Actions ──────────────────────────────────────────────── */}
          <div className="animate-fade-in-up pt-2" style={{ animationDelay: "500ms" }}>
            <ReportActions
              investigationId={id}
              hasPid={!!report.pid_relationship && report.pid_relationship.length > 0}
              onViewEvidence={() => {
                const firstEvidence = report.findings[0]?.evidence[0];
                if (firstEvidence) {
                  setActiveSourceId(firstEvidence.source_id);
                }
              }}
              onViewPid={() => {
                const pidEvidence = report.findings
                  .flatMap((f) => f.evidence)
                  .find((e) => e.type === "pid_drawing");
                if (pidEvidence) {
                  setActiveSourceId(pidEvidence.source_id);
                }
              }}
            />
          </div>

          {/* ─── Original Query ───────────────────────────────────────── */}
          <div className="border-t border-border pt-6 mt-4">
            <p className="text-text-3 text-xs mb-1">Original query</p>
            <p className="text-text-2 text-sm font-[family-name:var(--font-mono)]">
              {report.query}
            </p>
          </div>
        </div>
      </main>

      {/* Source Viewer Panel */}
      <SourceViewer
        sourceId={activeSourceId}
        onClose={handleCloseSourceViewer}
      />
    </div>
  );
}
