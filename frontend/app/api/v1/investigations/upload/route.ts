import { NextResponse } from "next/server";
import { proxyOrFallback } from "../../proxy";

export async function POST(req: Request) {
  return proxyOrFallback("/investigations/upload", req, () => {
    return NextResponse.json(
      {
        error: {
          code: "SERVICE_UNAVAILABLE",
          message: "Backend is unreachable for file uploads.",
          status: 503,
        },
      },
      { status: 503 }
    );
  });
}
