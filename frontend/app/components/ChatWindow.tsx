"use client";

import { useState, useEffect, useRef, useCallback, FormEvent, DragEvent } from "react";
import { useSession } from "@/app/hooks/useSession";
import {
  createConversation,
  getConversation,
  sendChatMessage,
  uploadChatFile,
  uploadChatFilesBatch,
} from "@/app/services/api";
import type { ChatMessage, ChatAttachment } from "@/app/types";

interface ChatWindowProps {
  conversationId: string | null;
  type?: "general" | "report";
  investigationId?: string;
  onConversationCreated?: (id: string) => void;
  compact?: boolean;
}

import MarkdownMessage from "@/app/components/MarkdownMessage";


// ─── Suggested Chips for Empty State ──────────────────────────────────
const GENERAL_SUGGESTIONS = [
  "What are common causes of bearing failure in industrial pumps?",
  "Explain vibration analysis techniques for rotating equipment",
  "What PPE is required for confined space entry?",
  "Summarize ISO 13849 safety standards",
  "How do I perform a root cause analysis for equipment failure?",
  "What is the ISO 10816 vibration severity standard?",
];

const REPORT_SUGGESTIONS = [
  "What were the key findings?",
  "What evidence supports the conclusion?",
  "Are there any unverified findings?",
  "What maintenance actions are recommended?",
];

const ALLOWED_EXTENSIONS = new Set([
  ".pdf",
  ".txt",
  ".csv",
  ".docx",
  ".text",
  ".md",
  ".json",
  ".png",
  ".jpg",
  ".jpeg",
  ".webp",
  ".gif",
  ".svg",
]);

export default function ChatWindow({
  conversationId,
  type = "general",
  investigationId,
  onConversationCreated,
  compact = false,
}: ChatWindowProps) {
  const { session } = useSession();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [loading, setLoading] = useState(false);
  const [currentConvId, setCurrentConvId] = useState<string | null>(conversationId);
  const [attachments, setAttachments] = useState<ChatAttachment[]>([]);
  const [uploadingCount, setUploadingCount] = useState<number>(0);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const folderInputRef = useRef<HTMLInputElement>(null);

  // Sync conversationId prop — also clear attachments/errors for a fresh state
  useEffect(() => {
    setCurrentConvId(conversationId);
    setAttachments([]);
    setUploadError(null);
  }, [conversationId]);

  // Load conversation messages when conversationId changes
  useEffect(() => {
    if (!currentConvId) {
      setMessages([]);
      return;
    }

    let cancelled = false;
    async function load() {
      setLoading(true);
      try {
        const detail = await getConversation(currentConvId!);
        if (!cancelled) {
          setMessages(detail.messages);
        }
      } catch {
        // Fail silently
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, [currentConvId]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  // Auto-resize textarea
  const handleTextareaChange = useCallback((value: string) => {
    setInput(value);
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 120) + "px";
    }
  }, []);

  // ─── File Upload (Multiple files & Folders) ────────────────────────
  const handleFileUpload = useCallback(async (files: FileList | File[]) => {
    setUploadError(null);
    const rawFiles = Array.from(files);
    if (rawFiles.length === 0) return;

    // Filter out hidden/system files and validate extensions
    const validFiles = rawFiles.filter((file) => {
      if (file.name.startsWith(".") || file.name === "Thumbs.db" || file.name === "desktop.ini") {
        return false;
      }
      const dotIndex = file.name.lastIndexOf(".");
      if (dotIndex === -1) return false;
      const ext = file.name.substring(dotIndex).toLowerCase();
      return ALLOWED_EXTENSIONS.has(ext);
    });

    if (validFiles.length === 0) {
      setUploadError(
        "No supported files found. Supported formats: PDF, TXT, CSV, DOCX, MD, JSON, PNG, JPG, WEBP, GIF, SVG."
      );
      return;
    }

    const paths = validFiles.map(
      (file) => ((file as unknown as { webkitRelativePath?: string }).webkitRelativePath || file.name)
    );

    setUploadingCount(validFiles.length);

    try {
      // 1. Primary: Use batch upload
      const uploaded = await uploadChatFilesBatch(validFiles, paths);
      const newAttachments: ChatAttachment[] = uploaded.map((item) => ({
        filename: item.filename,
        url: item.url,
        type: (item.type === "image" ? "image" : "document") as "document" | "image",
        extracted_text: item.extracted_text,
        relative_path: item.relative_path,
        source_id: item.source_id,
        size: item.size,
      }));

      if (newAttachments.length > 0) {
        setAttachments((prev) => [...prev, ...newAttachments]);
      }
    } catch (err) {
      console.warn("Batch upload failed, falling back to individual upload:", err);
      // 2. Fallback: upload file-by-file
      try {
        const results = await Promise.allSettled(
          validFiles.map(async (file) => {
            const formData = new FormData();
            formData.append("file", file);
            return await uploadChatFile(formData);
          })
        );

        const newAttachments: ChatAttachment[] = [];
        let failCount = 0;

        results.forEach((res, i) => {
          if (res.status === "fulfilled") {
            const result = res.value;
            newAttachments.push({
              filename: result.filename,
              url: result.url,
              type: result.type as "document" | "image",
              extracted_text: result.extracted_text_preview || undefined,
              relative_path: paths[i],
            });
          } else {
            failCount++;
          }
        });

        if (newAttachments.length > 0) {
          setAttachments((prev) => [...prev, ...newAttachments]);
        }

        if (failCount > 0) {
          setUploadError(
            failCount === validFiles.length
              ? "Failed to upload selected file(s). Please try again."
              : `${failCount} of ${validFiles.length} file(s) could not be uploaded.`
          );
        }
      } catch (fallbackErr) {
        setUploadError(
          fallbackErr instanceof Error ? fallbackErr.message : "Failed to upload files"
        );
      }
    } finally {
      setUploadingCount(0);
    }
  }, []);

  const handleDrop = useCallback(
    (e: DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      if (e.dataTransfer.files.length > 0) {
        handleFileUpload(e.dataTransfer.files);
      }
    },
    [handleFileUpload]
  );

  const removeAttachment = useCallback((index: number) => {
    setAttachments((prev) => prev.filter((_, i) => i !== index));
  }, []);

  const clearAllAttachments = useCallback(() => {
    setAttachments([]);
  }, []);

  // ─── Send Message ─────────────────────────────────────────────────
  const handleSend = useCallback(
    async (messageText?: string) => {
      const content = (messageText || input).trim();
      if (!content || sending || !session) return;

      setSending(true);
      setInput("");
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }

      try {
        let convId = currentConvId;

        // Create conversation if needed
        if (!convId) {
          const conv = await createConversation({
            session_id: session.session_id,
            title: content.length > 60 ? content.substring(0, 60) + "…" : content,
            type,
            investigation_id: investigationId,
          });
          convId = conv.id;
          setCurrentConvId(convId);
          onConversationCreated?.(convId);

          // Reload sidebar
          const reloadSidebar = (window as unknown as Record<string, unknown>).__reloadSidebar;
          if (typeof reloadSidebar === "function") {
            (reloadSidebar as () => void)();
          }
        }

        // Optimistically add user message
        const userMsg: ChatMessage = {
          id: `temp-${Date.now()}`,
          role: "user",
          content,
          attachments: [...attachments],
          created_at: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, userMsg]);
        const currentAttachments = [...attachments];
        setAttachments([]);

        // Send to API
        const response = await sendChatMessage(convId, content, currentAttachments);

        // Add assistant response
        setMessages((prev) => [
          ...prev,
          {
            id: response.id,
            role: "assistant" as const,
            content: response.content,
            attachments: response.attachments || [],
            created_at: response.created_at,
          },
        ]);
      } catch (err) {
        console.error("Chat send error:", err);
        const errMsg =
          err instanceof Error
            ? err.message
            : "Sorry, I encountered an error. Please try again.";
        // Show error in chat
        setMessages((prev) => [
          ...prev,
          {
            id: `error-${Date.now()}`,
            role: "assistant" as const,
            content: errMsg.includes("error")
              ? errMsg
              : `Sorry, I encountered an error: ${errMsg}`,
            attachments: [],
            created_at: new Date().toISOString(),
          },
        ]);
      } finally {
        setSending(false);
      }
    },
    [input, sending, session, currentConvId, type, investigationId, attachments, onConversationCreated]
  );

  const handleSubmit = useCallback(
    (e: FormEvent) => {
      e.preventDefault();
      handleSend();
    },
    [handleSend]
  );

  const suggestions = type === "report" ? REPORT_SUGGESTIONS : GENERAL_SUGGESTIONS;

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: compact ? "100%" : "100%",
        position: "relative",
      }}
      onDragOver={(e) => {
        e.preventDefault();
        setDragOver(true);
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={handleDrop}
    >
      {/* Drop zone overlay */}
      {dragOver && (
        <div className="drop-zone-overlay">
          <span>Drop files or folders to attach</span>
        </div>
      )}

      {/* ─── Messages Area ───────────────────────────────────────────── */}
      {loading ? (
        <div className="chat-messages">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="animate-pulse"
              style={{
                alignSelf: i % 2 === 0 ? "flex-end" : "flex-start",
                width: `${40 + i * 10}%`,
                height: "48px",
                background: "var(--color-surface-2)",
                borderRadius: "16px",
              }}
            />
          ))}
        </div>
      ) : messages.length === 0 && !sending ? (
        <div className="chat-empty">
          <div className="chat-empty-icon" style={{ fontSize: "2.5rem" }}>
            {type === "report" ? "📋" : "🛡️"}
          </div>
          <div>
            <h3
              className="font-[family-name:var(--font-playfair)]"
              style={{
                fontSize: "1.375rem",
                fontWeight: 400,
                color: "var(--color-text)",
                marginBottom: "8px",
                letterSpacing: "-0.02em",
              }}
            >
              {type === "report"
                ? "Ask about this report"
                : "What can I help you investigate?"}
            </h3>
            <p style={{ fontSize: "0.8125rem", color: "var(--color-text-3)", marginBottom: "4px" }}>
              {type === "report"
                ? "Ask follow-up questions grounded in the investigation findings."
                : "Ask about industrial safety, equipment health, or engineering standards. You can also attach files below."}
            </p>
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", justifyContent: "center", maxWidth: "560px" }}>
            {suggestions.map((q, i) => (
              <button
                key={i}
                onClick={() => handleSend(q)}
                className="animate-fade-in-up-small"
                style={{
                  animationDelay: `${(i + 1) * 60}ms`,
                  background: "var(--color-surface-2)",
                  border: "1px solid var(--color-border)",
                  borderRadius: "10px",
                  padding: "8px 14px",
                  fontSize: "0.75rem",
                  color: "var(--color-text-2)",
                  cursor: "pointer",
                  transition: "all 0.2s ease",
                  maxWidth: "260px",
                  textAlign: "left",
                  lineHeight: 1.4,
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = "var(--color-accent)";
                  e.currentTarget.style.color = "var(--color-accent)";
                  e.currentTarget.style.transform = "translateY(-1px)";
                  e.currentTarget.style.boxShadow = "0 4px 12px rgba(0,0,0,0.08)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = "var(--color-border)";
                  e.currentTarget.style.color = "var(--color-text-2)";
                  e.currentTarget.style.transform = "translateY(0)";
                  e.currentTarget.style.boxShadow = "none";
                }}
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      ) : (
        <div className="chat-messages">
          {messages.map((msg) => (
            <div key={msg.id}>
              <div
                className={`chat-bubble ${
                  msg.role === "user" ? "chat-bubble-user" : "chat-bubble-assistant"
                }`}
              >
                {/* Render attachments */}
                {msg.attachments && msg.attachments.length > 0 && (
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginBottom: "8px" }}>
                    {msg.attachments.map((att, i) =>
                      att.type === "image" ? (
                        <img
                          key={i}
                          src={att.url}
                          alt={att.filename}
                          style={{
                            maxWidth: "200px",
                            maxHeight: "150px",
                            borderRadius: "8px",
                            border: "1px solid var(--color-border)",
                          }}
                        />
                      ) : (
                        <span key={i} className="attachment-chip">
                          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                            <polyline points="14 2 14 8 20 8" />
                          </svg>
                          <span className="attachment-chip-name">{att.filename}</span>
                        </span>
                      )
                    )}
                  </div>
                )}

                {/* Render message content */}
                <MarkdownMessage content={msg.content} />
              </div>
              <div
                className="chat-timestamp"
                style={{ textAlign: msg.role === "user" ? "right" : "left" }}
              >
                {new Date(msg.created_at).toLocaleTimeString("en-US", {
                  hour: "numeric",
                  minute: "2-digit",
                })}
              </div>
            </div>
          ))}

          {/* Typing indicator */}
          {sending && (
            <div className="chat-bubble chat-bubble-assistant">
              <div className="typing-indicator">
                <div className="typing-dot" />
                <div className="typing-dot" />
                <div className="typing-dot" />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      )}

      {/* ─── Composer ────────────────────────────────────────────────── */}
      <div className="chat-composer">
        {/* Upload error banner */}
        {uploadError && (
          <div
            style={{
              padding: "6px 12px",
              marginBottom: "8px",
              background: "rgba(186, 56, 56, 0.1)",
              border: "1px solid rgba(186, 56, 56, 0.25)",
              borderRadius: "8px",
              fontSize: "0.75rem",
              color: "var(--color-red)",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            <span>{uploadError}</span>
            <button
              onClick={() => setUploadError(null)}
              style={{
                background: "none",
                border: "none",
                color: "var(--color-red)",
                cursor: "pointer",
                fontWeight: "bold",
              }}
            >
              ×
            </button>
          </div>
        )}

        {/* Attachment previews */}
        {attachments.length > 0 && (
          <div
            style={{
              display: "flex",
              flexWrap: "wrap",
              gap: "6px",
              marginBottom: "8px",
              maxHeight: "120px",
              overflowY: "auto",
              paddingRight: "4px",
            }}
          >
            {attachments.map((att, i) => (
              <span
                key={i}
                className="attachment-chip"
                title={att.relative_path || att.filename}
                style={{ display: "inline-flex", alignItems: "center", gap: "6px" }}
              >
                <span>{att.type === "image" ? "🖼" : att.relative_path?.includes("/") ? "📁" : "📄"}</span>
                <span className="attachment-chip-name" style={{ maxWidth: "200px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {att.relative_path && att.relative_path !== att.filename ? att.relative_path : att.filename}
                </span>
                <button
                  type="button"
                  onClick={() => removeAttachment(i)}
                  title="Remove attachment"
                  style={{
                    background: "none",
                    border: "none",
                    cursor: "pointer",
                    padding: "0 2px",
                    color: "inherit",
                    opacity: 0.7,
                  }}
                >
                  ×
                </button>
              </span>
            ))}
            {attachments.length > 2 && (
              <button
                type="button"
                onClick={clearAllAttachments}
                style={{
                  background: "none",
                  border: "none",
                  color: "var(--color-text-3)",
                  fontSize: "0.6875rem",
                  cursor: "pointer",
                  padding: "2px 6px",
                  textDecoration: "underline",
                }}
              >
                Clear all ({attachments.length})
              </button>
            )}
            {uploadingCount > 0 && (
              <span className="attachment-chip" style={{ opacity: 0.8 }}>
                <svg className="animate-spin" width="12" height="12" viewBox="0 0 24 24" fill="none">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" opacity="0.3" />
                  <path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
                </svg>
                {uploadingCount === 1 ? "Uploading 1 file…" : `Uploading ${uploadingCount} files…`}
              </span>
            )}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="chat-composer-inner">
            {/* Attach multiple files button */}
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              title="Attach files (select multiple files)"
              style={{
                background: "none",
                border: "none",
                cursor: "pointer",
                padding: "4px",
                color: "var(--color-text-3)",
                transition: "color 0.15s ease",
                flexShrink: 0,
              }}
              onMouseEnter={(e) => (e.currentTarget.style.color = "var(--color-accent)")}
              onMouseLeave={(e) => (e.currentTarget.style.color = "var(--color-text-3)")}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
              </svg>
            </button>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.txt,.csv,.docx,.png,.jpg,.jpeg,.webp,.gif,.md,.json"
              style={{ display: "none" }}
              onChange={(e) => {
                if (e.target.files && e.target.files.length > 0) {
                  handleFileUpload(e.target.files);
                }
                e.target.value = "";
              }}
            />

            {/* Attach folder button */}
            <button
              type="button"
              onClick={() => folderInputRef.current?.click()}
              title="Attach folder (select directory)"
              style={{
                background: "none",
                border: "none",
                cursor: "pointer",
                padding: "4px",
                color: "var(--color-text-3)",
                transition: "color 0.15s ease",
                flexShrink: 0,
              }}
              onMouseEnter={(e) => (e.currentTarget.style.color = "var(--color-accent)")}
              onMouseLeave={(e) => (e.currentTarget.style.color = "var(--color-text-3)")}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
              </svg>
            </button>
            <input
              ref={folderInputRef}
              type="file"
              {...{ webkitdirectory: "", directory: "", multiple: true }}
              style={{ display: "none" }}
              onChange={(e) => {
                if (e.target.files && e.target.files.length > 0) {
                  handleFileUpload(e.target.files);
                }
                e.target.value = "";
              }}
            />

            {/* Text input */}
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => handleTextareaChange(e.target.value)}
              placeholder={
                type === "report"
                  ? "Ask about this report…"
                  : "Ask KavachAI anything…"
              }
              rows={1}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
            />

            {/* Send button */}
            <button
              type="submit"
              disabled={(!input.trim() && attachments.length === 0) || sending}
              style={{
                background: "var(--color-accent)",
                color: "#faf8f5",
                border: "none",
                borderRadius: "10px",
                padding: "6px 10px",
                cursor: "pointer",
                transition: "all 0.15s ease",
                flexShrink: 0,
                opacity: (!input.trim() && attachments.length === 0) || sending ? 0.4 : 1,
              }}
              title="Send message"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="22" y1="2" x2="11" y2="13" />
                <polygon points="22 2 15 22 11 13 2 9 22 2" />
              </svg>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
