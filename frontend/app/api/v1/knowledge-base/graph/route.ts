import { NextResponse } from "next/server";
import { proxyOrFallback } from "../../proxy";

export async function GET(req: Request) {
  return proxyOrFallback("/knowledge-base/graph", req, async () => {
    return NextResponse.json({
      nodes: [
        { id: "T-101", type: "tank", label: "Crude Storage Tank T-101" },
        { id: "P-102", type: "pump", label: "Charge Pump P-102" },
        { id: "V-204", type: "valve", label: "Control Valve V-204" },
        { id: "R-101", type: "reactor", label: "Hydrotreater Reactor R-101" },
      ],
      edges: [
        { source: "T-101", target: "P-102", relationship: "suction_line", type: "pipe" },
        { source: "P-102", target: "V-204", relationship: "discharge_line", type: "pipe" },
        { source: "V-204", target: "R-101", relationship: "feed_line", type: "pipe" },
      ],
    });
  });
}
