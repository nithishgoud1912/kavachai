import { NextResponse } from "next/server";
import { proxyOrFallback } from "../../proxy";

export async function POST(req: Request) {
  const res = await proxyOrFallback("/session/revoke", req, async (_raw, parsedJson) => {
    const body = parsedJson || {};
    const sessionId = body.session_id || "current";

    const response = NextResponse.json({
      session_id: sessionId,
      revoked: true,
      message: "Session has been successfully revoked.",
    });

    response.cookies.delete("kavachai_session_id");
    return response;
  });

  return res;
}
