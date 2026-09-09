"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useSession } from "@/app/hooks/useSession";
import { getConversations, getInvestigations, deleteConversation } from "@/app/services/api";
import type { Conversation, InvestigationSummary } from "@/app/types";

interface SidebarProps {
  activeConversationId: string | null;
  onNewChat: () => void;
  onNewInvestigation: () => void;
  onSelectConversation: (id: string) => void;
  className?: string;
}

function timeAgo(dateStr: string): string {
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  const diff = now - then;
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  if (days === 1) return "yesterday";
  if (days < 7) return `${days}d ago`;
  return new Date(dateStr).toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

export default function Sidebar({
  activeConversationId,
  onNewChat,
  onNewInvestigation,
  onSelectConversation,
  className = "",
}: SidebarProps) {
  const { session } = useSession();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [investigations, setInvestigations] = useState<InvestigationSummary[]>([]);
  const [loadingChats, setLoadingChats] = useState(true);
  const [loadingReports, setLoadingReports] = useState(true);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  async function handleDeleteConversation(e: React.MouseEvent, id: string) {
    e.stopPropagation();
    if (!window.confirm("Are you sure you want to delete this chat?")) return;
    setDeletingId(id);
    try {
      await deleteConversation(id);
      setConversations((prev) => prev.filter((c) => c.id !== id));
      if (activeConversationId === id) {
        onNewChat();
      }
    } catch (err) {
      console.error("Failed to delete conversation:", err);
      alert("Failed to delete chat. Please try again.");
    } finally {
      setDeletingId(null);
    }
  }

  const loadData = useCallback(async () => {
    try {
      setLoadingChats(true);
      const convs = await getConversations();
      setConversations(convs);
    } catch {
      // Silently fail — sidebar still usable
    } finally {
      setLoadingChats(false);
    }

    try {
      setLoadingReports(true);
      const invs = await getInvestigations();
      setInvestigations(invs);
    } catch {
      // Silently fail
    } finally {
      setLoadingReports(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Expose reload for parent to call after creating new items
  useEffect(() => {
    (window as unknown as Record<string, unknown>).__reloadSidebar = loadData;
    return () => {
      delete (window as unknown as Record<string, unknown>).__reloadSidebar;
    };
  }, [loadData]);

  return (
    <aside className={`dashboard-sidebar ${className}`}>
      {/* ─── Top Actions ─────────────────────────────────────────── */}
      <div style={{ padding: "16px 12px 8px" }}>
        {/* Logo */}
        <div style={{ padding: "0 4px", marginBottom: "16px" }}>
          <Link href="/workspace" className="flex items-center gap-2" style={{ textDecoration: "none" }}>
            <span
              className="font-[family-name:var(--font-playfair)]"
              style={{
                color: "var(--color-accent)",
                fontSize: "1.25rem",
                fontWeight: 700,
                letterSpacing: "-0.02em",
              }}
            >
              KavachAI
            </span>
          </Link>
        </div>

        {/* New Chat */}
        <button
          id="new-chat-btn"
          onClick={onNewChat}
          style={{
            width: "100%",
            padding: "10px 16px",
            background: "var(--color-accent)",
            color: "#faf8f5",
            border: "none",
            borderRadius: "10px",
            fontSize: "0.8125rem",
            fontWeight: 600,
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            gap: "8px",
            justifyContent: "center",
            transition: "all 0.2s ease",
            marginBottom: "6px",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.filter = "brightness(1.1)";
            e.currentTarget.style.transform = "translateY(-1px)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.filter = "brightness(1)";
            e.currentTarget.style.transform = "translateY(0)";
          }}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
            <path d="M12 5v14M5 12h14" />
          </svg>
          New Chat
        </button>

        {/* New Investigation */}
        <button
          id="new-investigation-btn"
          onClick={onNewInvestigation}
          style={{
            width: "100%",
            padding: "9px 16px",
            background: "transparent",
            color: "var(--color-text-2)",
            border: "1px solid var(--color-border)",
            borderRadius: "10px",
            fontSize: "0.8125rem",
            fontWeight: 500,
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            gap: "8px",
            justifyContent: "center",
            transition: "all 0.2s ease",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.borderColor = "var(--color-accent)";
            e.currentTarget.style.color = "var(--color-accent)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.borderColor = "var(--color-border)";
            e.currentTarget.style.color = "var(--color-text-2)";
          }}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10" />
            <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76" fill="currentColor" stroke="none" />
          </svg>
          Deep Investigation
        </button>
      </div>

      {/* ─── Chat History ────────────────────────────────────────── */}
      <div style={{ flex: 1, overflowY: "auto", paddingBottom: "8px" }}>
        <p className="sidebar-section-title">Recent Chats</p>
        {loadingChats ? (
          <div style={{ padding: "8px 16px" }}>
            {[1, 2, 3].map((i) => (
              <div key={i} className="animate-pulse" style={{
                height: "32px",
                background: "var(--color-surface-2)",
                borderRadius: "8px",
                marginBottom: "4px",
              }} />
            ))}
          </div>
        ) : conversations.length === 0 ? (
          <p style={{
            padding: "8px 16px",
            fontSize: "0.75rem",
            color: "var(--color-text-3)",
            fontStyle: "italic",
          }}>
            No conversations yet
          </p>
        ) : (
          conversations.map((conv) => (
            <div
              key={conv.id}
              className={`sidebar-item ${activeConversationId === conv.id ? "active" : ""}`}
              onClick={() => onSelectConversation(conv.id)}
            >
              <span style={{ fontSize: "0.875rem", flexShrink: 0 }}>
                {conv.type === "report" ? "📋" : "💬"}
              </span>
              <span className="sidebar-item-title">{conv.title}</span>
              <span className="sidebar-item-meta">{timeAgo(conv.updated_at)}</span>
              <button
                type="button"
                className="sidebar-item-delete-btn"
                title="Delete chat"
                aria-label="Delete chat"
                disabled={deletingId === conv.id}
                onClick={(e) => handleDeleteConversation(e, conv.id)}
              >
                {deletingId === conv.id ? (
                  <span
                    className="animate-spin"
                    style={{
                      display: "inline-block",
                      width: "12px",
                      height: "12px",
                      border: "2px solid currentColor",
                      borderTopColor: "transparent",
                      borderRadius: "50%",
                    }}
                  />
                ) : (
                  <svg
                    width="13"
                    height="13"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <polyline points="3 6 5 6 21 6" />
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                    <line x1="10" y1="11" x2="10" y2="17" />
                    <line x1="14" y1="11" x2="14" y2="17" />
                  </svg>
                )}
              </button>
            </div>
          ))
        )}

        {/* ─── Reports ───────────────────────────────────────────── */}
        <p className="sidebar-section-title" style={{ marginTop: "24px" }}>
          Investigation Reports
        </p>
        {loadingReports ? (
          <div style={{ padding: "8px 16px" }}>
            {[1, 2].map((i) => (
              <div key={i} className="animate-pulse" style={{
                height: "40px",
                background: "var(--color-surface-2)",
                borderRadius: "8px",
                marginBottom: "4px",
              }} />
            ))}
          </div>
        ) : investigations.length === 0 ? (
          <p style={{
            padding: "8px 16px",
            fontSize: "0.75rem",
            color: "var(--color-text-3)",
            fontStyle: "italic",
          }}>
            No investigations yet
          </p>
        ) : (
          investigations.map((inv) => (
            <Link
              key={inv.id}
              href={`/report/${inv.id}`}
              className="sidebar-item"
              style={{ flexDirection: "column", alignItems: "flex-start", gap: "4px" }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "8px", width: "100%" }}>
                <span className="sidebar-item-title" style={{ fontSize: "0.8125rem" }}>
                  {inv.query.length > 40 ? inv.query.substring(0, 40) + "…" : inv.query}
                </span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <span className={`status-badge ${inv.status}`}>
                  {inv.status === "complete" ? "✓" : inv.status === "failed" ? "✕" : "◎"}{" "}
                  {inv.status.replace("_", " ")}
                </span>
                {inv.confidence !== null && (
                  <span style={{ fontSize: "0.625rem", color: "var(--color-text-3)" }}>
                    {inv.confidence}%
                  </span>
                )}
              </div>
            </Link>
          ))
        )}
      </div>

      {/* ─── Footer ──────────────────────────────────────────────── */}
      <div style={{
        padding: "12px 16px",
        borderTop: "1px solid var(--color-border)",
        background: "var(--color-bg)",
      }}>
        {session && (
          <p style={{ fontSize: "0.6875rem", color: "var(--color-text-3)" }}>
            <span style={{ color: "var(--color-text-2)" }}>{session.name}</span>
            <span style={{ margin: "0 6px" }}>·</span>
            <span className="font-[family-name:var(--font-mono)]" style={{ fontSize: "0.625rem" }}>
              {session.department}
            </span>
          </p>
        )}
      </div>
    </aside>
  );
}
