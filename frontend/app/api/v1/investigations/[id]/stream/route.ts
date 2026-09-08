export const dynamic = "force-dynamic";

export async function GET(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
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
            message: "Decomposing query into sub-tasks...",
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
            message: "Scanning inspection reports for P-102...",
            elapsed_ms: 600,
          },
          delay: 600,
        },
        {
          event: "agent_update",
          data: {
            agent: "document_agent",
            status: "complete",
            message: "Found 4 inspection reports (Jan, Apr, Jul)",
            elapsed_ms: 1100,
          },
          delay: 700,
        },
        {
          event: "agent_update",
          data: {
            agent: "data_agent",
            status: "working",
            message: "Computing vibration trend Jan–Jul (deterministic)...",
            elapsed_ms: 1400,
          },
          delay: 600,
        },
        {
          event: "agent_update",
          data: {
            agent: "data_agent",
            status: "complete",
            message: "Vibration increase: 2.1 → 3.7 mm/s (+76%)",
            elapsed_ms: 1850,
          },
          delay: 700,
        },
        {
          event: "agent_update",
          data: {
            agent: "vision_agent",
            status: "working",
            message: "Analyzing P&ID refinery schematic for P-102...",
            elapsed_ms: 2100,
          },
          delay: 600,
        },
        {
          event: "agent_update",
          data: {
            agent: "vision_agent",
            status: "complete",
            message: "Verified P&ID line: T-101 → P-102 → V-204 → R-101",
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
            message: "Advisory threshold: 3.0 mm/s (Breached)",
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
            message: "2 findings verified supported, 91% confidence",
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
