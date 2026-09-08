// ─── Agent Types ───────────────────────────────────────────────────

export type AgentName =
  | "planner"
  | "document_agent"
  | "data_agent"
  | "vision_agent"
  | "rag_agent"
  | "verification_agent";

export type AgentStatus =
  | "pending"
  | "working"
  | "complete"
  | "skipped"
  | "failed";

export const AGENT_DISPLAY_NAMES: Record<AgentName, string> = {
  planner: "Planner",
  document_agent: "Document Agent",
  data_agent: "Data Agent",
  vision_agent: "Vision Agent",
  rag_agent: "RAG Agent",
  verification_agent: "Verification",
};

export const ALL_AGENTS: AgentName[] = [
  "planner",
  "document_agent",
  "data_agent",
  "vision_agent",
  "rag_agent",
  "verification_agent",
];

// ─── Session ───────────────────────────────────────────────────────

export interface Session {
  session_id: string;
  name: string;
  department: string;
  issued_at: string;
}

// ─── Knowledge Base ────────────────────────────────────────────────

export interface KnowledgeBaseSummary {
  documents: number;
  datasets: number;
  pid_drawings: number;
}

// ─── Investigation ─────────────────────────────────────────────────

export interface Investigation {
  investigation_id: string;
  status: string;
  stream_url: string;
}

export interface SubTask {
  agent: AgentName;
  goal: string;
}

export interface InvestigationPlan {
  investigation_id: string;
  sub_tasks: SubTask[];
}

export interface AgentUpdate {
  agent: AgentName;
  status: AgentStatus;
  message: string;
  elapsed_ms: number;
}

export type InvestigationState =
  | "idle"
  | "creating"
  | "streaming"
  | "completed"
  | "insufficient_evidence"
  | "failed"
  | "recovering";

// ─── Evidence ──────────────────────────────────────────────────────

export interface EvidenceReference {
  type: "document" | "dataset" | "pid_drawing";
  source_id: string;
  label: string;
  page?: number | null;
  section?: string | null;
}

export interface DocumentEvidence {
  source_id: string;
  type: "document";
  filename: string;
  page: number;
  excerpt: string;
  view_url: string;
}

export interface DatasetEvidence {
  source_id: string;
  type: "dataset";
  rows: DatasetRow[];
}

export interface DatasetRow {
  timestamp: string;
  equipment_id: string;
  metric: string;
  value: number;
  unit: string;
}

export interface PidEvidence {
  source_id: string;
  type: "pid_drawing";
  filename: string;
  highlighted_component: string;
  connections: string[];
  view_url: string;
}

export type EvidenceSource = DocumentEvidence | DatasetEvidence | PidEvidence;

// ─── Findings & Report ─────────────────────────────────────────────

export type FindingVerificationStatus =
  | "supported"
  | "partially_supported"
  | "unsupported";

export type VerificationStatus =
  | "verified"
  | "partially_verified"
  | "unverified";

export type OverallStatus =
  | "attention_required"
  | "normal"
  | "critical";

export interface Finding {
  id: string;
  title: string;
  detail: string;
  verification_status: FindingVerificationStatus;
  evidence: EvidenceReference[];
}

export interface Report {
  investigation_id: string;
  query: string;
  overall_status: OverallStatus;
  condition_summary: string;
  findings: Finding[];
  pid_relationship: string[] | null;
  conclusion: string;
  confidence: number;
  verification_status: VerificationStatus;
  generated_at: string;
}

// ─── Export ─────────────────────────────────────────────────────────

export interface ExportResponse {
  export_id: string;
  download_url: string;
}

// ─── Audit ──────────────────────────────────────────────────────────

export interface AuditEntry {
  investigation_id: string;
  user: string;
  department: string;
  query: string;
  agents_invoked: AgentName[];
  verification_status: VerificationStatus;
  confidence: number;
  timestamp: string;
}

export interface AuditResponse {
  entries: AuditEntry[];
  total: number;
}

// ─── Errors ─────────────────────────────────────────────────────────

export interface APIError {
  error: {
    code: string;
    message: string;
    status: number;
  };
}

// ─── SSE Event Types ────────────────────────────────────────────────

export interface SSEInvestigationComplete {
  investigation_id: string;
  report_url: string;
}

export interface SSEInsufficientEvidence {
  investigation_id: string;
  message: string;
}

// ─── Chat ───────────────────────────────────────────────────────────

export interface ChatAttachment {
  filename: string;
  url: string;
  type: "document" | "image";
  extracted_text?: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  attachments: ChatAttachment[];
  created_at: string;
}

export interface Conversation {
  id: string;
  title: string;
  type: "general" | "report";
  investigation_id?: string;
  created_at: string;
  updated_at: string;
  last_message?: string;
}

export interface ConversationDetail {
  id: string;
  title: string;
  type: "general" | "report";
  investigation_id?: string;
  created_at: string;
  updated_at: string;
  messages: ChatMessage[];
}

// ─── Investigation Summary (Dashboard) ──────────────────────────────

export interface InvestigationSummary {
  id: string;
  query: string;
  status: string;
  condition_summary: string;
  confidence: number | null;
  verification_status: string | null;
  created_at: string;
  completed_at: string | null;
}
