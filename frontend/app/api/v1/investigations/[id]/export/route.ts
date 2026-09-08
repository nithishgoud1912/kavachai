import { NextResponse } from "next/server";
import { proxyOrFallback } from "../../../proxy";

export async function POST(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  return proxyOrFallback(`/investigations/${id}/export`, req, () => {
    return NextResponse.json({
      export_id: "exp_331",
      download_url: `/api/v1/investigations/${id}/report`,
    });
  });
}
