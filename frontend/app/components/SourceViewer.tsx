"use client";

import { useState, useEffect, useCallback } from "react";
import { getEvidence } from "@/app/services/api";
import type { EvidenceSource, DocumentEvidence, DatasetEvidence, PidEvidence } from "@/app/types";

interface SourceViewerProps {
  sourceId: string | null;
  onClose: () => void;
}

export default function SourceViewer({ sourceId, onClose }: SourceViewerProps) {
  const [evidence, setEvidence] = useState<EvidenceSource | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchEvidence = useCallback(async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await getEvidence(id);
      setEvidence(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load evidence");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (sourceId) {
      fetchEvidence(sourceId);
    } else {
      setEvidence(null);
    }
  }, [sourceId, fetchEvidence]);

  // Keyboard dismiss
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    if (sourceId) {
      document.addEventListener("keydown", handleKeyDown);
      return () => document.removeEventListener("keydown", handleKeyDown);
    }
  }, [sourceId, onClose]);

  if (!sourceId) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 z-40 animate-fade-in"
        onClick={onClose}
      />

      {/* Panel */}
      <div className="fixed right-0 top-0 bottom-0 w-full max-w-lg bg-surface border-l border-border
                      z-50 overflow-y-auto animate-slide-in-right">
        {/* Header */}
        <div className="sticky top-0 bg-surface/95 backdrop-blur-sm border-b border-border px-6 py-4 flex items-center justify-between z-10">
          <h3 className="text-sm font-medium text-text">Source Viewer</h3>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg bg-surface-2 hover:bg-surface-3 flex items-center justify-center
                       text-text-3 hover:text-text transition-colors duration-200"
            aria-label="Close source viewer"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {loading && (
            <div className="space-y-4">
              {/* Skeleton */}
              <div className="h-4 bg-surface-2 rounded w-3/4 animate-pulse" />
              <div className="h-4 bg-surface-2 rounded w-1/2 animate-pulse" />
              <div className="h-32 bg-surface-2 rounded animate-pulse mt-6" />
              <div className="h-4 bg-surface-2 rounded w-5/6 animate-pulse" />
              <div className="h-4 bg-surface-2 rounded w-2/3 animate-pulse" />
            </div>
          )}

          {error && (
            <div className="text-red text-sm bg-red/10 border border-red/20 rounded-lg px-4 py-3">
              {error}
            </div>
          )}

          {evidence && !loading && (
            <>
              {evidence.type === "document" && (
                <DocumentView evidence={evidence as DocumentEvidence} />
              )}
              {evidence.type === "dataset" && (
                <DatasetView evidence={evidence as DatasetEvidence} />
              )}
              {evidence.type === "pid_drawing" && (
                <PidView evidence={evidence as PidEvidence} />
              )}
            </>
          )}
        </div>
      </div>
    </>
  );
}

// ─── Document Evidence ──────────────────────────────────────────────

function DocumentView({ evidence }: { evidence: DocumentEvidence }) {
  return (
    <div className="space-y-6">
      {/* Metadata */}
      <div className="space-y-2">
        <h4 className="font-[family-name:var(--font-mono)] text-text text-sm font-medium">
          {evidence.filename}
        </h4>
        <div className="flex items-center gap-3 text-text-3 text-xs font-[family-name:var(--font-mono)]">
          {evidence.page && <span>Page {evidence.page}</span>}
        </div>
      </div>

      {/* Excerpt */}
      <div className="bg-surface-2 border border-border rounded-lg p-5">
        <p className="text-xs text-text-3 uppercase tracking-wider mb-3">Excerpt</p>
        <p className="text-text text-sm leading-relaxed">
          {evidence.excerpt}
        </p>
      </div>

      {/* Source link */}
      {evidence.view_url && (
        <a
          href={evidence.view_url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-teal text-sm hover:text-accent transition-colors flex items-center gap-2"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
            <polyline points="15 3 21 3 21 9" />
            <line x1="10" y1="14" x2="21" y2="3" />
          </svg>
          View original document
        </a>
      )}
    </div>
  );
}

// ─── Dataset Evidence ───────────────────────────────────────────────

function DatasetView({ evidence }: { evidence: DatasetEvidence }) {
  return (
    <div className="space-y-6">
      <h4 className="font-[family-name:var(--font-mono)] text-text text-sm font-medium">
        Dataset Evidence
      </h4>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border">
              <th className="text-left py-2.5 px-3 text-text-3 text-xs font-medium font-[family-name:var(--font-mono)]">
                Timestamp
              </th>
              <th className="text-left py-2.5 px-3 text-text-3 text-xs font-medium font-[family-name:var(--font-mono)]">
                Equipment
              </th>
              <th className="text-left py-2.5 px-3 text-text-3 text-xs font-medium font-[family-name:var(--font-mono)]">
                Metric
              </th>
              <th className="text-right py-2.5 px-3 text-text-3 text-xs font-medium font-[family-name:var(--font-mono)]">
                Value
              </th>
              <th className="text-left py-2.5 px-3 text-text-3 text-xs font-medium font-[family-name:var(--font-mono)]">
                Unit
              </th>
            </tr>
          </thead>
          <tbody>
            {evidence.rows.map((row, i) => (
              <tr
                key={i}
                className="border-b border-border/50 hover:bg-teal/5 transition-colors"
              >
                <td className="py-2.5 px-3 font-[family-name:var(--font-mono)] text-text-2 text-xs">
                  {row.timestamp}
                </td>
                <td className="py-2.5 px-3 font-[family-name:var(--font-mono)] text-text text-xs">
                  {row.equipment_id}
                </td>
                <td className="py-2.5 px-3 text-text-2 text-xs">{row.metric}</td>
                <td className="py-2.5 px-3 font-[family-name:var(--font-mono)] text-accent text-xs text-right font-medium">
                  {row.value}
                </td>
                <td className="py-2.5 px-3 font-[family-name:var(--font-mono)] text-text-3 text-xs">
                  {row.unit}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ─── P&ID Evidence ──────────────────────────────────────────────────

function PidView({ evidence }: { evidence: PidEvidence }) {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h4 className="font-[family-name:var(--font-mono)] text-text text-sm font-medium">
          {evidence.filename}
        </h4>
        <span className="text-[11px] font-[family-name:var(--font-mono)] bg-teal/10 text-teal border border-teal/20 px-2 py-0.5 rounded-full">
          Qwen2.5-VL Grounded
        </span>
      </div>

      {/* Visual Description from VLM */}
      {evidence.visual_description && (
        <div className="bg-surface-2 border border-border rounded-lg p-4 space-y-1.5">
          <p className="text-xs text-text-3 uppercase tracking-wider font-semibold">Visual Inspection Observation</p>
          <p className="text-sm text-text-2 leading-relaxed">
            {evidence.visual_description}
          </p>
        </div>
      )}

      {/* Highlighted component */}
      <div className="bg-surface-2 border border-border rounded-lg p-5 space-y-3">
        <div className="flex items-center justify-between">
          <p className="text-xs text-text-3 uppercase tracking-wider">Highlighted Component</p>
          {evidence.bounding_box && (
            <span className="text-[10px] font-[family-name:var(--font-mono)] text-text-3">
              Box: [{evidence.bounding_box.join(", ")}]
            </span>
          )}
        </div>
        <p className="font-[family-name:var(--font-mono)] text-accent text-lg font-semibold">
          {evidence.highlighted_component}
        </p>
        {evidence.connections.length > 0 && (
          <div>
            <p className="text-xs text-text-3 mb-2">Connected to:</p>
            <div className="flex flex-wrap gap-2">
              {evidence.connections.map((conn) => (
                <span
                  key={conn}
                  className="font-[family-name:var(--font-mono)] text-xs bg-surface-3 border border-border
                             text-text-2 px-2.5 py-1 rounded-md"
                >
                  {conn}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Diagram Preview */}
      {evidence.view_url && (
        <div className="space-y-2">
          <p className="text-xs text-text-3 uppercase tracking-wider">Schematic Preview</p>
          <div className="rounded-lg overflow-hidden border border-border bg-white p-2">
            <img
              src={evidence.view_url}
              alt="P&ID Diagram"
              className="w-full h-auto object-contain rounded"
              onError={(e) => {
                (e.target as HTMLElement).style.display = "none";
              }}
            />
          </div>
          <a
            href={evidence.view_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-teal text-sm hover:text-accent transition-colors inline-flex items-center gap-2 pt-1"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
              <polyline points="15 3 21 3 21 9" />
              <line x1="10" y1="14" x2="21" y2="3" />
            </svg>
            Open full diagram in new tab
          </a>
        </div>
      )}
    </div>
  );
}
