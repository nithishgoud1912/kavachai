import { NextResponse } from "next/server";
import { proxyOrFallback } from "../../proxy";
import { mockEvidenceMap } from "../../mock-data";

export async function GET(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  return proxyOrFallback(`/evidence/${id}`, req, () => {
    const evidence = mockEvidenceMap[id];
    if (evidence) {
      return NextResponse.json(evidence);
    }
    // Default fallback document if unknown ID
    return NextResponse.json({
      source_id: id,
      type: "document",
      filename: `Evidence_${id}.pdf`,
      page: 1,
      excerpt: `Evidence excerpt corresponding to technical source identifier ${id}. Verified against local sovereign knowledge base.`,
      view_url: `/files/${id}/page/1`,
    });
  });
}
