import { NextResponse } from "next/server";
import { proxyOrFallback } from "../../proxy";

export async function POST(req: Request) {
  return proxyOrFallback("/knowledge-base/documents", req, () => {
    return NextResponse.json(
      {
        document_id: `doc_${Math.random().toString(36).substring(2, 6)}`,
        status: "processing",
        chunks_expected: true,
      },
      { status: 202 }
    );
  });
}
