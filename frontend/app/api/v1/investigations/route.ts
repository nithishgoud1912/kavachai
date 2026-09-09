import { NextResponse } from "next/server";
import { proxyOrFallback } from "../proxy";
import { mockAuditEntries, mockInvestigationSummaries } from "../mock-data";

export async function GET(req: Request) {
  return proxyOrFallback("/investigations", req, () => {
    return NextResponse.json(mockInvestigationSummaries);
  });
}

export async function POST(req: Request) {
  return proxyOrFallback("/investigations", req, async () => {
    return NextResponse.json(
      {
        error: {
          code: "SERVICE_UNAVAILABLE",
          message: "Backend service is unreachable. Please ensure the backend is running.",
          status: 503,
        },
      },
      { status: 503 }
    );
  });
}
