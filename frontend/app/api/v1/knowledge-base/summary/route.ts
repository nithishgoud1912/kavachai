import { NextResponse } from "next/server";
import { proxyOrFallback } from "../../proxy";
import { mockSummary } from "../../mock-data";

export async function GET(req: Request) {
  return proxyOrFallback("/knowledge-base/summary", req, () => {
    return NextResponse.json(mockSummary);
  });
}
