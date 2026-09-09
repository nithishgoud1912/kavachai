import { NextResponse } from "next/server";
import { proxyOrFallback } from "../../proxy";
import { mockEvidenceMap } from "../../mock-data";

export async function GET(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  return proxyOrFallback(`/evidence/${id}`, req, () => {
    return NextResponse.json({ detail: "Evidence not found" }, { status: 404 });
  });
}
