import { NextResponse } from "next/server";
import { mockChatFiles } from "../../../../mock-data";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000/api/v1";

export async function GET(
  req: Request,
  props: { params: Promise<{ source_id: string }> }
) {
  const { source_id } = await props.params;

  // 1. Try forwarding to backend if available
  try {
    const ctrl = new AbortController();
    const t = setTimeout(() => ctrl.abort(), 2000);
    const backendRes = await fetch(`${BACKEND_URL}/evidence/files/${encodeURIComponent(source_id)}/raw`, {
      method: "GET",
      headers: {
        ...(req.headers.get("authorization")
          ? { Authorization: req.headers.get("authorization")! }
          : {}),
      },
      signal: ctrl.signal,
    });
    clearTimeout(t);
    if (backendRes.ok) {
      return backendRes;
    }
  } catch {
    // Fall back to local mock store
  }

  // 2. Check mock files store
  const stored = mockChatFiles[source_id];
  if (stored && stored.dataBase64) {
    const buffer = Buffer.from(stored.dataBase64, "base64");
    return new NextResponse(buffer, {
      status: 200,
      headers: {
        "Content-Type": stored.contentType || "application/octet-stream",
        "Content-Disposition": `inline; filename="${stored.filename}"`,
        "Content-Length": buffer.length.toString(),
      },
    });
  }

  // Also check by filename in mockChatFiles
  for (const key of Object.keys(mockChatFiles)) {
    if (key.includes(source_id)) {
      const file = mockChatFiles[key];
      if (file.dataBase64) {
        const buffer = Buffer.from(file.dataBase64, "base64");
        return new NextResponse(buffer, {
          status: 200,
          headers: {
            "Content-Type": file.contentType || "application/octet-stream",
            "Content-Disposition": `inline; filename="${file.filename}"`,
            "Content-Length": buffer.length.toString(),
          },
        });
      }
    }
  }

  return NextResponse.json(
    {
      error: {
        code: "FILE_NOT_FOUND",
        message: `Evidence file ${source_id} not found.`,
        status: 404,
      },
    },
    { status: 404 }
  );
}
