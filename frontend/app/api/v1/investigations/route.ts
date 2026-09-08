import { NextResponse } from "next/server";
import { proxyOrFallback } from "../proxy";
import { mockAuditEntries } from "../mock-data";

export async function POST(req: Request) {
  return proxyOrFallback("/investigations", req, async (_raw, parsedJson) => {
    try {
      const body = parsedJson || {};
      const query = body.query || "Investigate Pump P-102 and determine whether its condition has deteriorated.";
      const investigationId = "inv_7788";

      // Append to audit log in memory
      mockAuditEntries.unshift({
        investigation_id: investigationId,
        user: "Abhinay Boya",
        department: "HSE",
        query,
        agents_invoked: ["planner", "document_agent", "data_agent", "vision_agent", "rag_agent", "verification_agent"],
        verification_status: "verified",
        confidence: 91,
        timestamp: new Date().toISOString(),
      });

      return NextResponse.json(
        {
          investigation_id: investigationId,
          status: "planning",
          stream_url: `/api/v1/investigations/${investigationId}/stream`,
        },
        { status: 202 }
      );
    } catch {
      return NextResponse.json(
        {
          error: {
            code: "INVALID_REQUEST",
            message: "Failed to initiate investigation.",
            status: 400,
          },
        },
        { status: 400 }
      );
    }
  });
}
