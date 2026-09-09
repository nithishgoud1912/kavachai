"use client";

import { useState, useEffect, useRef, FormEvent, DragEvent } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/app/components/Sidebar";
import ChatWindow from "@/app/components/ChatWindow";
import SuggestedQuestions from "@/app/components/SuggestedQuestions";
import { useSession } from "@/app/hooks/useSession";
import {
  createInvestigation,
  uploadInvestigationFiles,
} from "@/app/services/api";

type DashboardView = "chat" | "investigation";

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function getFileIcon(filename: string): string {
  const ext = filename.split(".").pop()?.toLowerCase();
  if (ext === "pdf") return "📕";
  if (["csv", "xlsx", "xls"].includes(ext || "")) return "📊";
  if (["png", "jpg", "jpeg", "webp", "svg"].includes(ext || "")) return "🖼️";
  if (["doc", "docx", "txt", "md"].includes(ext || "")) return "📄";
  return "📁";
}

export default function Workspace() {
  const router = useRouter();
  const { session, isAuthenticated, isLoading: sessionLoading } = useSession();
  const [activeView, setActiveView] = useState<DashboardView>("chat");
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);

  // Investigation mode state
  const [query, setQuery] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Attachments state
  const [attachedFiles, setAttachedFiles] = useState<File[]>([]);
  const [attachedPaths, setAttachedPaths] = useState<string[]>([]);
  const [isDragging, setIsDragging] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const folderInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!sessionLoading && !isAuthenticated) {
      router.push("/");
    }
  }, [sessionLoading, isAuthenticated, router]);

  if (sessionLoading) {
    return (
      <div className="dashboard-layout">
        <div className="dashboard-sidebar animate-pulse" style={{ background: "var(--color-surface)" }}>
          <div style={{ padding: "16px" }}>
            <div style={{ height: "28px", background: "var(--color-surface-2)", borderRadius: "8px", marginBottom: "16px" }} />
            <div style={{ height: "40px", background: "var(--color-surface-2)", borderRadius: "10px", marginBottom: "8px" }} />
            <div style={{ height: "40px", background: "var(--color-surface-2)", borderRadius: "10px" }} />
          </div>
        </div>
        <div className="dashboard-main" style={{ alignItems: "center", justifyContent: "center" }}>
          <div className="animate-pulse" style={{ width: "60%", maxWidth: "500px" }}>
            <div style={{ height: "32px", background: "var(--color-surface-2)", borderRadius: "8px", marginBottom: "16px" }} />
            <div style={{ height: "120px", background: "var(--color-surface-2)", borderRadius: "12px" }} />
          </div>
        </div>
      </div>
    );
  }

  if (!isAuthenticated || !session) return null;

  function handleNewChat() {
    setActiveView("chat");
    setActiveConversationId(null);
  }

  function handleNewInvestigation() {
    setActiveView("investigation");
    setActiveConversationId(null);
    setQuery("");
    setError(null);
    setUploadStatus(null);
  }

  function handleSelectConversation(id: string) {
    setActiveView("chat");
    setActiveConversationId(id);
  }

  function handleConversationCreated(id: string) {
    setActiveConversationId(id);
  }

  function handleFilesAdded(newFiles: FileList | File[]) {
    const fileArray = Array.from(newFiles);
    if (fileArray.length === 0) return;

    const newPaths: string[] = [];
    const filteredFiles: File[] = [];

    fileArray.forEach((file) => {
      const isDuplicate = attachedFiles.some(
        (existing) => existing.name === file.name && existing.size === file.size
      );
      if (!isDuplicate) {
        filteredFiles.push(file);
        const relPath = (file as any).webkitRelativePath || file.name;
        newPaths.push(relPath);
      }
    });

    if (filteredFiles.length > 0) {
      setAttachedFiles((prev) => [...prev, ...filteredFiles]);
      setAttachedPaths((prev) => [...prev, ...newPaths]);
    }
  }

  function handleRemoveFile(index: number) {
    setAttachedFiles((prev) => prev.filter((_, i) => i !== index));
    setAttachedPaths((prev) => prev.filter((_, i) => i !== index));
  }

  function handleClearAllFiles() {
    setAttachedFiles([]);
    setAttachedPaths([]);
    if (fileInputRef.current) fileInputRef.current.value = "";
    if (folderInputRef.current) folderInputRef.current.value = "";
  }

  function handleDragOver(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }

  function handleDragLeave(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }

  function handleDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFilesAdded(e.dataTransfer.files);
    }
  }

  async function handleInvestigationSubmit(e?: FormEvent) {
    if (e) e.preventDefault();
    if (!query.trim() || !session || submitting) return;

    setSubmitting(true);
    setError(null);
    setUploadStatus(null);

    try {
      let attachmentsPayload: any[] = [];

      if (attachedFiles.length > 0) {
        setUploadStatus(`Indexing ${attachedFiles.length} uploaded file${attachedFiles.length > 1 ? "s" : ""} into vector store...`);
        const uploaded = await uploadInvestigationFiles(attachedFiles, attachedPaths);
        attachmentsPayload = (uploaded || []).map((f: any) => ({
          filename: f.filename,
          url: f.url,
          type: f.type,
          extracted_text: f.extracted_text_preview || "",
          source_id: f.source_id,
          path: f.path,
          size: f.size,
        }));
      }

      setUploadStatus("Initializing multi-agent pipeline...");
      const investigation = await createInvestigation(
        query.trim(),
        session.session_id,
        attachmentsPayload
      );
      router.push(`/investigation/${investigation.investigation_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start investigation");
      setSubmitting(false);
      setUploadStatus(null);
    }
  }

  const totalAttachmentSize = attachedFiles.reduce((sum, f) => sum + f.size, 0);

  return (
    <div className="dashboard-layout">
      {/* ─── Sidebar ───────────────────────────────────────────────── */}
      <Sidebar
        activeConversationId={activeConversationId}
        onNewChat={handleNewChat}
        onNewInvestigation={handleNewInvestigation}
        onSelectConversation={handleSelectConversation}
      />

      {/* ─── Main Content ──────────────────────────────────────────── */}
      <div className="dashboard-main">
        {/* ─── Top Bar ─────────────────────────────────────────────── */}
        <div
          style={{
            padding: "12px 24px",
            borderBottom: "1px solid var(--color-border)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            background: "var(--color-bg)",
            flexShrink: 0,
          }}
        >
          <div className="mode-tabs" style={{ width: "fit-content" }}>
            <button
              className={`mode-tab ${activeView === "chat" ? "active" : ""}`}
              onClick={handleNewChat}
            >
              💬 AI Chat
            </button>
            <button
              className={`mode-tab ${activeView === "investigation" ? "active" : ""}`}
              onClick={handleNewInvestigation}
            >
              🔍 Deep Investigation
            </button>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <span style={{ fontSize: "0.8125rem", color: "var(--color-text-2)" }}>
              <span style={{ color: "var(--color-text)" }}>{session.name}</span>
              <span style={{ color: "var(--color-text-3)", margin: "0 6px" }}>·</span>
              <span
                className="font-[family-name:var(--font-mono)]"
                style={{ fontSize: "0.75rem", color: "var(--color-text-3)" }}
              >
                {session.department}
              </span>
            </span>
            <button
              onClick={() => router.push("/audit")}
              style={{
                fontSize: "0.75rem",
                color: "var(--color-text-3)",
                background: "none",
                border: "1px solid var(--color-border)",
                borderRadius: "8px",
                padding: "5px 10px",
                cursor: "pointer",
                transition: "all 0.15s ease",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = "var(--color-teal)";
                e.currentTarget.style.color = "var(--color-teal)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = "var(--color-border)";
                e.currentTarget.style.color = "var(--color-text-3)";
              }}
            >
              Audit Log
            </button>
          </div>
        </div>

        {/* ─── Content Area ────────────────────────────────────────── */}
        {activeView === "chat" ? (
          <ChatWindow
            conversationId={activeConversationId}
            type="general"
            onConversationCreated={handleConversationCreated}
          />
        ) : (
          /* ─── Investigation Mode ─────────────────────────────────── */
          <div
            style={{
              flex: 1,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              padding: "40px 24px",
              overflowY: "auto",
            }}
          >
            <div style={{ width: "100%", maxWidth: "680px" }}>
              <div style={{ textAlign: "center", marginBottom: "28px" }} className="hero-fade-in-up hero-stagger-1">
                <h2
                  className="font-[family-name:var(--font-playfair)]"
                  style={{
                    fontSize: "1.75rem",
                    fontWeight: 500,
                    color: "var(--color-text)",
                    letterSpacing: "-0.02em",
                    marginBottom: "8px",
                  }}
                >
                  What do you want to investigate?
                </h2>
                <p style={{ fontSize: "0.875rem", color: "var(--color-text-3)", maxWidth: "520px", margin: "0 auto" }}>
                  Define your objective and attach relevant inspection reports, telemetry CSVs, or entire asset folders for multi-agent evidence synthesis.
                </p>
              </div>

              <form
                onSubmit={handleInvestigationSubmit}
                className="hero-fade-in-up hero-stagger-2"
                style={{ position: "relative" }}
              >
                <div
                  className="card-shadow card-hover"
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                  style={{
                    background: "var(--color-surface)",
                    border: isDragging
                      ? "2px dashed var(--color-accent)"
                      : "1px solid var(--color-border)",
                    borderRadius: "16px",
                    overflow: "hidden",
                    transition: "all 0.2s ease",
                    boxShadow: isDragging ? "0 0 16px rgba(184, 80, 66, 0.15)" : undefined,
                  }}
                >
                  {/* Query Textarea */}
                  <textarea
                    id="investigation-query"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Investigate Pump P-102 and determine whether its vibration exceeds ISO thresholds based on the attached documents..."
                    rows={3}
                    disabled={submitting}
                    className="font-[family-name:var(--font-mono)]"
                    style={{
                      width: "100%",
                      background: "transparent",
                      padding: "20px 24px 12px",
                      color: "var(--color-text)",
                      resize: "none",
                      border: "none",
                      outline: "none",
                      fontSize: "0.875rem",
                      lineHeight: "1.5",
                    }}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        if (query.trim() && !submitting) handleInvestigationSubmit();
                      }
                    }}
                  />

                  {/* Attached Files List */}
                  {attachedFiles.length > 0 && (
                    <div
                      style={{
                        padding: "8px 20px 14px",
                        borderTop: "1px dashed var(--color-border)",
                        background: "rgba(0, 0, 0, 0.02)",
                      }}
                    >
                      <div
                        style={{
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "space-between",
                          marginBottom: "8px",
                          fontSize: "0.75rem",
                          color: "var(--color-text-3)",
                        }}
                      >
                        <span style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                          <span>📎</span>
                          <strong>{attachedFiles.length} file{attachedFiles.length > 1 ? "s" : ""} attached</strong>
                          <span>({formatFileSize(totalAttachmentSize)})</span>
                        </span>
                        <button
                          type="button"
                          onClick={handleClearAllFiles}
                          disabled={submitting}
                          style={{
                            background: "none",
                            border: "none",
                            color: "var(--color-red)",
                            fontSize: "0.6875rem",
                            cursor: "pointer",
                            padding: "2px 6px",
                            borderRadius: "4px",
                            transition: "opacity 0.15s ease",
                          }}
                        >
                          Clear all
                        </button>
                      </div>

                      <div
                        style={{
                          display: "flex",
                          flexWrap: "wrap",
                          gap: "8px",
                          maxHeight: "130px",
                          overflowY: "auto",
                          paddingRight: "4px",
                        }}
                      >
                        {attachedFiles.map((file, idx) => {
                          const displayPath = attachedPaths[idx] || file.name;
                          return (
                            <div
                              key={`${file.name}-${idx}`}
                              style={{
                                display: "inline-flex",
                                alignItems: "center",
                                gap: "6px",
                                background: "var(--color-surface-2)",
                                border: "1px solid var(--color-border)",
                                borderRadius: "8px",
                                padding: "4px 8px",
                                fontSize: "0.75rem",
                                color: "var(--color-text)",
                                maxWidth: "260px",
                              }}
                            >
                              <span>{getFileIcon(file.name)}</span>
                              <span
                                style={{
                                  overflow: "hidden",
                                  textOverflow: "ellipsis",
                                  whiteSpace: "nowrap",
                                  direction: "rtl",
                                  textAlign: "left",
                                }}
                                title={displayPath}
                              >
                                {displayPath}
                              </span>
                              <span style={{ fontSize: "0.6875rem", color: "var(--color-text-3)", flexShrink: 0 }}>
                                {formatFileSize(file.size)}
                              </span>
                              {!submitting && (
                                <button
                                  type="button"
                                  onClick={() => handleRemoveFile(idx)}
                                  style={{
                                    background: "none",
                                    border: "none",
                                    color: "var(--color-text-3)",
                                    fontSize: "0.75rem",
                                    cursor: "pointer",
                                    padding: "0 2px",
                                    lineHeight: 1,
                                  }}
                                  onMouseEnter={(e) => (e.currentTarget.style.color = "var(--color-red)")}
                                  onMouseLeave={(e) => (e.currentTarget.style.color = "var(--color-text-3)")}
                                >
                                  ✕
                                </button>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {/* Bottom Action Bar */}
                  <div
                    style={{
                      padding: "12px 20px",
                      borderTop: "1px solid var(--color-border)",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      background: "var(--color-surface)",
                    }}
                  >
                    {/* Left: Attachment trigger buttons */}
                    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                      {/* Hidden File Input */}
                      <input
                        ref={fileInputRef}
                        type="file"
                        multiple
                        disabled={submitting}
                        onChange={(e) => {
                          if (e.target.files) handleFilesAdded(e.target.files);
                          e.target.value = "";
                        }}
                        style={{ display: "none" }}
                      />

                      {/* Hidden Folder Input */}
                      <input
                        ref={folderInputRef}
                        type="file"
                        multiple
                        disabled={submitting}
                        {...({ webkitdirectory: "", directory: "" } as any)}
                        onChange={(e) => {
                          if (e.target.files) handleFilesAdded(e.target.files);
                          e.target.value = "";
                        }}
                        style={{ display: "none" }}
                      />

                      <button
                        type="button"
                        onClick={() => fileInputRef.current?.click()}
                        disabled={submitting}
                        style={{
                          background: "var(--color-surface-2)",
                          border: "1px solid var(--color-border)",
                          color: "var(--color-text-2)",
                          fontSize: "0.75rem",
                          fontWeight: 500,
                          padding: "6px 12px",
                          borderRadius: "8px",
                          cursor: submitting ? "not-allowed" : "pointer",
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "6px",
                          transition: "all 0.15s ease",
                        }}
                        onMouseEnter={(e) => {
                          if (!submitting) {
                            e.currentTarget.style.borderColor = "var(--color-accent)";
                            e.currentTarget.style.color = "var(--color-accent)";
                          }
                        }}
                        onMouseLeave={(e) => {
                          if (!submitting) {
                            e.currentTarget.style.borderColor = "var(--color-border)";
                            e.currentTarget.style.color = "var(--color-text-2)";
                          }
                        }}
                      >
                        <span>📎</span>
                        <span>Attach Files</span>
                      </button>

                      <button
                        type="button"
                        onClick={() => folderInputRef.current?.click()}
                        disabled={submitting}
                        style={{
                          background: "var(--color-surface-2)",
                          border: "1px solid var(--color-border)",
                          color: "var(--color-text-2)",
                          fontSize: "0.75rem",
                          fontWeight: 500,
                          padding: "6px 12px",
                          borderRadius: "8px",
                          cursor: submitting ? "not-allowed" : "pointer",
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "6px",
                          transition: "all 0.15s ease",
                        }}
                        onMouseEnter={(e) => {
                          if (!submitting) {
                            e.currentTarget.style.borderColor = "var(--color-teal)";
                            e.currentTarget.style.color = "var(--color-teal)";
                          }
                        }}
                        onMouseLeave={(e) => {
                          if (!submitting) {
                            e.currentTarget.style.borderColor = "var(--color-border)";
                            e.currentTarget.style.color = "var(--color-text-2)";
                          }
                        }}
                      >
                        <span>📁</span>
                        <span>Attach Folder</span>
                      </button>
                    </div>

                    {/* Right: Submit Button */}
                    <button
                      type="submit"
                      disabled={!query.trim() || submitting}
                      style={{
                        background: "var(--color-accent)",
                        color: "#faf8f5",
                        fontWeight: 600,
                        fontSize: "0.875rem",
                        padding: "9px 20px",
                        borderRadius: "10px",
                        border: "none",
                        cursor: !query.trim() || submitting ? "not-allowed" : "pointer",
                        display: "flex",
                        alignItems: "center",
                        gap: "8px",
                        transition: "all 0.2s ease",
                        opacity: !query.trim() || submitting ? 0.4 : 1,
                      }}
                    >
                      {submitting ? (
                        <>
                          <svg className="animate-spin" width="14" height="14" viewBox="0 0 24 24" fill="none">
                            <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" opacity="0.3" />
                            <path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
                          </svg>
                          Starting…
                        </>
                      ) : (
                        <>
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <circle cx="12" cy="12" r="10" />
                            <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76" fill="currentColor" stroke="none" />
                          </svg>
                          Investigate
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </form>

              {/* Upload & Pipeline Progress Indicator */}
              {uploadStatus && (
                <div
                  className="card-shadow hero-fade-in-up"
                  style={{
                    marginTop: "16px",
                    padding: "12px 16px",
                    background: "rgba(45, 138, 110, 0.08)",
                    border: "1px solid rgba(45, 138, 110, 0.25)",
                    borderRadius: "10px",
                    fontSize: "0.8125rem",
                    color: "var(--color-teal)",
                    display: "flex",
                    alignItems: "center",
                    gap: "10px",
                  }}
                >
                  <svg className="animate-spin" width="16" height="16" viewBox="0 0 24 24" fill="none">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" opacity="0.3" />
                    <path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
                  </svg>
                  <span>{uploadStatus}</span>
                </div>
              )}

              {/* Error Banner */}
              {error && (
                <div
                  style={{
                    marginTop: "16px",
                    padding: "12px 16px",
                    background: "rgba(186, 56, 56, 0.08)",
                    border: "1px solid rgba(186, 56, 56, 0.2)",
                    borderRadius: "10px",
                    fontSize: "0.8125rem",
                    color: "var(--color-red)",
                  }}
                >
                  {error}
                </div>
              )}

              <div className="hero-fade-in-up hero-stagger-3" style={{ marginTop: "28px" }}>
                <SuggestedQuestions onSelect={(q) => setQuery(q)} />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
