import { NextResponse } from "next/server";
import { proxyOrFallback } from "../../../proxy";

export async function GET(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  return proxyOrFallback(`/knowledge-base/documents/${encodeURIComponent(id)}`, req, async () => {
    return NextResponse.json({
      document_id: id,
      filename: `${id}.pdf`,
      document_type: "inspection_report",
      page_count: 5,
      chunk_count: 12,
      status: "ready",
      created_at: new Date().toISOString(),
    });
  });
}
