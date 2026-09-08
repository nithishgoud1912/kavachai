"use client";

import { useState } from "react";
import { exportReport, getDownloadUrl } from "@/app/services/api";

interface ReportActionsProps {
  investigationId: string;
  hasPid: boolean;
  onViewEvidence: () => void;
  onViewPid?: () => void;
}

type ExportState = "idle" | "exporting" | "success" | "error";

export default function ReportActions({
  investigationId,
  hasPid,
  onViewEvidence,
  onViewPid,
}: ReportActionsProps) {
  const [exportState, setExportState] = useState<ExportState>("idle");

  async function handleExport() {
    setExportState("exporting");
    try {
      const result = await exportReport(investigationId, "pdf");
      // Trigger download
      const url = getDownloadUrl(result.download_url);
      const link = document.createElement("a");
      link.href = url;
      link.download = `kavachai-report-${investigationId}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      setExportState("success");
      setTimeout(() => setExportState("idle"), 3000);
    } catch {
      setExportState("error");
      setTimeout(() => setExportState("idle"), 3000);
    }
  }

  return (
    <div className="flex flex-wrap gap-3">
      <button
        onClick={onViewEvidence}
        className="bg-surface border border-border text-text-2 text-sm px-5 py-2.5 rounded-lg
                   hover:border-teal/40 hover:text-teal hover:bg-surface-2
                   transition-all duration-200 flex items-center gap-2"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
          <polyline points="14 2 14 8 20 8" />
          <line x1="16" y1="13" x2="8" y2="13" />
          <line x1="16" y1="17" x2="8" y2="17" />
        </svg>
        View Evidence
      </button>

      {hasPid && onViewPid && (
        <button
          onClick={onViewPid}
          className="bg-surface border border-border text-text-2 text-sm px-5 py-2.5 rounded-lg
                     hover:border-teal/40 hover:text-teal hover:bg-surface-2
                     transition-all duration-200 flex items-center gap-2"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <rect x="3" y="3" width="18" height="18" rx="2" />
            <circle cx="8.5" cy="8.5" r="1.5" />
            <path d="M21 15l-5-5L5 21" />
          </svg>
          View P&ID
        </button>
      )}

      <button
        onClick={handleExport}
        disabled={exportState === "exporting"}
        className={`text-sm px-5 py-2.5 rounded-lg flex items-center gap-2 transition-all duration-200
                    ${
                      exportState === "success"
                        ? "bg-green/10 border border-green/30 text-green"
                        : exportState === "error"
                        ? "bg-red/10 border border-red/30 text-red"
                        : "bg-accent text-bg hover:brightness-110 hover:-translate-y-0.5"
                    }
                    disabled:opacity-50 disabled:cursor-not-allowed`}
      >
        {exportState === "exporting" ? (
          <>
            <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" opacity="0.3" />
              <path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
            </svg>
            Exporting…
          </>
        ) : exportState === "success" ? (
          <>
            <span>✓</span> Exported
          </>
        ) : exportState === "error" ? (
          <>
            <span>✕</span> Export failed
          </>
        ) : (
          <>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
            Export Report
          </>
        )}
      </button>
    </div>
  );
}
