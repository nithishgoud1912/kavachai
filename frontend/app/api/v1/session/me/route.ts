import { NextResponse } from "next/server";
import { proxyOrFallback } from "../../proxy";

export async function GET(req: Request) {
  return proxyOrFallback("/session/me", req, async () => {
    // Fallback: check cookie or return mock session
    const cookieHeader = req.headers.get("cookie") || "";
    const match = cookieHeader.match(/kavachai_session_id=([^;]+)/);
    const sessionId = match ? match[1] : "sess_mock";

    return NextResponse.json({
      session_id: sessionId,
      name: "Priya",
      department: "HSE",
      issued_at: new Date().toISOString(),
      expires_at: new Date(Date.now() + 24 * 3600 * 1000).toISOString(),
    });
  });
}
