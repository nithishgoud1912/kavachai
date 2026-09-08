"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import Header from "@/app/components/Header";
import AgentTimeline from "@/app/components/AgentTimeline";
import InsufficientEvidence from "@/app/components/InsufficientEvidence";
import { useSession } from "@/app/hooks/useSession";
import { useInvestigation } from "@/app/hooks/useInvestigation";
import { useInvestigationStream } from "@/app/hooks/useInvestigationStream";
import { getReport, getPlan } from "@/app/services/api";
import type { SubTask } from "@/app/types";

export default function InvestigationPage() {
  const router = useRouter();
  const routeParams = useParams();
  const id = (routeParams?.id as string) || "";
  const { isAuthenticated, isLoading: sessionLoading } = useSession();
  const investigation = useInvestigation();
  const [plan, setPlan] = useState<SubTask[]>([]);
  const [query, setQuery] = useState<string>("");

  // Redirect if not authenticated once session check is complete
  useEffect(() => {
    if (!sessionLoading && !isAuthenticated) {
      router.push("/");
    }
  }, [sessionLoading, isAuthenticated, router]);

  // Start streaming on mount
  useEffect(() => {
    if (isAuthenticated && id) {
      investigation.setStreaming(id);

      // Fetch the plan for enriched timeline
      getPlan(id)
        .then((p) => {
          setPlan(p.sub_tasks);
        })
        .catch(() => {
          // Plan fetch is optional enrichment
        });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, isAuthenticated]);

  // SSE Stream
  useInvestigationStream(
    investigation.investigationState === "streaming" && id ? id : null,
    {
      onAgentUpdate: (update) => {
        investigation.updateAgent(update);
      },
      onInvestigationComplete: async (data) => {
        try {
          const report = await getReport(id);
          setQuery(report.query);
          investigation.setCompleted(report);
          router.push(`/report/${id}`);
        } catch {
          investigation.setFailed("Failed to load investigation report");
        }
      },
      onInsufficientEvidence: (data) => {
        investigation.setInsufficientEvidence(
          data.message || "No relevant evidence found in the knowledge base."
        );
      },
      onReconnecting: () => {
        investigation.setRecovering();
      },
      onError: () => {
        // Don't immediately fail — the backend may still be processing
        if (
          investigation.investigationState !== "completed" &&
          investigation.investigationState !== "insufficient_evidence"
        ) {
          investigation.setRecovering();
          // Try to fetch report in case investigation completed while disconnected
          setTimeout(async () => {
            try {
              const report = await getReport(id);
              investigation.setCompleted(report);
              router.push(`/report/${id}`);
            } catch {
              // Still processing or truly failed — stay in recovering state
            }
          }, 2000);
        }
      },
    }
  );

  if (sessionLoading) {
    return (
      <div className="min-h-screen bg-bg flex flex-col">
        <Header showBackToWorkspace />
        <main className="flex-1 flex flex-col items-center px-6 py-10">
          <div className="w-full max-w-2xl space-y-8 animate-pulse">
            <div className="h-6 bg-surface-2 rounded w-1/4" />
            <div className="h-10 bg-surface-2 rounded w-3/4" />
            <div className="h-48 bg-surface-2 rounded-xl" />
          </div>
        </main>
      </div>
    );
  }

  if (!isAuthenticated) return null;

  return (
    <div className="min-h-screen bg-bg flex flex-col">
      <Header showBackToWorkspace />

      <main className="flex-1 flex flex-col items-center px-6 py-10">
        <div className="w-full max-w-2xl space-y-8">
          {/* Query Display */}
          <div className="animate-fade-in-up">
            <p className="text-text-3 text-sm mb-2">Investigating:</p>
            <h1 className="font-[family-name:var(--font-fraunces)] text-xl text-text font-light leading-relaxed">
              &ldquo;{query || "Pump P-102 condition and vibration assessment"}&rdquo;
            </h1>
          </div>

          {/* Recovering Banner */}
          {investigation.investigationState === "recovering" && (
            <div className="bg-orange/10 border border-orange/20 rounded-lg px-4 py-3 flex items-center gap-3 animate-fade-in">
              <svg className="animate-spin h-4 w-4 text-orange" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" opacity="0.3" />
                <path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
              </svg>
              <span className="text-orange text-sm">
                Reconnecting to investigation stream…
              </span>
            </div>
          )}

          {/* Agent Timeline */}
          <AgentTimeline agents={investigation.agents} plan={plan} />

          {/* Insufficient Evidence */}
          {investigation.investigationState === "insufficient_evidence" && (
            <InsufficientEvidence
              message={investigation.insufficientMessage || undefined}
              onBackToWorkspace={() => router.push("/workspace")}
            />
          )}

          {/* Error State */}
          {investigation.investigationState === "failed" && (
            <div className="bg-red/10 border border-red/20 rounded-xl p-6 text-center animate-fade-in">
              <p className="text-red text-sm mb-4">{investigation.error}</p>
              <button
                onClick={() => router.push("/workspace")}
                className="text-sm text-teal hover:text-accent transition-colors cursor-pointer"
              >
                Return to workspace
              </button>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
