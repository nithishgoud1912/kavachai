"use client";

import { useState, useEffect, FormEvent } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/app/components/Sidebar";
import ChatWindow from "@/app/components/ChatWindow";
import SuggestedQuestions from "@/app/components/SuggestedQuestions";
import { useSession } from "@/app/hooks/useSession";
import { createInvestigation } from "@/app/services/api";

type DashboardView = "chat" | "investigation";

export default function Workspace() {
  const router = useRouter();
  const { session, isAuthenticated, isLoading: sessionLoading } = useSession();
  const [activeView, setActiveView] = useState<DashboardView>("chat");
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);

  // Investigation mode state
  const [query, setQuery] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
  }

  function handleSelectConversation(id: string) {
    setActiveView("chat");
    setActiveConversationId(id);
  }

  function handleConversationCreated(id: string) {
    setActiveConversationId(id);
    // Sidebar reloads via the global __reloadSidebar ref
  }

  async function handleInvestigationSubmit(e: FormEvent) {
    e.preventDefault();
    if (!query.trim() || !session) return;

    setSubmitting(true);
    setError(null);

    try {
      const investigation = await createInvestigation(query.trim(), session.session_id);
      router.push(`/investigation/${investigation.investigation_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start investigation");
      setSubmitting(false);
    }
  }

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
            <div style={{ width: "100%", maxWidth: "640px" }}>
              <h2
                className="font-[family-name:var(--font-playfair)] hero-fade-in-up hero-stagger-1"
                style={{
                  fontSize: "1.75rem",
                  fontWeight: 400,
                  color: "var(--color-text)",
                  textAlign: "center",
                  letterSpacing: "-0.02em",
                  marginBottom: "32px",
                }}
              >
                What do you want to investigate?
              </h2>

              <form
                onSubmit={handleInvestigationSubmit}
                className="hero-fade-in-up hero-stagger-2"
                style={{ position: "relative" }}
              >
                <div
                  className="card-shadow card-hover"
                  style={{
                    background: "var(--color-surface)",
                    border: "1px solid var(--color-border)",
                    borderRadius: "16px",
                    overflow: "hidden",
                    transition: "all 0.2s ease",
                  }}
                >
                  <textarea
                    id="investigation-query"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Investigate Pump P-102 and determine whether its condition has deteriorated."
                    rows={3}
                    className="font-[family-name:var(--font-mono)]"
                    style={{
                      width: "100%",
                      background: "transparent",
                      padding: "24px 24px 56px",
                      color: "var(--color-text)",
                      resize: "none",
                      border: "none",
                      outline: "none",
                      fontSize: "0.875rem",
                    }}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        if (query.trim()) handleInvestigationSubmit(e);
                      }
                    }}
                  />
                  <div style={{ position: "absolute", bottom: "16px", right: "16px" }}>
                    <button
                      type="submit"
                      disabled={!query.trim() || submitting}
                      style={{
                        background: "var(--color-accent)",
                        color: "#faf8f5",
                        fontWeight: 600,
                        fontSize: "0.875rem",
                        padding: "10px 20px",
                        borderRadius: "10px",
                        border: "none",
                        cursor: "pointer",
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

              <div className="hero-fade-in-up hero-stagger-3" style={{ marginTop: "24px" }}>
                <SuggestedQuestions onSelect={(q) => setQuery(q)} />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
