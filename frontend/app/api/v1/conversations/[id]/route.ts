import { NextResponse } from "next/server";
import { proxyOrFallback } from "../../proxy";
import { mockConversations, mockConversationMessages } from "../../mock-data";

export async function GET(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;

  return proxyOrFallback(`/conversations/${id}`, req, () => {
    const conv = mockConversations.find((c) => c.id === id);
    if (!conv) {
      return NextResponse.json(
        {
          error: {
            code: "NOT_FOUND",
            message: "Conversation not found",
            status: 404,
          },
        },
        { status: 404 }
      );
    }

    const messages = mockConversationMessages[id] || [];

    return NextResponse.json({
      id: conv.id,
      title: conv.title,
      type: conv.type,
      investigation_id: conv.investigation_id,
      created_at: conv.created_at,
      updated_at: conv.updated_at,
      messages,
    });
  });
}

export async function DELETE(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;

  return proxyOrFallback(`/conversations/${id}`, req, () => {
    const idx = mockConversations.findIndex((c) => c.id === id);
    if (idx !== -1) {
      mockConversations.splice(idx, 1);
    }
    delete mockConversationMessages[id];
    return new Response(null, { status: 204 });
  });
}
