"use client";

import React from "react";
import type { Report, AttachmentItem } from "@/app/types";

interface InvestigationReportProps {
  report: Report;
  attachments?: AttachmentItem[];
}

export default function InvestigationReport({
  report,
  attachments = [],
}: InvestigationReportProps) {
  const allAttachments = (attachments && attachments.length > 0)
    ? attachments
    : (report.attachments || []);

  if (allAttachments.length === 0) return null;

  return (
    <div className="bg-surface border border-border rounded-xl px-6 py-4 card-shadow mt-4">
      <div className="flex items-center justify-between mb-3">
        <p className="text-text-3 text-xs uppercase tracking-wider font-semibold flex items-center gap-2">
          <span>📁</span> Attached Documents & Folders ({allAttachments.length})
        </p>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {allAttachments.map((att, idx) => {
          const downloadUrl = att.source_id
            ? `/api/v1/evidence/files/${encodeURIComponent(att.source_id)}/raw`
            : att.url || `/api/v1/evidence/files/${encodeURIComponent(att.filename)}/raw`;

          return (
            <div
              key={idx}
              className="flex items-center justify-between p-2.5 rounded-lg border border-border bg-surface-2/40 hover:border-teal/50 transition-colors"
            >
              <div className="flex items-center gap-2.5 min-w-0 pr-2">
                <span className="text-base flex-shrink-0">
                  {att.type === "image" ? "🖼" : att.relative_path?.includes("/") ? "📁" : "📄"}
                </span>
                <div className="min-w-0">
                  <p
                    className="text-xs text-text font-medium truncate"
                    title={att.relative_path || att.filename}
                  >
                    {att.relative_path && att.relative_path !== att.filename
                      ? att.relative_path
                      : att.filename}
                  </p>
                  {att.size && (
                    <p className="text-[10px] text-text-3">
                      {(att.size / 1024).toFixed(1)} KB
                    </p>
                  )}
                </div>
              </div>
              <a
                href={downloadUrl}
                download={att.filename}
                target="_blank"
                rel="noopener noreferrer"
                className="flex-shrink-0 text-xs text-teal hover:text-accent font-medium px-2.5 py-1 rounded border border-border hover:border-teal transition-all flex items-center gap-1"
                title={`Download ${att.filename}`}
              >
                <svg
                  width="12"
                  height="12"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                  <polyline points="7 10 12 15 17 10" />
                  <line x1="12" y1="15" x2="12" y2="3" />
                </svg>
                Download
              </a>
            </div>
          );
        })}
      </div>
    </div>
  );
}
