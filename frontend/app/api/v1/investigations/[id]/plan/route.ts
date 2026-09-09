import { NextResponse } from "next/server";
import { proxyOrFallback } from "../../../proxy";
import { mockDefaultPlan } from "../../../mock-data";

export async function GET(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  return proxyOrFallback(`/investigations/${id}/plan`, req, () => {
    return NextResponse.json({ detail: "Plan not found" }, { status: 404 });
  });
}
