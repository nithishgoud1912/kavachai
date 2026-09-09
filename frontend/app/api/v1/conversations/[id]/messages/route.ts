import { NextResponse } from "next/server";
import { proxyOrFallback } from "../../../proxy";
import {
  mockConversations,
  mockConversationMessages,
  generateMockAssistantResponse,
} from "../../../mock-data";
import type { ChatMessage, ChatAttachment } from "@/app/types";

export async function POST(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;

  return proxyOrFallback(
    `/conversations/${id}/messages`,
    req,
    async (_raw, parsedJson) => {
      try {
        const body = parsedJson || {};
        const content: string = (body.content || "").trim();
        const attachments: ChatAttachment[] = body.attachments || [];

        // Ensure conversation exists or create on the fly
        let conv = mockConversations.find((c) => c.id === id);
        const now = new Date().toISOString();

        if (!conv) {
          conv = {
            id,
            title: content.length > 60 ? content.substring(0, 60) + "…" : content || "New Chat",
            type: "general",
            created_at: now,
            updated_at: now,
          };
          mockConversations.unshift(conv);
          mockConversationMessages[id] = [];
        }

        if (!mockConversationMessages[id]) {
          mockConversationMessages[id] = [];
        }

        // Auto-title conversation if still default
        if (conv.title === "New Chat" && content) {
          conv.title = content.length > 60 ? content.substring(0, 60) + "…" : content;
        }

        // Add user message to history
        const userMsg: ChatMessage = {
          id: `msg_user_${Date.now()}`,
          role: "user",
          content,
          attachments,
          created_at: now,
        };
        mockConversationMessages[id].push(userMsg);

        // Generate intelligent assistant response
        const assistantContent = generateMockAssistantResponse(
          conv.type,
          content,
          attachments,
          conv.investigation_id
        );

        const assistantMsg: ChatMessage = {
          id: `msg_asst_${Date.now()}`,
          role: "assistant",
          content: assistantContent,
          attachments: [],
          created_at: new Date().toISOString(),
        };

        mockConversationMessages[id].push(assistantMsg);
        conv.updated_at = assistantMsg.created_at;
        conv.last_message = assistantContent.substring(0, 100);

        return NextResponse.json(assistantMsg);
      } catch {
        return NextResponse.json(
          {
            error: {
              code: "FAILED_TO_PROCESS_MESSAGE",
              message: "Failed to generate AI response. Please try again.",
              status: 500,
            },
          },
          { status: 500 }
        );
      }
    }
  );
}
