const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8000/api/v1";

/** One transport path: backend errors remain errors; no simulated fallback. */
export async function proxyToBackend(req: Request): Promise<Response> {
  const url = new URL(req.url);
  const origin = req.headers.get("origin");
  if (!["GET", "HEAD", "OPTIONS"].includes(req.method) && origin && origin !== url.origin) {
    return Response.json({ detail: "Cross-origin request denied" }, { status: 403 });
  }
  const headers = new Headers();
  for (const key of ["authorization", "x-session-id", "content-type", "last-event-id"]) {
    const value = req.headers.get(key);
    if (value) headers.set(key, value);
  }
  const cookie = req.headers.get("cookie")?.split(";").map(v => v.trim()).find(v => v.startsWith("kavach_session="));
  if (!headers.has("authorization") && cookie) {
    try { headers.set("authorization", `Bearer ${decodeURIComponent(cookie.slice(15))}`); }
    catch { return Response.json({ detail: "Invalid session cookie" }, { status: 400 }); }
  }
  const path = url.pathname.replace(/^\/api\/v1/, "");
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 180000);
  req.signal.addEventListener("abort", () => controller.abort(), { once: true });
  try {
    let body: Uint8Array | undefined;
    if (!["GET", "HEAD"].includes(req.method) && req.body) {
      const reader = req.body.getReader();
      const chunks: Uint8Array[] = [];
      let size = 0;
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          size += value.byteLength;
          if (size > 24 * 1024 * 1024) {
            await reader.cancel();
            return Response.json({ detail: "Request too large" }, { status: 413 });
          }
          chunks.push(value);
        }
      } finally { reader.releaseLock(); }
      body = new Uint8Array(size);
      let offset = 0;
      for (const chunk of chunks) { body.set(chunk, offset); offset += chunk.byteLength; }
    }
    const result = await fetch(`${BACKEND_URL}${path}${url.search}`, {
      method: req.method, headers, body, signal: controller.signal, cache: "no-store",
    });
    const responseHeaders = new Headers();
    for (const key of ["content-type", "content-disposition"]) {
      const value = result.headers.get(key);
      if (value) responseHeaders.set(key, value);
    }
    responseHeaders.set("Cache-Control", "private, no-store");
    responseHeaders.set("X-Content-Type-Options", "nosniff");
    if (result.ok && ["/auth/login", "/auth/mfa/verify", "/session"].includes(path)) {
      const data = await result.clone().json();
      if (data.session_id && !data.mfa_required) responseHeaders.set("Set-Cookie",
        `kavach_session=${encodeURIComponent(data.session_id)}; HttpOnly; SameSite=Strict; Path=/;${url.protocol === "https:" ? " Secure;" : ""}`);
    }
    if (path === "/auth/logout" || path === "/session/revoke") responseHeaders.set("Set-Cookie", "kavach_session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0");
    return new Response(result.body, { status: result.status, headers: responseHeaders });
  } catch {
    return Response.json({ detail: "Local backend unavailable or request timed out" }, { status: 503 });
  } finally { clearTimeout(timer); }
}
