import { NextResponse } from "next/server";
import { proxyOrFallback } from "../../proxy";

export async function POST(req: Request) {
  return proxyOrFallback("/knowledge-base/datasets", req, () => {
    return NextResponse.json({
      dataset_id: "ds_4471",
      columns: ["timestamp", "equipment_id", "metric", "value", "unit"],
      row_count: 214,
      status: "ready",
    });
  });
}
