"use client";

import React, { useState } from "react";

interface HITLReviewBarProps {
  status?: "pending" | "approved" | "revised" | "rejected";
  onApprove: (comments: string) => Promise<void>;
  onRevise: (comments: string) => Promise<void>;
  onReject: (comments: string) => Promise<void>;
  className?: string;
}

export default function HITLReviewBar({
  status = "pending",
  onApprove,
  onRevise,
  onReject,
  className = "",
}: HITLReviewBarProps) {
  const [comments, setComments] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [actionDone, setActionDone] = useState<string | null>(null);

  if (status !== "pending" && !actionDone) {
    let color = "bg-green/10 text-green border-green/30";
    let text = `Deliverable Approved with Full Clearance`;
    if (status === "revised") {
      color = "bg-warning/10 text-warning border-warning/30";
      text = `Revision Requested — Re-routing to Agent`;
    } else if (status === "rejected") {
      color = "bg-red/10 text-red border-red/30";
      text = `Deliverable Rejected by Authority`;
    }

    return (
      <div className={`p-4 rounded-xl border text-xs font-semibold flex items-center justify-between ${color} ${className}`}>
        <span className="flex items-center gap-2">
          <span>🛡️</span>
          <span>{text}</span>
        </span>
        <span className="font-mono text-[11px] uppercase">MRPL Sign-Off Complete</span>
      </div>
    );
  }

  const handleAction = async (type: "approve" | "revise" | "reject") => {
    setSubmitting(true);
    try {
      if (type === "approve") await onApprove(comments);
      if (type === "revise") await onRevise(comments);
      if (type === "reject") await onReject(comments);
      setActionDone(type);
    } catch {
      // Handled in parent
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      className={`p-4 rounded-2xl bg-surface border-2 border-accent/30 shadow-md space-y-3 ${className}`}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-base">⚠️</span>
          <div>
            <h4 className="font-serif font-bold text-sm text-text">
              Human-in-the-Loop Sign-Off Required
            </h4>
            <p className="text-xs text-text-2">
              Statutory or operational action note requires safety engineer sign-off before dispatch.
            </p>
          </div>
        </div>
        <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-accent/10 text-accent font-semibold">
          Clearance Level 2
        </span>
      </div>

      <input
        type="text"
        value={comments}
        onChange={(e) => setComments(e.target.value)}
        placeholder="Optional endorsement remarks or specific revision instructions..."
        className="w-full text-xs p-2.5 rounded-lg border border-border bg-bg-base focus:bg-surface focus:outline-none focus:ring-1 focus:ring-accent"
      />

      <div className="flex items-center justify-end gap-2.5 pt-1">
        <button
          onClick={() => handleAction("reject")}
          disabled={submitting}
          className="px-3 py-1.5 rounded-lg border border-red/30 text-red hover:bg-red/10 text-xs font-semibold transition-colors"
        >
          Reject Note
        </button>
        <button
          onClick={() => handleAction("revise")}
          disabled={submitting}
          className="px-3 py-1.5 rounded-lg border border-border text-text hover:bg-surface-2 text-xs font-semibold transition-colors"
        >
          Request Revision
        </button>
        <button
          onClick={() => handleAction("approve")}
          disabled={submitting}
          className="px-4 py-1.5 rounded-lg bg-green text-white hover:bg-green/90 text-xs font-semibold shadow-xs transition-colors"
        >
          Approve & Sign Deliverable
        </button>
      </div>
    </div>
  );
}
