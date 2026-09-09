const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000/api/v1";

export async function proxyOrFallback(
  path: string,
  req: Request,
  fallback: (rawBody?: string, parsedJson?: any) => Promise<Response> | Response
): Promise<Response> {
  const contentType = req.headers.get("content-type") || "";
  const isMultipart = contentType.includes("multipart/form-data");
  let bodyBuffer: Buffer | undefined;
  let rawBodyText: string | undefined;
  let parsedJson: any = null;

  if (req.method !== "GET" && req.method !== "HEAD") {
    try {
      if (isMultipart) {
        bodyBuffer = Buffer.from(await req.arrayBuffer());
      } else {
        rawBodyText = await req.text();
        if (rawBodyText) {
          try {
            parsedJson = JSON.parse(rawBodyText);
          } catch {}
        }
      }
    } catch {}
  }

  try {
    const controller = new AbortController();
    // 60-second timeout to allow local LLM inference
    const timeoutId = setTimeout(() => controller.abort(), 60000);

    const headers = new Headers();
    req.headers.forEach((value, key) => {
      if (key.toLowerCase() !== "host" && key.toLowerCase() !== "content-length") {
        headers.set(key, value);
      }
    });

    const targetUrl = `${BACKEND_URL}${path}`;

    const res = await fetch(targetUrl, {
      method: req.method,
      headers,
      body: (isMultipart ? bodyBuffer : rawBodyText) as any,
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    // Return the real backend response directly
    return res;
  } catch (err) {
    console.warn(`[Proxy] Backend at ${BACKEND_URL}${path} unreachable:`, err);
    return fallback(rawBodyText, parsedJson);
  }
}
