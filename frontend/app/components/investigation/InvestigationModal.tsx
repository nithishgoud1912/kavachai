"use client";

import { useState, useRef, ChangeEvent, FormEvent } from "react";
import { useSession } from "@/app/hooks/useSession";
import { createInvestigation, uploadInvestigationFiles } from "@/app/services/api";
import type { AttachmentItem, Investigation } from "@/app/types";

interface InvestigationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onInvestigationCreated?: (investigation: Investigation) => void;
}

export default function InvestigationModal({
  isOpen,
  onClose,
  onInvestigationCreated,
}: InvestigationModalProps) {
  const { session } = useSession();
  const [query, setQuery] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [paths, setPaths] = useState<string[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const folderInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  function handleFilesSelect(e: ChangeEvent<HTMLInputElement>) {
    if (!e.target.files || e.target.files.length === 0) return;
    const selected = Array.from(e.target.files);
    const newPaths = selected.map(
      (f) => (f as unknown as { webkitRelativePath?: string }).webkitRelativePath || f.name
    );
    setFiles((prev) => [...prev, ...selected]);
    setPaths((prev) => [...prev, ...newPaths]);
    e.target.value = "";
  }

  function handleFolderSelect(e: ChangeEvent<HTMLInputElement>) {
    if (!e.target.files || e.target.files.length === 0) return;
    const selected = Array.from(e.target.files);
    const newPaths = selected.map(
      (f) => (f as unknown as { webkitRelativePath?: string }).webkitRelativePath || f.name
    );
    setFiles((prev) => [...prev, ...selected]);
    setPaths((prev) => [...prev, ...newPaths]);
    e.target.value = "";
  }

  function removeFile(index: number) {
    setFiles((prev) => prev.filter((_, i) => i !== index));
    setPaths((prev) => prev.filter((_, i) => i !== index));
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!query.trim() || !session) return;

    setSubmitting(true);
    setError(null);

    try {
      let attachments: AttachmentItem[] | undefined;
      if (files.length > 0) {
        attachments = await uploadInvestigationFiles(files, paths);
      }

      const res = await createInvestigation(query.trim(), session.session_id, attachments);
      onInvestigationCreated?.(res);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start investigation");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        backgroundColor: "rgba(0, 0, 0, 0.7)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 1000,
        padding: "16px",
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: "var(--color-surface, #1e2025)",
          border: "1px solid var(--color-border, #2d3139)",
          borderRadius: "16px",
          width: "100%",
          maxWidth: "580px",
          overflow: "hidden",
          boxShadow: "0 20px 50px rgba(0,0,0,0.5)",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div
          style={{
            padding: "20px 24px",
            borderBottom: "1px solid var(--color-border)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <h3 style={{ fontSize: "1.125rem", fontWeight: 600, color: "var(--color-text)" }}>
            🔍 Deep Investigation
          </h3>
          <button
            onClick={onClose}
            style={{
              background: "none",
              border: "none",
              color: "var(--color-text-3)",
              fontSize: "1.25rem",
              cursor: "pointer",
            }}
          >
            ✕
          </button>
        </div>

        <form onSubmit={handleSubmit} style={{ padding: "24px" }}>
          <label
            style={{
              display: "block",
              fontSize: "0.8125rem",
              fontWeight: 500,
              color: "var(--color-text-2)",
              marginBottom: "8px",
            }}
          >
            Investigation Target / Incident Query
          </label>
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g. Investigate Pump P-102 vibration velocity anomalies and bearing temperature spikes."
            rows={3}
            style={{
              width: "100%",
              background: "var(--color-surface-2, #141619)",
              border: "1px solid var(--color-border)",
              borderRadius: "10px",
              padding: "12px 14px",
              color: "var(--color-text)",
              fontSize: "0.875rem",
              resize: "none",
              outline: "none",
              marginBottom: "16px",
            }}
          />

          {/* Selected files chips */}
          {files.length > 0 && (
            <div style={{ marginBottom: "16px" }}>
              <div
                style={{
                  fontSize: "0.75rem",
                  color: "var(--color-text-3)",
                  marginBottom: "6px",
                }}
              >
                Attached Files & Folders ({files.length}):
              </div>
              <div
                style={{
                  display: "flex",
                  flexWrap: "wrap",
                  gap: "6px",
                  maxHeight: "120px",
                  overflowY: "auto",
                }}
              >
                {files.map((file, i) => (
                  <span
                    key={i}
                    className="attachment-chip"
                    title={paths[i] || file.name}
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "6px",
                      fontSize: "0.75rem",
                      background: "rgba(255,255,255,0.06)",
                      padding: "4px 8px",
                      borderRadius: "6px",
                      border: "1px solid var(--color-border)",
                    }}
                  >
                    <span>{paths[i]?.includes("/") ? "📁" : "📄"}</span>
                    <span
                      style={{
                        maxWidth: "180px",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {paths[i] || file.name}
                    </span>
                    <button
                      type="button"
                      onClick={() => removeFile(i)}
                      style={{
                        background: "none",
                        border: "none",
                        color: "inherit",
                        opacity: 0.7,
                        cursor: "pointer",
                        padding: "0 2px",
                      }}
                    >
                      ✕
                    </button>
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Hidden inputs */}
          <input
            ref={fileInputRef}
            type="file"
            multiple
            onChange={handleFilesSelect}
            style={{ display: "none" }}
          />
          <input
            ref={folderInputRef}
            type="file"
            {...{ webkitdirectory: "", directory: "", multiple: true }}
            onChange={handleFolderSelect}
            style={{ display: "none" }}
          />

          {error && (
            <div
              style={{
                marginBottom: "16px",
                padding: "10px 12px",
                background: "rgba(186, 56, 56, 0.1)",
                border: "1px solid rgba(186, 56, 56, 0.3)",
                borderRadius: "8px",
                fontSize: "0.8125rem",
                color: "var(--color-red)",
              }}
            >
              {error}
            </div>
          )}

          {/* Buttons bar */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              paddingTop: "12px",
              borderTop: "1px solid var(--color-border)",
            }}
          >
            <div style={{ display: "flex", gap: "8px" }}>
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                style={{
                  background: "var(--color-surface-2, rgba(255,255,255,0.06))",
                  color: "var(--color-text-2)",
                  border: "1px solid var(--color-border)",
                  borderRadius: "8px",
                  fontSize: "0.75rem",
                  padding: "6px 12px",
                  cursor: "pointer",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "6px",
                }}
              >
                📎 Attach Files
              </button>
              <button
                type="button"
                onClick={() => folderInputRef.current?.click()}
                style={{
                  background: "var(--color-surface-2, rgba(255,255,255,0.06))",
                  color: "var(--color-text-2)",
                  border: "1px solid var(--color-border)",
                  borderRadius: "8px",
                  fontSize: "0.75rem",
                  padding: "6px 12px",
                  cursor: "pointer",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "6px",
                }}
              >
                📁 Attach Folder
              </button>
            </div>

            <div style={{ display: "flex", gap: "8px" }}>
              <button
                type="button"
                onClick={onClose}
                style={{
                  background: "none",
                  border: "1px solid var(--color-border)",
                  color: "var(--color-text-3)",
                  borderRadius: "8px",
                  padding: "8px 14px",
                  fontSize: "0.8125rem",
                  cursor: "pointer",
                }}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={!query.trim() || submitting}
                style={{
                  background: "var(--color-accent)",
                  color: "#faf8f5",
                  border: "none",
                  borderRadius: "8px",
                  padding: "8px 18px",
                  fontSize: "0.8125rem",
                  fontWeight: 600,
                  cursor: "pointer",
                  opacity: !query.trim() || submitting ? 0.5 : 1,
                }}
              >
                {submitting ? "Starting…" : "Start Investigation"}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
