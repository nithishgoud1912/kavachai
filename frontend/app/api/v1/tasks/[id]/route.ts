import { NextResponse } from "next/server";
import { tasksStore } from "../route";

export async function GET(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const task = tasksStore.get(id);
  if (!task) {
    return NextResponse.json({ error: { message: "Task not found", status: 404 } }, { status: 404 });
  }
  return NextResponse.json(task);
}

export async function PATCH(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const task = tasksStore.get(id);
  if (!task) {
    return NextResponse.json({ error: { message: "Task not found", status: 404 } }, { status: 404 });
  }

  try {
    const body = await req.json();
    const { action, comments } = body;

    if (action === "approve") {
      task.hitl_status = "approved";
      task.status = "complete";
    } else if (action === "revise") {
      task.hitl_status = "revised";
      task.status = "running";
      task.reasoning_output += `\n\n**Revision Request from Safety Officer:** "${comments || "Please refine section 2"}"\n\n*Agent is re-synthesizing technical parameters...*`;
    } else if (action === "reject") {
      task.hitl_status = "rejected";
    }
    task.hitl_comments = comments;
    tasksStore.set(id, task);

    return NextResponse.json(task);
  } catch (err: any) {
    return NextResponse.json({ error: { message: err.message, status: 500 } }, { status: 500 });
  }
}
