"use client";
import React, { useState, useEffect, useCallback } from "react";
import AppShell from "@/app/components/AppShell";
import KBSummaryHeader from "@/app/components/KBSummaryHeader";
import DocumentTable, { type KBDocumentRow } from "@/app/components/DocumentTable";
import EquipmentGraphPanel from "@/app/components/EquipmentGraphPanel";
import AttachmentDropzone from "@/app/components/AttachmentDropzone";
import { listStoredDocuments, type StoredDocument } from "@/app/services/api";
import type { AttachmentItem } from "@/app/types";

export default function KnowledgeBasePage() {
  const [documents, setDocuments] = useState<StoredDocument[] | null>(null);
  const [attachments, setAttachments] = useState<AttachmentItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [showGraph, setShowGraph] = useState(false);
  const refresh = useCallback(async () => {
    try { const data = await listStoredDocuments(); setDocuments(data.documents); setError(null); }
    catch (e) { setDocuments(null); setError(e instanceof Error ? e.message : "Document service unavailable"); }
  }, []);
  useEffect(() => { const timer = setTimeout(() => void refresh(), 0); return () => clearTimeout(timer); }, [refresh]);
  const rows: KBDocumentRow[] = (documents ?? []).map(d => ({
    id: d.document_id, filename: d.filename, type: d.document_type, department: d.department_scope ?? "Unspecified",
    pageCount: d.pages, chunkCount: d.chunks, ocrTier: "See stored chunk metadata",
    status: d.status === "ready" ? "indexed" : d.status === "failed" ? "failed" : "ocr_processing", ingestedAt: d.ingested_at,
  }));
  return <AppShell title="Knowledge Base Connector" subtitle="Authorized local documents" breadcrumbs={[{ label: "Workspace", href: "/workspace" }, { label: "Knowledge Base" }]}>
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      <KBSummaryHeader totalDocs={documents?.length} totalChunks={documents?.reduce((sum, d) => sum + d.chunks, 0)} totalPid={documents?.filter(d => d.document_type === "pid_drawing").length} />
      <div className="flex gap-4"><button onClick={() => void refresh()}>Refresh documents</button><button onClick={() => setShowGraph(!showGraph)}>{showGraph ? "Show documents" : "Show equipment metadata graph"}</button></div>
      <AttachmentDropzone attachments={attachments} onChange={items => { setAttachments(items); void refresh(); }} />
      {error && <p role="alert" className="text-red">{error}</p>}
      {!documents && !error && <p>Loading authorized documents…</p>}
      {documents?.length === 0 && <p>No documents are available to this account. Upload a file to begin.</p>}
      {documents && !showGraph && <DocumentTable documents={rows} />}
      {showGraph && <EquipmentGraphPanel />}
    </div>
  </AppShell>;
}
