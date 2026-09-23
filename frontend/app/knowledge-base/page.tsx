"use client";

import React, { useState } from "react";
import AppShell from "@/app/components/AppShell";
import KBSummaryHeader from "@/app/components/KBSummaryHeader";
import IngestionPipelineVisualizer from "@/app/components/IngestionPipelineVisualizer";
import DocumentTable, { type KBDocumentRow } from "@/app/components/DocumentTable";
import EquipmentGraphPanel from "@/app/components/EquipmentGraphPanel";
import AttachmentDropzone from "@/app/components/AttachmentDropzone";
import type { AttachmentItem } from "@/app/types";

const INITIAL_DOCS: KBDocumentRow[] = [
  {
    id: "doc-1",
    filename: "MRPL_CDU2_Operating_Manual_Rev4.pdf",
    type: "document",
    department: "OPERATIONS",
    pageCount: 148,
    chunkCount: 620,
    ocrTier: "Tier 1 (Native Stream)",
    status: "indexed",
    ingestedAt: "2026-09-20T08:30:00Z",
  },
  {
    id: "doc-2",
    filename: "P-204A_Vibration_Spectra_Apr2026.pdf",
    type: "document",
    department: "MAINTENANCE",
    pageCount: 4,
    chunkCount: 28,
    ocrTier: "Tier 3 (Tesseract 5.3)",
    status: "indexed",
    ingestedAt: "2026-09-23T10:10:00Z",
  },
  {
    id: "doc-3",
    filename: "MRPL-CDU2-PID-004_Piping_Diagram.pdf",
    type: "pid",
    department: "ENGINEERING",
    pageCount: 1,
    chunkCount: 12,
    ocrTier: "Tier 4 (VLM Multimodal)",
    status: "indexed",
    ingestedAt: "2026-09-22T14:15:00Z",
  },
  {
    id: "doc-4",
    filename: "ISO_10816-3_Vibration_Standards.pdf",
    type: "document",
    department: "SAFETY (HSE)",
    pageCount: 36,
    chunkCount: 180,
    ocrTier: "Tier 1 (Native Stream)",
    status: "indexed",
    ingestedAt: "2026-09-18T11:00:00Z",
  },
  {
    id: "doc-5",
    filename: "Scanned_Handwritten_Log_ShiftB.pdf",
    type: "image",
    department: "OPERATIONS",
    pageCount: 2,
    chunkCount: 14,
    ocrTier: "Tier 4 (Qwen2.5-VL)",
    status: "ocr_processing",
    ingestedAt: "2026-09-23T12:00:00Z",
  },
];

export default function KnowledgeBasePage() {
  const [documents, setDocuments] = useState<KBDocumentRow[]>(INITIAL_DOCS);
  const [uploadingFiles, setUploadingFiles] = useState<AttachmentItem[]>([]);
  const [activeTab, setActiveTab] = useState<"docs" | "pipeline" | "pid">("docs");

  const handleUpload = (newItems: AttachmentItem[]) => {
    setUploadingFiles(newItems);
    // Simulate instantaneous local ingestion
    if (newItems.length > 0) {
      const added: KBDocumentRow[] = newItems.map((item, idx) => ({
        id: `doc-${Date.now()}-${idx}`,
        filename: item.filename,
        type: item.type === "image" ? "image" : "document",
        department: "REFINERY",
        pageCount: 1,
        chunkCount: 8,
        ocrTier: "Tier 2 (Density Verified)",
        status: "indexed",
        ingestedAt: new Date().toISOString(),
      }));
      setDocuments((prev) => [...added, ...prev]);
    }
  };

  return (
    <AppShell
      title="Knowledge Base Connector"
      subtitle="Confidential On-Premise SOPs & P&IDs"
      breadcrumbs={[
        { label: "Workspace", href: "/workspace" },
        { label: "Knowledge Base" },
      ]}
    >
      <div className="space-y-6 max-w-7xl mx-auto pb-12">
        {/* Aggregate Header */}
        <KBSummaryHeader
          totalDocs={documents.length}
          totalChunks={documents.reduce((acc, d) => acc + d.chunkCount, 0)}
        />

        {/* View Switcher Tabs */}
        <div className="flex items-center gap-2 border-b border-border pb-2">
          <button
            onClick={() => setActiveTab("docs")}
            className={`px-4 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
              activeTab === "docs"
                ? "bg-accent text-white shadow-xs"
                : "bg-surface text-text-2 hover:bg-surface-2 border border-border"
            }`}
          >
            📚 Ingested Documents ({documents.length})
          </button>
          <button
            onClick={() => setActiveTab("pipeline")}
            className={`px-4 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
              activeTab === "pipeline"
                ? "bg-accent text-white shadow-xs"
                : "bg-surface text-text-2 hover:bg-surface-2 border border-border"
            }`}
          >
            ⚙️ 4-Tier OCR Pipeline
          </button>
          <button
            onClick={() => setActiveTab("pid")}
            className={`px-4 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
              activeTab === "pid"
                ? "bg-accent text-white shadow-xs"
                : "bg-surface text-text-2 hover:bg-surface-2 border border-border"
            }`}
          >
            📐 P&ID Topology Visualizer
          </button>
        </div>

        {/* Ingestion Dropzone */}
        <div className="p-4 bg-surface border border-border rounded-2xl shadow-xs space-y-2">
          <span className="text-xs font-mono font-semibold uppercase text-text-3">
            Local Bulk Ingestion Dropzone
          </span>
          <AttachmentDropzone attachments={uploadingFiles} onChange={handleUpload} />
        </div>

        {/* Tab 1: Documents Table */}
        {activeTab === "docs" && <DocumentTable documents={documents} />}

        {/* Tab 2: 4-Tier OCR Visualizer */}
        {activeTab === "pipeline" && <IngestionPipelineVisualizer currentTier={3} />}

        {/* Tab 3: P&ID Topology */}
        {activeTab === "pid" && <EquipmentGraphPanel />}
      </div>
    </AppShell>
  );
}
