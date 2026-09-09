"use client";

import { useState, useEffect, FormEvent, useCallback } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/app/components/Sidebar";
import ChatWindow from "@/app/components/ChatWindow";
import SuggestedQuestions from "@/app/components/SuggestedQuestions";
import PidRelationship from "@/app/components/PidRelationship";
import { useSession } from "@/app/hooks/useSession";
import {
  createInvestigation,
  getKnowledgeBaseSummary,
  getKnowledgeBaseGraph,
  uploadDocument,
  uploadDataset,
} from "@/app/services/api";
import type { KnowledgeBaseSummary, KnowledgeBaseGraph } from "@/app/types";

type DashboardView = "chat" | "investigation" | "knowledge";

export default function Workspace() {
  const router = useRouter();
  const { session, isAuthenticated, isLoading: sessionLoading } = useSession();
  const [activeView, setActiveView] = useState<DashboardView>("chat");
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);

  // Investigation mode state
  const [query, setQuery] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Knowledge Base mode state
  const [kbSummary, setKbSummary] = useState<KnowledgeBaseSummary | null>(null);
  const [kbGraph, setKbGraph] = useState<KnowledgeBaseGraph | null>(null);
  const [kbLoading, setKbLoading] = useState(false);
  
  // Document upload state
  const [docFile, setDocFile] = useState<File | null>(null);
  const [docType, setDocType] = useState("inspection_report");
  const [docEquipment, setDocEquipment] = useState("P-102");
  const [docDepartment, setDocDepartment] = useState("Reliability");
  const [uploadingDoc, setUploadingDoc] = useState(false);
  const [docMsg, setDocMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Dataset upload state
  const [datasetFile, setDatasetFile] = useState<File | null>(null);
  const [datasetEquipment, setDatasetEquipment] = useState("P-102");
  const [uploadingDataset, setUploadingDataset] = useState(false);
  const [datasetMsg, setDatasetMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const loadKnowledgeData = useCallback(async () => {
    setKbLoading(true);
    try {
      const [sum, graph] = await Promise.all([
        getKnowledgeBaseSummary().catch(() => null),
        getKnowledgeBaseGraph().catch(() => null),
      ]);
      if (sum) setKbSummary(sum);
      if (graph) setKbGraph(graph);
    } catch {
      // Handled gracefully
    } finally {
      setKbLoading(false);
    }
  }, []);

  useEffect(() => {
    if (activeView === "knowledge") {
      loadKnowledgeData();
    }
  }, [activeView, loadKnowledgeData]);

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

  async function handleDocUploadSubmit(e: FormEvent) {
    e.preventDefault();
    if (!docFile) return;
    setUploadingDoc(true);
    setDocMsg(null);
    try {
      const formData = new FormData();
      formData.append("file", docFile);
      formData.append("document_type", docType);
      formData.append("equipment_ids", JSON.stringify([docEquipment]));
      formData.append("department_scope", docDepartment);
      const res = await uploadDocument(formData);
      setDocMsg({ type: "success", text: `Document ingested! ID: ${res.document_id} (${res.status})` });
      setDocFile(null);
      loadKnowledgeData();
    } catch (err) {
      setDocMsg({ type: "error", text: err instanceof Error ? err.message : "Failed to upload document" });
    } finally {
      setUploadingDoc(false);
    }
  }

  async function handleDatasetUploadSubmit(e: FormEvent) {
    e.preventDefault();
    if (!datasetFile) return;
    setUploadingDataset(true);
    setDatasetMsg(null);
    try {
      const formData = new FormData();
      formData.append("file", datasetFile);
      formData.append("equipment_id", datasetEquipment);
      formData.append("table_name", "plant_telemetry");
      const res = await uploadDataset(formData);
      setDatasetMsg({ type: "success", text: `Dataset ingested! ID: ${res.dataset_id} (${res.status})` });
      setDatasetFile(null);
      loadKnowledgeData();
    } catch (err) {
      setDatasetMsg({ type: "error", text: err instanceof Error ? err.message : "Failed to upload dataset" });
    } finally {
      setUploadingDataset(false);
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
            <button
              className={`mode-tab ${activeView === "knowledge" ? "active" : ""}`}
              onClick={() => { setActiveView("knowledge"); setActiveConversationId(null); }}
            >
              📚 Plant Knowledge
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
        ) : activeView === "investigation" ? (
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
        ) : (
          /* ─── Plant Knowledge Base View ──────────────────────────── */
          <div
            style={{
              flex: 1,
              padding: "32px 36px",
              overflowY: "auto",
              background: "var(--color-bg)",
            }}
          >
            <div style={{ maxWidth: "1000px", margin: "0 auto" }}>
              <div style={{ marginBottom: "28px" }}>
                <h2
                  className="font-[family-name:var(--font-playfair)]"
                  style={{
                    fontSize: "1.75rem",
                    fontWeight: 700,
                    color: "var(--color-text)",
                    letterSpacing: "-0.02em",
                    marginBottom: "6px",
                  }}
                >
                  Plant Knowledge Base & Asset Ingestion
                </h2>
                <p style={{ fontSize: "0.875rem", color: "var(--color-text-3)" }}>
                  Sovereign index of refinery operating manuals, P&ID topology, and time-series telemetry data.
                </p>
              </div>

              {/* Stats Summary Cards */}
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
                  gap: "16px",
                  marginBottom: "32px",
                }}
              >
                <div
                  className="card-shadow"
                  style={{
                    background: "var(--color-surface)",
                    border: "1px solid var(--color-border)",
                    borderRadius: "12px",
                    padding: "18px 20px",
                  }}
                >
                  <div style={{ fontSize: "0.75rem", color: "var(--color-text-3)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "6px" }}>
                    Documents Indexed
                  </div>
                  <div style={{ fontSize: "1.75rem", fontWeight: 700, color: "var(--color-accent)" }}>
                    {kbSummary ? kbSummary.documents : kbLoading ? "..." : 7}
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "var(--color-text-2)", marginTop: "4px" }}>
                    Manuals, SOPs & Inspection Reports
                  </div>
                </div>

                <div
                  className="card-shadow"
                  style={{
                    background: "var(--color-surface)",
                    border: "1px solid var(--color-border)",
                    borderRadius: "12px",
                    padding: "18px 20px",
                  }}
                >
                  <div style={{ fontSize: "0.75rem", color: "var(--color-text-3)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "6px" }}>
                    Telemetry Datasets
                  </div>
                  <div style={{ fontSize: "1.75rem", fontWeight: 700, color: "var(--color-teal)" }}>
                    {kbSummary ? kbSummary.datasets : kbLoading ? "..." : 1}
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "var(--color-text-2)", marginTop: "4px" }}>
                    Structured time-series tables
                  </div>
                </div>

                <div
                  className="card-shadow"
                  style={{
                    background: "var(--color-surface)",
                    border: "1px solid var(--color-border)",
                    borderRadius: "12px",
                    padding: "18px 20px",
                  }}
                >
                  <div style={{ fontSize: "0.75rem", color: "var(--color-text-3)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "6px" }}>
                    P&ID Drawings
                  </div>
                  <div style={{ fontSize: "1.75rem", fontWeight: 700, color: "var(--color-text)" }}>
                    {kbSummary ? kbSummary.pid_drawings : kbLoading ? "..." : 1}
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "var(--color-text-2)", marginTop: "4px" }}>
                    Unit 101 Topological graph
                  </div>
                </div>
              </div>

              {/* P&ID Plant Topology Visualization */}
              <div style={{ marginBottom: "36px" }}>
                <h3 style={{ fontSize: "1rem", fontWeight: 600, color: "var(--color-text)", marginBottom: "12px" }}>
                  Active Plant Topology (Unit 101)
                </h3>
                <PidRelationship
                  components={
                    kbGraph && kbGraph.nodes.length > 0
                      ? kbGraph.nodes.map((n) => n.id)
                      : ["T-101", "P-102", "V-204", "R-101"]
                  }
                  highlighted="P-102"
                />
              </div>

              {/* Ingestion Forms Grid */}
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(420px, 1fr))",
                  gap: "24px",
                }}
              >
                {/* 1. Ingest Industrial Document */}
                <div
                  className="card-shadow"
                  style={{
                    background: "var(--color-surface)",
                    border: "1px solid var(--color-border)",
                    borderRadius: "14px",
                    padding: "24px",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "16px" }}>
                    <span style={{ fontSize: "1.25rem" }}>📄</span>
                    <h3 style={{ fontSize: "1.0625rem", fontWeight: 600, color: "var(--color-text)" }}>
                      Ingest Document
                    </h3>
                  </div>
                  <p style={{ fontSize: "0.8125rem", color: "var(--color-text-3)", marginBottom: "20px" }}>
                    Upload an inspection report, SOP, or operating manual for semantic chunking and embedding.
                  </p>

                  <form onSubmit={handleDocUploadSubmit}>
                    <div style={{ marginBottom: "14px" }}>
                      <label style={{ display: "block", fontSize: "0.75rem", color: "var(--color-text-2)", marginBottom: "6px" }}>
                        File (PDF, DOCX)
                      </label>
                      <input
                        type="file"
                        accept=".pdf,.docx,.txt"
                        required
                        onChange={(e) => setDocFile(e.target.files?.[0] || null)}
                        style={{
                          width: "100%",
                          fontSize: "0.8125rem",
                          color: "var(--color-text)",
                          padding: "8px 10px",
                          borderRadius: "8px",
                          border: "1px solid var(--color-border)",
                          background: "var(--color-surface-2)",
                        }}
                      />
                    </div>

                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginBottom: "14px" }}>
                      <div>
                        <label style={{ display: "block", fontSize: "0.75rem", color: "var(--color-text-2)", marginBottom: "6px" }}>
                          Document Type
                        </label>
                        <select
                          value={docType}
                          onChange={(e) => setDocType(e.target.value)}
                          style={{
                            width: "100%",
                            padding: "8px 10px",
                            borderRadius: "8px",
                            border: "1px solid var(--color-border)",
                            background: "var(--color-surface-2)",
                            color: "var(--color-text)",
                            fontSize: "0.8125rem",
                          }}
                        >
                          <option value="inspection_report">Inspection Report</option>
                          <option value="manual">Operating Manual</option>
                          <option value="sop">Safety SOP</option>
                          <option value="other">General Documentation</option>
                        </select>
                      </div>

                      <div>
                        <label style={{ display: "block", fontSize: "0.75rem", color: "var(--color-text-2)", marginBottom: "6px" }}>
                          Target Equipment ID
                        </label>
                        <input
                          type="text"
                          value={docEquipment}
                          onChange={(e) => setDocEquipment(e.target.value)}
                          placeholder="e.g. P-102"
                          style={{
                            width: "100%",
                            padding: "8px 10px",
                            borderRadius: "8px",
                            border: "1px solid var(--color-border)",
                            background: "var(--color-surface-2)",
                            color: "var(--color-text)",
                            fontSize: "0.8125rem",
                          }}
                        />
                      </div>
                    </div>

                    <button
                      type="submit"
                      disabled={!docFile || uploadingDoc}
                      style={{
                        width: "100%",
                        padding: "10px 16px",
                        background: "var(--color-accent)",
                        color: "#faf8f5",
                        border: "none",
                        borderRadius: "8px",
                        fontWeight: 600,
                        fontSize: "0.8125rem",
                        cursor: !docFile || uploadingDoc ? "not-allowed" : "pointer",
                        opacity: !docFile || uploadingDoc ? 0.5 : 1,
                        transition: "all 0.2s ease",
                      }}
                    >
                      {uploadingDoc ? "Chunking & Ingesting..." : "Upload & Ingest Document"}
                    </button>
                  </form>

                  {docMsg && (
                    <div
                      style={{
                        marginTop: "14px",
                        padding: "10px 12px",
                        borderRadius: "8px",
                        fontSize: "0.75rem",
                        background: docMsg.type === "success" ? "rgba(45, 138, 110, 0.1)" : "rgba(186, 56, 56, 0.1)",
                        color: docMsg.type === "success" ? "var(--color-teal)" : "var(--color-red)",
                        border: `1px solid ${docMsg.type === "success" ? "var(--color-teal)" : "var(--color-red)"}`,
                      }}
                    >
                      {docMsg.text}
                    </div>
                  )}
                </div>

                {/* 2. Ingest Telemetry Dataset */}
                <div
                  className="card-shadow"
                  style={{
                    background: "var(--color-surface)",
                    border: "1px solid var(--color-border)",
                    borderRadius: "14px",
                    padding: "24px",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "16px" }}>
                    <span style={{ fontSize: "1.25rem" }}>📊</span>
                    <h3 style={{ fontSize: "1.0625rem", fontWeight: 600, color: "var(--color-text)" }}>
                      Ingest Telemetry Dataset
                    </h3>
                  </div>
                  <p style={{ fontSize: "0.8125rem", color: "var(--color-text-3)", marginBottom: "20px" }}>
                    Upload time-series telemetry CSV (vibration, temperature, pressure) for deterministic analytics.
                  </p>

                  <form onSubmit={handleDatasetUploadSubmit}>
                    <div style={{ marginBottom: "14px" }}>
                      <label style={{ display: "block", fontSize: "0.75rem", color: "var(--color-text-2)", marginBottom: "6px" }}>
                        Dataset File (CSV, XLSX)
                      </label>
                      <input
                        type="file"
                        accept=".csv,.xlsx"
                        required
                        onChange={(e) => setDatasetFile(e.target.files?.[0] || null)}
                        style={{
                          width: "100%",
                          fontSize: "0.8125rem",
                          color: "var(--color-text)",
                          padding: "8px 10px",
                          borderRadius: "8px",
                          border: "1px solid var(--color-border)",
                          background: "var(--color-surface-2)",
                        }}
                      />
                    </div>

                    <div style={{ marginBottom: "14px" }}>
                      <label style={{ display: "block", fontSize: "0.75rem", color: "var(--color-text-2)", marginBottom: "6px" }}>
                        Equipment ID
                      </label>
                      <input
                        type="text"
                        value={datasetEquipment}
                        onChange={(e) => setDatasetEquipment(e.target.value)}
                        placeholder="e.g. P-102"
                        style={{
                          width: "100%",
                          padding: "8px 10px",
                          borderRadius: "8px",
                          border: "1px solid var(--color-border)",
                          background: "var(--color-surface-2)",
                          color: "var(--color-text)",
                          fontSize: "0.8125rem",
                        }}
                      />
                    </div>

                    <button
                      type="submit"
                      disabled={!datasetFile || uploadingDataset}
                      style={{
                        width: "100%",
                        padding: "10px 16px",
                        background: "var(--color-teal)",
                        color: "#faf8f5",
                        border: "none",
                        borderRadius: "8px",
                        fontWeight: 600,
                        fontSize: "0.8125rem",
                        cursor: !datasetFile || uploadingDataset ? "not-allowed" : "pointer",
                        opacity: !datasetFile || uploadingDataset ? 0.5 : 1,
                        transition: "all 0.2s ease",
                      }}
                    >
                      {uploadingDataset ? "Ingesting Table..." : "Upload & Parse Telemetry"}
                    </button>
                  </form>

                  {datasetMsg && (
                    <div
                      style={{
                        marginTop: "14px",
                        padding: "10px 12px",
                        borderRadius: "8px",
                        fontSize: "0.75rem",
                        background: datasetMsg.type === "success" ? "rgba(45, 138, 110, 0.1)" : "rgba(186, 56, 56, 0.1)",
                        color: datasetMsg.type === "success" ? "var(--color-teal)" : "var(--color-red)",
                        border: `1px solid ${datasetMsg.type === "success" ? "var(--color-teal)" : "var(--color-red)"}`,
                      }}
                    >
                      {datasetMsg.text}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
