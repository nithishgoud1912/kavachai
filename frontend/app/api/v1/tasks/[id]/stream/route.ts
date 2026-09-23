import { tasksStore } from "../../route";

export const dynamic = "force-dynamic";

export async function GET(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const task = tasksStore.get(id);

  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    async start(controller) {
      function send(event: string, data: any) {
        const payload = `event: ${event}\ndata: ${typeof data === "string" ? data : JSON.stringify(data)}\n\n`;
        controller.enqueue(encoder.encode(payload));
      }

      if (!task) {
        send("task_failed", { task_id: id, error: "Task not found" });
        controller.close();
        return;
      }

      // If task is already complete/awaiting review, stream its current plan and outputs in fast cadence
      send("plan_created", task.plan);

      for (const sub of task.plan) {
        send("subtask_started", { subtask_id: sub.id, model: sub.assigned_model });
        send("model_selected", {
          task_type: sub.task_type,
          model: sub.assigned_model,
          reason: `Auto-routed for ${sub.task_type} optimization`,
        });

        const relatedTool = task.tool_calls.find((t) => t.subtask_id === sub.id);
        if (relatedTool) {
          send("tool_call_started", relatedTool);
          send("tool_call_result", relatedTool);
        }

        send("subtask_completed", { subtask_id: sub.id, duration_ms: sub.duration_ms || 400 });
      }

      // Stream reasoning in chunks
      const chunks = task.reasoning_output.split("\n\n");
      for (const chunk of chunks) {
        send("output_delta", { delta: chunk + "\n\n" });
      }

      // Stream citations & artifacts
      for (const citation of task.citations) {
        send("citation_added", citation);
      }
      for (const artifact of task.artifacts) {
        send("artifact_created", artifact);
      }

      if (task.hitl_required) {
        send("hitl_required", { task_id: task.id, prompt: "Safety Officer / Lead Engineer sign-off required" });
      }

      send("task_completed", { task_id: task.id, duration_ms: 3200 });
      controller.close();
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
    },
  });
}
