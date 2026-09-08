import { NextResponse } from "next/server";
import { proxyOrFallback } from "../proxy";

export async function POST(req: Request) {
  return proxyOrFallback("/session", req, async (_raw, parsedJson) => {
    try {
      const body = parsedJson || {};
      const name = body.name || "Abhinay Boya";
      const department = body.department || "HSE";
      const sessionId = `sess_${Math.random().toString(36).substring(2, 11)}`;
      const issuedAt = new Date().toISOString();

      const response = NextResponse.json({
        session_id: sessionId,
        name,
        department,
        issued_at: issuedAt,
      });

      // Set session cookie
      response.cookies.set("kavachai_session_id", sessionId, {
        path: "/",
        httpOnly: true,
        sameSite: "lax",
      });

      return response;
    } catch {
      return NextResponse.json(
        {
          error: {
            code: "INVALID_REQUEST",
            message: "Failed to parse session request.",
            status: 400,
          },
        },
        { status: 400 }
      );
    }
  });
}
