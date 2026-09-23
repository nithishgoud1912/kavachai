import { NextResponse } from "next/server";
import { proxyOrFallback } from "../../../proxy";

export async function POST(req: Request) {
  return proxyOrFallback("/auth/mfa/verify", req, () => NextResponse.json(
    { detail: "Local authentication service is unavailable." }, { status: 503 }
  ));
}
