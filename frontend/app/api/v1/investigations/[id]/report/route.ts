import { NextResponse } from "next/server";
import { proxyOrFallback } from "../../../proxy";
import { mockDefaultReport } from "../../../mock-data";

export async function GET(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  return proxyOrFallback(`/investigations/${id}/report`, req, () => {
    return NextResponse.json({ detail: "Report not found" }, { status: 404 });
  });
}
