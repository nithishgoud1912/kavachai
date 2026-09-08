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
    const timeoutId = setTimeout(() => controller.abort(), 400); // 400ms fast check

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

    if (res.ok || res.status < 500) {
      return res;
    }
    return fallback(rawBody, parsedJson);
  } catch {
    return fallback(rawBody, parsedJson);
  }
}
