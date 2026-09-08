const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000/api/v1";

export async function proxyOrFallback(
  path: string,
  req: Request,
  fallback: (rawBody?: string, parsedJson?: any) => Promise<Response> | Response
): Promise<Response> {
  let rawBody: string | undefined;
  let parsedJson: any = null;

  if (req.method !== "GET" && req.method !== "HEAD") {
    try {
      rawBody = await req.text();
      if (rawBody) {
        try {
          parsedJson = JSON.parse(rawBody);
        } catch {}
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
      body: rawBody,
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    // If backend replied (2xx, 3xx, 4xx, or 5xx), return the actual backend response
    return res;
  } catch (err) {
    console.warn(`[Proxy] Backend at ${BACKEND_URL}${path} unreachable, falling back to mock:`, err);
    return fallback(rawBody, parsedJson);
  }
}
