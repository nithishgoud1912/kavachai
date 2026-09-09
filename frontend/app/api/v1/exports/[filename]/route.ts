import { NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000/api/v1";

export async function GET(
  req: Request,
  { params }: { params: Promise<{ filename: string }> }
) {
  const { filename } = await params;

  // Sanitize filename
  if (!filename || !/^exp_[a-zA-Z0-9_\-]+\.pdf$/.test(filename)) {
    return new Response("Invalid filename", { status: 400 });
  }

  try {
    const targetUrl = `${BACKEND_URL}/exports/${encodeURIComponent(filename)}`;
    const headers = new Headers();
    req.headers.forEach((value, key) => {
      if (key.toLowerCase() !== "host" && key.toLowerCase() !== "content-length") {
        headers.set(key, value);
      }
    });

    const res = await fetch(targetUrl, {
      method: "GET",
      headers,
    });

    if (res.ok) {
      const blob = await res.blob();
      return new Response(blob, {
        headers: {
          "Content-Type": "application/pdf",
          "Content-Disposition": `attachment; filename="${filename}"`,
          "Cache-Control": "public, max-age=3600",
        },
      });
    }

    return new Response(`Export report ${filename} not found on server`, { status: res.status });
  } catch (err) {
    console.error("[Proxy] Failed to fetch exported PDF:", err);
    return new Response("Export report unavailable", { status: 502 });
  }
}
