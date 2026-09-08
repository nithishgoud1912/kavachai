import { NextResponse } from "next/server";
import { proxyOrFallback } from "../proxy";
import { mockAuditEntries } from "../mock-data";

export async function GET(req: Request) {
  return proxyOrFallback("/audit-log", req, () => {
    return NextResponse.json({
      entries: mockAuditEntries,
      total: mockAuditEntries.length,
    });
  });
}
