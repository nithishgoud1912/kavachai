export const dynamic = "force-dynamic";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000/api/v1";

export async function GET(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;

  // 1. Try to proxy live SSE stream from the FastAPI backend
  try {
    const targetUrl = `${BACKEND_URL}/investigations/${id}/stream`;
    const headers: Record<string, string> = {
      Accept: "text/event-stream",
    };
    const auth = req.headers.get("authorization");
    if (auth) {
      headers["Authorization"] = auth;
    }

    const backendRes = await fetch(targetUrl, {
      headers,
      signal: req.signal,
    });

    if (backendRes.ok && backendRes.body) {
      return new Response(backendRes.body, {
        headers: {
          "Content-Type": "text/event-stream; charset=utf-8",
          "Cache-Control": "no-cache, no-transform",
          Connection: "keep-alive",
          "X-Accel-Buffering": "no",
        },
      });
    }
  } catch (err) {
    console.warn(`[Stream Proxy] Backend stream at ${BACKEND_URL}/investigations/${id}/stream unreachable:`, err);
  }

  // 2. Offline / disconnected fallback demo stream
  const encoder = new TextEncoder();
  let isClosed = false;

  const stream = new ReadableStream({
    async start(controller) {
      req.signal.addEventListener("abort", () => {
        isClosed = true;
        try {
          controller.close();
        } catch {}
      });

      const sendEvent = (event: string, data: unknown) => {
        if (isClosed) return;
        controller.enqueue(
          encoder.encode(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`)
        );
      };

      const steps = [
        {
          event: "agent_update",
          data: {
            agent: "planner",
            status: "working",
            message: "Decomposing query into sub-tasks (demo mode)...",
            elapsed_ms: 120,
          },
          delay: 200,
        },
        {
          event: "agent_update",
          data: {
            agent: "planner",
            status: "complete",
            message: "Decomposed into 4 agent sub-tasks",
            elapsed_ms: 450,
          },
          delay: 500,
        },
        {
          event: "agent_update",
          data: {
            agent: "document_agent",
            status: "working",
            message: "Scanning inspection reports for equipment...",
            elapsed_ms: 600,
          },
          delay: 600,
        },
        {
          event: "agent_update",
          data: {
            agent: "document_agent",
            status: "complete",
            message: "Found inspection reports in knowledge base",
            elapsed_ms: 1100,
          },
          delay: 700,
        },
        {
          event: "agent_update",
          data: {
            agent: "data_agent",
            status: "working",
            message: "Computing telemetry trend (deterministic)...",
            elapsed_ms: 1400,
          },
          delay: 600,
        },
        {
          event: "agent_update",
          data: {
            agent: "data_agent",
            status: "complete",
            message: "Telemetry trend analysis complete",
            elapsed_ms: 1850,
          },
          delay: 700,
        },
        {
          event: "agent_update",
          data: {
            agent: "vision_agent",
            status: "working",
            message: "Analyzing P&ID refinery schematic...",
            elapsed_ms: 2100,
          },
          delay: 600,
        },
        {
          event: "agent_update",
          data: {
            agent: "vision_agent",
            status: "complete",
            message: "Verified P&ID connectivity chain",
            elapsed_ms: 2600,
          },
          delay: 700,
        },
        {
          event: "agent_update",
          data: {
            agent: "rag_agent",
            status: "working",
            message: "Retrieving OEM operating limits from manual...",
            elapsed_ms: 2850,
          },
          delay: 500,
        },
        {
          event: "agent_update",
          data: {
            agent: "rag_agent",
            status: "complete",
            message: "Operating threshold retrieved",
            elapsed_ms: 3200,
          },
          delay: 600,
        },
        {
          event: "agent_update",
          data: {
            agent: "verification_agent",
            status: "working",
            message: "Cross-verifying findings against evidence bundle...",
            elapsed_ms: 3500,
          },
          delay: 700,
        },
        {
          event: "agent_update",
          data: {
            agent: "verification_agent",
            status: "complete",
            message: "Findings verified against knowledge base",
            elapsed_ms: 3950,
          },
          delay: 600,
        },
        {
          event: "investigation_complete",
          data: {
            investigation_id: id,
            report_url: `/report/${id}`,
          },
          delay: 400,
        },
      ];

      for (const step of steps) {
        if (isClosed) break;
        await new Promise((r) => setTimeout(r, step.delay));
        if (isClosed) break;
        sendEvent(step.event, step.data);
      }

      if (!isClosed) {
        try {
          controller.close();
        } catch {}
      }
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream; charset=utf-8",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
      "X-Accel-Buffering": "no",
    },
  });
}
