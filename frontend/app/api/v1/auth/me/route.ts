import { NextResponse } from "next/server";
import { proxyOrFallback } from "../../proxy";

export async function GET(req: Request) {
  return proxyOrFallback("/auth/me", req, () => NextResponse.json(
    { detail: "Local authentication service is unavailable." }, { status: 503 }
  ));
}
