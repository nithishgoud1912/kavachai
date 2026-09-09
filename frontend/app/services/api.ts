import type {
  Session,
  SessionRevokeResponse,
  KnowledgeBaseSummary,
  KnowledgeBaseGraph,
  DocumentDetail,
  Investigation,
  InvestigationPlan,
  Report,
  EvidenceSource,
  ExportResponse,
  AuditResponse,
  APIError,
  Conversation,
  ConversationDetail,
  ChatAttachment,
  ChatMessage,
  InvestigationSummary,
  AttachmentItem,
} from "@/app/types";

export type { AttachmentItem };

// Response type aliases for chat endpoints
type ChatMessageItem = ChatMessage;
type UploadedFile = {
  filename: string;
  url: string;
  type: string;
  extracted_text_preview: string | null;
};

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "/api/v1";

// ─── Error Handling ─────────────────────────────────────────────────

export class KavachAIAPIError extends Error {
  code: string;
  status: number;

  constructor(apiError: APIError["error"]) {
    super(apiError.message);
    this.name = "KavachAIAPIError";
    this.code = apiError.code;
    this.status = apiError.status;
  }
}

const ERROR_MESSAGES: Record<number, string> = {
  400: "Invalid request. Please check your input.",
  401: "Session expired. Please log in again.",
  403: "You do not have permission to access this resource.",
  404: "The requested resource was not found.",
  422: "Validation error. Please check your input.",
  500: "An internal error occurred. Please try again.",
};

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let apiError: APIError["error"];
    try {
      const body = await response.json();
      apiError = body.error || {
        code: "UNKNOWN_ERROR",
        message: ERROR_MESSAGES[response.status] || "An unexpected error occurred.",
        status: response.status,
      };
    } catch {
      apiError = {
        code: "UNKNOWN_ERROR",
        message: ERROR_MESSAGES[response.status] || "An unexpected error occurred.",
        status: response.status,
      };
    }
    throw new KavachAIAPIError(apiError);
  }
  return response.json();
}

function getAuthHeaders(): HeadersInit {
  if (typeof window === "undefined") return {};
  const sessionId = sessionStorage.getItem("kavachai_session_id");
  if (sessionId) {
    return { Authorization: `Bearer ${sessionId}` };
  }
  return {};
}

// ─── Session ────────────────────────────────────────────────────────

export async function createSession(
  name: string,
  department: string
): Promise<Session> {
  const res = await fetch(`${API_BASE}/session`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
    body: JSON.stringify({ name, department }),
    credentials: "include",
  });
  return handleResponse<Session>(res);
}

export async function getCurrentSession(): Promise<Session> {
  const res = await fetch(`${API_BASE}/session/me`, {
    headers: { ...getAuthHeaders() },
    credentials: "include",
  });
  return handleResponse<Session>(res);
}

export async function revokeSession(sessionId?: string): Promise<SessionRevokeResponse> {
  const res = await fetch(`${API_BASE}/session/revoke`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
    body: JSON.stringify(sessionId ? { session_id: sessionId } : {}),
    credentials: "include",
  });
  return handleResponse<SessionRevokeResponse>(res);
}

// ─── Knowledge Base ─────────────────────────────────────────────────

export async function getKnowledgeBaseSummary(): Promise<KnowledgeBaseSummary> {
  const res = await fetch(`${API_BASE}/knowledge-base/summary`, {
    headers: { ...getAuthHeaders() },
    credentials: "include",
  });
  return handleResponse<KnowledgeBaseSummary>(res);
}

export async function getKnowledgeBaseGraph(): Promise<KnowledgeBaseGraph> {
  const res = await fetch(`${API_BASE}/knowledge-base/graph`, {
    headers: { ...getAuthHeaders() },
    credentials: "include",
  });
  return handleResponse<KnowledgeBaseGraph>(res);
}

export async function getDocument(documentId: string): Promise<DocumentDetail> {
  const res = await fetch(`${API_BASE}/knowledge-base/documents/${encodeURIComponent(documentId)}`, {
    headers: { ...getAuthHeaders() },
    credentials: "include",
  });
  return handleResponse<DocumentDetail>(res);
}

export async function uploadDocument(formData: FormData): Promise<{ document_id: string; status: string }> {
  const res = await fetch(`${API_BASE}/knowledge-base/documents`, {
    method: "POST",
    headers: { ...getAuthHeaders() },
    body: formData,
    credentials: "include",
  });
  return handleResponse(res);
}

export async function uploadDataset(formData: FormData): Promise<{ dataset_id: string; status: string }> {
  const res = await fetch(`${API_BASE}/knowledge-base/datasets`, {
    method: "POST",
    headers: { ...getAuthHeaders() },
    body: formData,
    credentials: "include",
  });
  return handleResponse(res);
}

// ─── Investigations ─────────────────────────────────────────────────

export async function uploadInvestigationFiles(
  files: File[],
  paths?: string[]
): Promise<AttachmentItem[]> {
  const formData = new FormData();
  files.forEach((f) => formData.append("files", f));
  if (paths && paths.length > 0) {
    formData.append("paths", JSON.stringify(paths));
  }
  const res = await fetch(`${API_BASE}/investigations/upload`, {
    method: "POST",
    headers: { ...getAuthHeaders() },
    body: formData,
    credentials: "include",
  });
  const data = await handleResponse<{ files?: any[]; uploaded?: any[]; total_files: number }>(res);
  return (data.files || data.uploaded || []) as AttachmentItem[];
}

export async function createInvestigation(
  query: string,
  sessionId: string,
  attachments: any[] = []
): Promise<Investigation> {
  const res = await fetch(`${API_BASE}/investigations`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
    body: JSON.stringify({ query, session_id: sessionId, attachments }),
    credentials: "include",
  });
  return handleResponse<Investigation>(res);
}

export async function getReport(
  investigationId: string
): Promise<Report> {
  const res = await fetch(
    `${API_BASE}/investigations/${investigationId}/report`,
    {
      headers: { ...getAuthHeaders() },
      credentials: "include",
    }
  );
  return handleResponse<Report>(res);
}

export async function getPlan(
  investigationId: string
): Promise<InvestigationPlan> {
  const res = await fetch(
    `${API_BASE}/investigations/${investigationId}/plan`,
    {
      headers: { ...getAuthHeaders() },
      credentials: "include",
    }
  );
  return handleResponse<InvestigationPlan>(res);
}

// ─── Evidence ───────────────────────────────────────────────────────

export async function getEvidence(
  sourceId: string
): Promise<EvidenceSource> {
  const res = await fetch(`${API_BASE}/evidence/${sourceId}`, {
    headers: { ...getAuthHeaders() },
    credentials: "include",
  });
  return handleResponse<EvidenceSource>(res);
}

// ─── Export ─────────────────────────────────────────────────────────

export async function exportReport(
  investigationId: string,
  format: string = "pdf"
): Promise<ExportResponse> {
  const res = await fetch(
    `${API_BASE}/investigations/${investigationId}/export`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json", ...getAuthHeaders() },
      body: JSON.stringify({ format }),
      credentials: "include",
    }
  );
  return handleResponse<ExportResponse>(res);
}

// ─── Audit Log ──────────────────────────────────────────────────────

export async function getAuditLog(
  limit: number = 50,
  offset: number = 0
): Promise<AuditResponse> {
  const res = await fetch(
    `${API_BASE}/audit-log?limit=${limit}&offset=${offset}`,
    {
      headers: { ...getAuthHeaders() },
      credentials: "include",
    }
  );
  return handleResponse<AuditResponse>(res);
}

// ─── SSE URL Builder ────────────────────────────────────────────────

export function getStreamUrl(investigationId: string): string {
  return `${API_BASE}/investigations/${investigationId}/stream`;
}

// ─── Download helper ────────────────────────────────────────────────

export function getDownloadUrl(path: string): string {
  // If path starts with /, it's relative to the API base host
  if (path.startsWith("/")) {
    if (API_BASE.startsWith("http")) {
      try {
        const url = new URL(API_BASE);
        return `${url.origin}${path}`;
      } catch {
        return path;
      }
    }
    return path;
  }
  return path;
}

// ─── Chat Conversations ─────────────────────────────────────────────

export async function getConversations(
  type?: string,
  investigationId?: string
): Promise<Conversation[]> {
  const params = new URLSearchParams();
  if (type) params.set("type", type);
  if (investigationId) params.set("investigation_id", investigationId);
  const qs = params.toString();
  const res = await fetch(
    `${API_BASE}/conversations${qs ? `?${qs}` : ""}`,
    {
      headers: { ...getAuthHeaders() },
      credentials: "include",
    }
  );
  return handleResponse<Conversation[]>(res);
}

export async function createConversation(data: {
  session_id: string;
  title?: string;
  type?: string;
  investigation_id?: string;
}): Promise<Conversation> {
  const res = await fetch(`${API_BASE}/conversations`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
    body: JSON.stringify(data),
    credentials: "include",
  });
  return handleResponse<Conversation>(res);
}

export async function getConversation(
  id: string
): Promise<ConversationDetail> {
  const res = await fetch(`${API_BASE}/conversations/${id}`, {
    headers: { ...getAuthHeaders() },
    credentials: "include",
  });
  return handleResponse<ConversationDetail>(res);
}

export async function deleteConversation(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/conversations/${encodeURIComponent(id)}`, {
    method: "DELETE",
    headers: { ...getAuthHeaders() },
    credentials: "include",
  });
  if (!res.ok && res.status !== 204) {
    throw new Error(`Failed to delete conversation: ${res.statusText}`);
  }
}

export async function sendChatMessage(
  conversationId: string,
  content: string,
  attachments: ChatAttachment[] = []
): Promise<ChatMessageItem> {
  const res = await fetch(
    `${API_BASE}/conversations/${conversationId}/messages`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json", ...getAuthHeaders() },
      body: JSON.stringify({ content, attachments }),
      credentials: "include",
    }
  );
  return handleResponse<ChatMessageItem>(res);
}

export async function uploadChatFile(
  formData: FormData
): Promise<UploadedFile> {
  const res = await fetch(`${API_BASE}/conversations/upload`, {
    method: "POST",
    headers: { ...getAuthHeaders() },
    body: formData,
    credentials: "include",
  });
  return handleResponse<UploadedFile>(res);
}

export async function uploadChatFilesBatch(
  files: File[],
  paths?: string[]
): Promise<AttachmentItem[]> {
  const formData = new FormData();
  files.forEach((f) => formData.append("files", f));
  if (paths && paths.length > 0) {
    formData.append("paths", JSON.stringify(paths));
  }
  const res = await fetch(`${API_BASE}/conversations/upload-batch`, {
    method: "POST",
    headers: { ...getAuthHeaders() },
    body: formData,
    credentials: "include",
  });
  if (!res.ok) throw new Error("Batch upload failed");
  const data = await res.json();
  return (data.uploaded || data.files || []) as AttachmentItem[];
}

// ─── Investigation List ─────────────────────────────────────────────

export async function getInvestigations(): Promise<InvestigationSummary[]> {
  const res = await fetch(`${API_BASE}/investigations`, {
    headers: { ...getAuthHeaders() },
    credentials: "include",
  });
  return handleResponse<InvestigationSummary[]>(res);
}
