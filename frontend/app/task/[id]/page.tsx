"use client";

import React, { use, useState } from "react";
import AppShell from "@/app/components/AppShell";
import TaskHeader from "@/app/components/TaskHeader";
import PlanTree from "@/app/components/PlanTree";
import ToolCallTimeline from "@/app/components/ToolCallTimeline";
import LiveOutputPanel from "@/app/components/LiveOutputPanel";
import ArtifactGallery from "@/app/components/ArtifactGallery";
import HITLReviewBar from "@/app/components/HITLReviewBar";
import TaskFollowUpInput from "@/app/components/TaskFollowUpInput";
import SourceCitation from "@/app/components/SourceCitation";
import SourceViewer from "@/app/components/SourceViewer";
import SandboxBlockedState from "@/app/components/SandboxBlockedState";
import Toast, { type ToastMessage } from "@/app/components/Toast";
import { useTask } from "@/app/hooks/useTask";
import { useTaskStream } from "@/app/hooks/useTaskStream";
import type { EvidenceReference } from "@/app/types";

export default function LiveTaskWorkspacePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const { task, loading, error, reviewTask, followUp, reload } = useTask(id);
  const [activeCitation, setActiveCitation] = useState<EvidenceReference | null>(null);
  const [toast, setToast] = useState<ToastMessage | null>(null);

  // SSE Stream integration for live multi-agent events
  const stream = useTaskStream(id, {
    onTaskCompleted: () => {
      void reload();
      setToast({
        id: "task-done",
        type: "success",
        title: "Agentic Task Completed",
        message: "All sub-tasks evaluated and deliverables synthesized on-premise.",
      });
    },
    onHitlRequired: () => {
      setToast({
        id: "hitl-alert",
        type: "warning",
        title: "Sign-Off Required",
        message: "Executive approval note awaiting safety engineer sign-off.",
      });
    },
  });

  if (loading) {
    return (
      <AppShell title="Live Task Workspace" subtitle={id}>
        <div className="flex h-96 items-center justify-center">
          <div className="space-y-3 text-center">
            <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin mx-auto" />
            <p className="font-serif text-accent text-sm font-semibold tracking-wide">
              Connecting to Air-Gapped Agent Pipeline...
            </p>
          </div>
        </div>
      </AppShell>
    );
  }

  if (error || !task) {
    return (
      <AppShell title="Task Workspace">
        <div className="max-w-xl mx-auto p-8 bg-surface border border-red/30 rounded-2xl text-center space-y-4 my-12">
          <span className="text-3xl">⚠️</span>
          <h3 className="font-serif text-lg font-bold text-red">Unable to Load Task</h3>
          <p className="text-xs text-text-2">{error || "Task was not found in the local repository."}</p>
        </div>
      </AppShell>
    );
  }

  // Merge SSE live stream state with initial task data
  const currentPlan = stream.plan.length > 0 ? stream.plan : task.plan;
  const currentToolCalls = stream.toolCalls.length > 0 ? stream.toolCalls : task.tool_calls;
  const currentReasoning = stream.reasoning || task.reasoning_output;
  const currentArtifacts = stream.artifacts.length > 0 ? stream.artifacts : task.artifacts;
  const currentCitations = stream.citations.length > 0 ? stream.citations : task.citations;

  const handleApprove = async (comments: string) => {
    await reviewTask("approve", comments);
    setToast({
      id: "approved",
      type: "success",
      title: "Deliverable Approved",
      message: "Endorsement recorded in local append-only audit trail.",
    });
  };

  const handleRevise = async (comments: string) => {
    await reviewTask("revise", comments);
    window.location.reload();
    setToast({
      id: "revised",
      type: "info",
      title: "Revision Requested",
      message: "Agent prompted to re-synthesize parameters with revision comments.",
    });
  };

  const handleReject = async (comments: string) => {
    await reviewTask("reject", comments);
    setToast({
      id: "rejected",
      type: "error",
      title: "Deliverable Rejected",
      message: "Action note was marked as rejected by operator.",
    });
  };

  const handleFollowUp = async (msg: string) => {
    await followUp(msg);
  };

  return (
    <AppShell
      title="Live Agent Workspace"
      subtitle={task.id}
      breadcrumbs={[
        { label: "Workspace", href: "/workspace" },
        { label: "Tasks", href: "/tasks" },
        { label: task.id },
      ]}
    >
      <div className="space-y-6 max-w-7xl mx-auto pb-12">
        {/* Task Header */}
        <TaskHeader task={task} />

        {/* Two-Pane Workspace Layout (40% Left Plan/Timeline, 60% Right Reasoning/Deliverables) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* ─── Left Pane: Plan & Tool-Call Timeline (40% / 5 cols) ── */}
          <div className="lg:col-span-5 space-y-6">
            <PlanTree plan={currentPlan} />
            <ToolCallTimeline toolCalls={currentToolCalls} />
          </div>

          {/* ─── Right Pane: Output, Artifacts & Citations (60% / 7 cols) */}
          <div className="lg:col-span-7 space-y-6">
            {/* Human-In-The-Loop Approval Bar (when required) */}
            {task.hitl_required && (
              <HITLReviewBar
                status={task.hitl_status}
                onApprove={handleApprove}
                onRevise={handleRevise}
                onReject={handleReject}
              />
            )}

            {/* Live Streaming Reasoning Panel */}
            <LiveOutputPanel
              content={currentReasoning}
              isStreaming={stream.isStreaming}
            />

            {/* Generated Deliverables Artifacts Gallery */}
            <ArtifactGallery artifacts={currentArtifacts} taskId={task.id} />

            {/* Grounded Source Citations */}
            {currentCitations && currentCitations.length > 0 && (
              <div className="p-4 bg-surface border border-border rounded-2xl shadow-xs space-y-2">
                <span className="text-[11px] font-mono uppercase text-text-3 font-semibold">
                  Source Grounded Citations ({currentCitations.length})
                </span>
                <div className="flex flex-wrap gap-2 pt-1">
                  {currentCitations.map((c, i) => (
                    <SourceCitation
                      key={i}
                      citation={c}
                      onClick={(cit) => setActiveCitation(cit)}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Inline Context Follow-Up Input */}
            <div className="pt-2">
              <TaskFollowUpInput onSend={handleFollowUp} />
            </div>
          </div>
        </div>
      </div>

      {/* Source Viewer Modal for cited evidence inspection */}
      {activeCitation && (
        <SourceViewer
          sourceId={activeCitation.source_id}
          onClose={() => setActiveCitation(null)}
        />
      )}

      {/* Transient Notifications */}
      <Toast toast={toast} onClose={() => setToast(null)} />
    </AppShell>
  );
}
