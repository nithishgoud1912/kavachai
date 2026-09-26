"use client";
import React, { use, useEffect, useState } from "react";
import AppShell from "@/app/components/AppShell";
import { getStoredDocument, getStoredChunks, type StoredDocument, type StoredChunk } from "@/app/services/api";
export default function DocumentDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [document, setDocument] = useState<StoredDocument | null>(null);
  const [chunks, setChunks] = useState<StoredChunk[]>([]);
  const [offset, setOffset] = useState(0);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    let active = true;
    Promise.all([getStoredDocument(id), getStoredChunks(id, offset)]).then(([doc, data]) => {
      if (active) { setDocument(doc); setChunks(data.chunks); setTotal(data.total); setError(null); }
    }).catch(e => { if (active) { setDocument(null); setChunks([]); setError(e instanceof Error ? e.message : "Document unavailable"); } });
    return () => { active = false; };
  }, [id, offset]);
  return <AppShell title={document?.filename ?? "Document details"} subtitle="Stored source and extraction evidence" breadcrumbs={[{ label: "Knowledge Base", href: "/knowledge-base" }, { label: "Document" }]}>
    <div className="space-y-5 max-w-5xl mx-auto">
      {error && <p role="alert">{error}</p>}
      {!error && !document && <p>Loading document…</p>}
      {document && <><div className="p-5 bg-surface border border-border rounded-xl space-y-2">
        <p>Status: {document.status} · Pages/sheets: {document.pages} · Stored chunks: {document.chunks}</p>
        <p>Source: {document.source_id} · Scope: {document.department_scope ?? "Unspecified"}</p>
        <p>Ingested: {new Date(document.ingested_at).toLocaleString()}</p>
        <a className="text-accent underline" href={`/api/v1/files/${encodeURIComponent(document.source_id)}/raw`}>Open original source</a>
      </div>
      <p>Extraction metadata below comes from stored chunks. Older records may have no recorded extraction method.</p>
      {chunks.length === 0 && <p>No stored chunks.</p>}
      {chunks.map(chunk => <article key={chunk.id} className="p-5 bg-surface border border-border rounded-xl space-y-3">
        <h2>Chunk {Number(chunk.metadata.chunk_index) + 1} · Page/sheet {String(chunk.metadata.page ?? "Unknown")}</h2>
        <p>Extraction: {String(chunk.metadata.ocr_engine ?? "Not recorded")}</p>
        <pre className="whitespace-pre-wrap break-words text-sm">{chunk.text}</pre>
        <details><summary>Source metadata</summary><pre className="whitespace-pre-wrap break-words text-xs">{JSON.stringify(chunk.metadata, null, 2)}</pre></details>
      </article>)}
      <div className="flex gap-5"><button disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - 50))}>Previous</button><span>{total === 0 ? 0 : offset + 1}–{Math.min(offset + chunks.length, total)} of {total}</span><button disabled={offset + chunks.length >= total} onClick={() => setOffset(offset + 50)}>Next</button></div></>}
    </div>
  </AppShell>;
}
