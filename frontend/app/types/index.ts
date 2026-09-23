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
  expires_at?: string | null;
}

export interface SessionRevokeResponse {
  session_id: string;
  revoked: boolean;
  message: string;
}

// ─── Knowledge Base ────────────────────────────────────────────────

export interface KnowledgeBaseSummary {
  documents: number;
  datasets: number;
  pid_drawings: number;
}

export interface GraphNode {
  id: string;
  type?: string;
  label?: string;
  description?: string;
  metadata?: Record<string, unknown>;
}

export interface GraphEdge {
  source: string;
  target: string;
  relationship?: string;
  type?: string;
  metadata?: Record<string, unknown>;
}

export interface KnowledgeBaseGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface DocumentDetail {
  document_id: string;
  filename: string;
  document_type: string;
  page_count: number;
  chunk_count: number;
  status: string;
  created_at: string;
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
  view_url?: string;
  visual_description?: string;
  bounding_box?: number[] | null;
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

export interface TopologyNode {
  tag: string;
  name: string;
  role: string;
  spec: string;
  status: string;
}

export interface BypassLoop {
  tag: string;
  name: string;
  from_node: string;
  to_node: string;
  purpose: string;
}

export interface Report {
  investigation_id: string;
  query: string;
  overall_status: OverallStatus;
  condition_summary: string;
  findings: Finding[];
  pid_relationship: string[] | null;
  vision_observation?: string | null;
  bounding_box?: number[] | null;
  telemetry_trend?: { label: string; value: number; unit: string }[] | null;
  process_topology?: TopologyNode[] | null;
  bypass_loops?: BypassLoop[] | null;
  conclusion: string;
  confidence: number;
  verification_status: VerificationStatus;
  attachments?: AttachmentItem[];
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

// ─── Attachments & Uploads ──────────────────────────────────────────

export interface AttachmentItem {
  filename: string;
  url: string;
  type: "document" | "image" | string;
  extracted_text?: string;
  relative_path?: string;
  source_id?: string;
  size?: number;
}

// ─── Chat ───────────────────────────────────────────────────────────

export interface ChatAttachment {
  filename: string;
  url: string;
  type: "document" | "image" | string;
  extracted_text?: string;
  relative_path?: string;
  source_id?: string;
  size?: number;
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

// ─── Sovereign Workbench Core Types ─────────────────────────────────

export type TaskMode = "auto" | "document" | "code" | "vision" | "spreadsheet";
export type DeliverableType = "word" | "ppt" | "excel" | "code" | "chat";
export type TaskStatus =
  | "queued"
  | "planning"
  | "running"
  | "awaiting_review"
  | "complete"
  | "failed";

export interface SubTaskItem {
  id: string;
  goal: string;
  assigned_model: string;
  task_type: string;
  status: "pending" | "running" | "done" | "skipped" | "failed";
  started_at?: string;
  completed_at?: string;
  duration_ms?: number;
  error?: string;
}

export interface ToolCallEvent {
  id: string;
  subtask_id?: string;
  tool_name: string;
  category: "file" | "code_sandbox" | "doc_search" | "spreadsheet" | "ocr" | "vision";
  arguments: Record<string, unknown> | string;
  status: "running" | "completed" | "failed" | "blocked";
  started_at: string;
  duration_ms?: number;
  result_summary?: string;
  raw_output?: string;
  sandbox_result?: {
    exit_code: number;
    stdout: string;
    stderr: string;
    duration_ms: number;
    memory_mb?: number;
  };
}

export interface ArtifactItem {
  id: string;
  task_id: string;
  name: string;
  type: "docx" | "pptx" | "xlsx" | "code" | "image" | "pdf";
  size_bytes: number;
  created_at: string;
  model_used: string;
  download_url: string;
  preview_url?: string;
  metadata?: {
    pages?: number;
    slides?: number;
    rows?: number;
    language?: string;
    bounding_boxes?: { label: string; box_2d: number[]; confidence?: number }[];
    summary?: string;
    sources?: EvidenceReference[];
    sections?: { title: string; content: string }[];
    sheets?: { name: string; headers: string[]; data: (string | number)[][] }[];
    slides_data?: { title: string; points: string[]; speaker_notes?: string }[];
  };
}

export interface WorkbenchTask {
  id: string;
  query: string;
  mode: TaskMode;
  deliverable_type?: DeliverableType;
  status: TaskStatus;
  attachments: AttachmentItem[];
  plan: SubTaskItem[];
  tool_calls: ToolCallEvent[];
  reasoning_output: string;
  artifacts: ArtifactItem[];
  citations: EvidenceReference[];
  created_at: string;
  completed_at?: string;
  hitl_required?: boolean;
  hitl_status?: "pending" | "approved" | "revised" | "rejected";
  hitl_comments?: string;
  models_used: string[];
  confidence?: number;
}

// ─── Model Router Types ──────────────────────────────────────────────

export interface ModelRegistryEntry {
  id: string;
  name: string;
  display_name: string;
  provider: "ollama" | "vllm" | "local";
  size: string;
  quantization?: string;
  context_length: number;
  capabilities: ("reasoning" | "code" | "vision" | "embedding" | "extraction")[];
  status: "loaded" | "warm" | "cold" | "offline";
  vram_usage_gb: number;
  max_vram_gb: number;
  latency_p95_ms: number;
  endpoint: string;
}

export interface RoutingRule {
  id: string;
  task_type: string;
  preferred_model_id: string;
  fallback_model_id?: string;
  condition_description: string;
  enabled: boolean;
}

export interface RoutingDecisionLog {
  id: string;
  timestamp: string;
  task_id?: string;
  query_snippet: string;
  detected_intent: string;
  selected_model: string;
  reason: string;
  confidence: number;
}

// ─── Network Monitor & Sovereignty Types ────────────────────────────

export interface NetworkConnectionEntry {
  id: string;
  timestamp: string;
  destination: string;
  port: number;
  service: string;
  method: string;
  status: "allowed" | "blocked";
  latency_ms: number;
}

export interface EgressReport {
  total_connections: number;
  local_allowed: number;
  external_recorded: number;
  external_destinations: string[];
  sovereign: boolean;
  session_start: string;
  verified_airgap: boolean;
  allowlist: string[];
}

// ─── Code Sandbox Types ──────────────────────────────────────────────

export interface SandboxExecutionResult {
  id: string;
  code: string;
  language: string;
  exit_code: number;
  stdout: string;
  stderr: string;
  execution_time_ms: number;
  memory_peak_mb: number;
  blocked_imports?: string[];
  is_sandboxed: boolean;
  status: "success" | "runtime_error" | "security_blocked" | "timeout";
}

