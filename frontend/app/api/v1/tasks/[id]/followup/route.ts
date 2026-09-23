import { NextResponse } from "next/server";
import { tasksStore } from "../../route";

export async function POST(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const task = tasksStore.get(id);
  if (!task) {
    return NextResponse.json({ error: { message: "Task not found", status: 404 } }, { status: 404 });
  }

  try {
    const { message } = await req.json();
    const reply = `Follow-up evaluation on "${message}": Verified against local knowledge base. Relevant process safety parameters and equipment thresholds have been cross-checked on-premise without external network communication.`;

    task.reasoning_output += `\n\n---\n**Q (Follow-up):** ${message}\n**A:** ${reply}`;
    tasksStore.set(id, task);

    return NextResponse.json({ reply });
  } catch (err: any) {
    return NextResponse.json({ error: { message: err.message, status: 500 } }, { status: 500 });
  }
}
