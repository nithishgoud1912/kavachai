import { NextResponse } from "next/server";
import { mockChatFiles } from "../../../mock-data";

export async function GET(
  _req: Request,
  { params }: { params: Promise<{ filename: string }> }
) {
  const { filename } = await params;
  const file = mockChatFiles[filename];

  if (!file || !file.dataBase64) {
    return new Response("File not found", { status: 404 });
  }

  const buffer = Buffer.from(file.dataBase64, "base64");

  return new Response(buffer, {
    headers: {
      "Content-Type": file.contentType || "application/octet-stream",
      "Content-Disposition": `inline; filename="${file.filename}"`,
      "Cache-Control": "public, max-age=3600",
    },
  });
}
