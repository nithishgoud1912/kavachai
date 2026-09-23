"use client";

import React from "react";
import Link from "next/link";
import Badge from "./Badge";

export interface KBDocumentRow {
  id: string;
  filename: string;
  type: string;
  department: string;
  pageCount: number;
  chunkCount: number;
  ocrTier: string;
  status: "indexed" | "ocr_processing" | "embedding" | "queued" | "failed";
  ingestedAt: string;
}

interface DocumentTableProps {
  documents: KBDocumentRow[];
  onSelectDoc?: (doc: KBDocumentRow) => void;
  className?: string;
}

export default function DocumentTable({
  documents,
  onSelectDoc,
  className = "",
}: DocumentTableProps) {
  return (
    <div className={`bg-surface border border-border rounded-2xl overflow-hidden shadow-xs space-y-3 p-5 ${className}`}>
      <div className="flex items-center justify-between pb-2 border-b border-border-subtle">
        <div>
          <h3 className="font-serif font-bold text-base text-text">Ingested Document Repository</h3>
          <p className="text-xs text-text-3 font-mono">
            Full-text extracted and chunked locally with multi-tier OCR pipeline
          </p>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs font-sans border-collapse">
          <thead>
            <tr className="border-b border-border text-text-3 font-mono text-[11px] uppercase">
              <th className="pb-2.5">Document Name</th>
              <th className="pb-2.5">Scope</th>
              <th className="pb-2.5">Pages</th>
              <th className="pb-2.5">Chunks</th>
              <th className="pb-2.5">OCR Extraction Tier</th>
              <th className="pb-2.5">Status</th>
              <th className="pb-2.5 text-right">Detail</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/60">
            {documents.map((doc) => (
              <tr key={doc.id} className="hover:bg-bg-base/70 transition-colors">
                <td className="py-3 font-medium text-text">
                  <div className="flex items-center gap-2">
                    <span className="text-base">
                      {doc.type === "pid" ? "📐" : doc.type === "image" ? "🖼️" : "📄"}
                    </span>
                    <span className="font-mono font-semibold text-xs truncate max-w-[220px]">
                      {doc.filename}
                    </span>
                  </div>
                </td>
                <td className="py-3 font-mono text-[11px] text-text-2">
                  <span className="px-2 py-0.5 rounded bg-surface-2 border border-border">
                    {doc.department}
                  </span>
                </td>
                <td className="py-3 font-mono text-text-2">{doc.pageCount}</td>
                <td className="py-3 font-mono text-text-2">{doc.chunkCount}</td>
                <td className="py-3 font-mono text-[11px] text-text-2">
                  <span className="px-2 py-0.5 rounded bg-surface-2 border border-border">
                    {doc.ocrTier}
                  </span>
                </td>
                <td className="py-3">
                  <Badge
                    variant={doc.status === "indexed" ? "complete" : doc.status === "ocr_processing" ? "running" : "queued"}
                    label={doc.status.toUpperCase()}
                    size="sm"
                  />
                </td>
                <td className="py-3 text-right">
                  <Link
                    href={`/knowledge-base/document/${doc.id}`}
                    className="px-2.5 py-1 rounded-lg bg-surface-2 hover:bg-surface border border-border text-[11px] text-text font-medium transition-colors"
                  >
                    Inspect
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
