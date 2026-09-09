import type {
  KnowledgeBaseSummary,
  InvestigationPlan,
  Report,
  EvidenceSource,
  AuditEntry,
  InvestigationSummary,
  Conversation,
  ChatMessage,
  ChatAttachment,
} from "@/app/types";

export const mockSummary: KnowledgeBaseSummary = {
  documents: 0,
  datasets: 0,
  pid_drawings: 0,
};

export const mockDefaultPlan: InvestigationPlan = {
  investigation_id: "",
  sub_tasks: [],
};

export const mockDefaultReport: Report = {
  investigation_id: "",
  query: "",
  overall_status: "normal",
  condition_summary: "No report available.",
  findings: [],
  pid_relationship: [],
  conclusion: "",
  confidence: 0,
  verification_status: "unverified",
  generated_at: new Date().toISOString(),
};

export const mockEvidenceMap: Record<string, EvidenceSource> = {};

export const mockAuditEntries: AuditEntry[] = [];

export const mockInvestigationSummaries: InvestigationSummary[] = [];

export const mockConversations: Conversation[] = [];
export const mockConversationMessages: Record<string, ChatMessage[]> = {};

export interface StoredChatFile {
  filename: string;
  url: string;
  type: "document" | "image";
  extracted_text: string;
  dataBase64?: string;
  contentType?: string;
}

export const mockChatFiles: Record<string, StoredChatFile> = {};

export function generateMockAssistantResponse(..._args: any[]): string {
  return "The AI backend server is not connected. Please ensure the backend server is running.";
}
