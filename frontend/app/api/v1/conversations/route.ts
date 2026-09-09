import { NextResponse } from "next/server";
import { proxyOrFallback } from "../proxy";
import { mockConversations, mockConversationMessages } from "../mock-data";
import type { Conversation } from "@/app/types";

export async function GET(req: Request) {
  return proxyOrFallback("/conversations", req, () => {
    try {
      const url = new URL(req.url);
      const type = url.searchParams.get("type");
      const investigationId = url.searchParams.get("investigation_id");

      let filtered = [...mockConversations];
      if (type) {
        filtered = filtered.filter((c) => c.type === type);
      }
      if (investigationId) {
        filtered = filtered.filter((c) => c.investigation_id === investigationId);
      }

      // Sort by updated_at desc
      filtered.sort(
        (a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
      );

      return NextResponse.json(filtered);
    } catch {
      return NextResponse.json([]);
    }
  });
}

export async function POST(req: Request) {
  return proxyOrFallback("/conversations", req, async (_raw, parsedJson) => {
    try {
      const body = parsedJson || {};
      const id = `conv_${Math.random().toString(36).substring(2, 11)}`;
      const now = new Date().toISOString();

      const newConv: Conversation = {
        id,
        title: body.title || "New Chat",
        type: body.type === "report" ? "report" : "general",
        investigation_id: body.investigation_id || undefined,
        created_at: now,
        updated_at: now,
      };

      mockConversations.unshift(newConv);
      mockConversationMessages[id] = [];

      return NextResponse.json(newConv, { status: 201 });
    } catch {
      return NextResponse.json(
        {
          error: {
            code: "INVALID_REQUEST",
            message: "Failed to create conversation.",
            status: 400,
          },
        },
        { status: 400 }
      );
    }
  });
}
