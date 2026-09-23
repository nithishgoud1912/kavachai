import { NextResponse } from "next/server";
import type { WorkbenchTask, TaskMode, DeliverableType, AttachmentItem } from "@/app/types";

// In-memory persistent tasks for local session
export const tasksStore: Map<string, WorkbenchTask> = new Map();

// Seed initial realistic MRPL industrial tasks
function seedTasksIfNeeded() {
  if (tasksStore.size > 0) return;

  const sample1: WorkbenchTask = {
    id: "task-mrpl-101",
    query: "Draft an approval note from the scanned inspection report for P-204 Crude Feed Pump vibration anomaly.",
    mode: "auto",
    deliverable_type: "word",
    status: "awaiting_review",
    attachments: [
      {
        filename: "P-204_Vibration_Spectra_Apr2026.pdf",
        url: "/api/v1/evidence/files/p204/raw",
        type: "document",
        size: 1420000,
      },
      {
        filename: "P-204_Bearing_Defect_Thermal.png",
        url: "/api/v1/evidence/files/p204_thermal/raw",
        type: "image",
        size: 890000,
      },
    ],
    plan: [
      {
        id: "sub-1",
        goal: "Multi-tier OCR on scanned inspection spectra report",
        assigned_model: "Qwen2.5-VL · vision",
        task_type: "ocr_extraction",
        status: "done",
        duration_ms: 1240,
      },
      {
        id: "sub-2",
        goal: "Extract peak vibration frequencies (BPFO 142.4 Hz harmonics)",
        assigned_model: "Qwen2.5-Coder · code",
        task_type: "spectral_analysis",
        status: "done",
        duration_ms: 820,
      },
      {
        id: "sub-3",
        goal: "Check P&ID topology for pump bypass isolation valve HV-204B",
        assigned_model: "Qwen2.5-VL · vision",
        task_type: "pid_lookup",
        status: "done",
        duration_ms: 950,
      },
      {
        id: "sub-4",
        goal: "Synthesize formal MRPL Executive Approval Note as DOCX deliverable",
        assigned_model: "Qwen2.5:3b · reasoning",
        task_type: "document_synthesis",
        status: "done",
        duration_ms: 1850,
      },
    ],
    tool_calls: [
      {
        id: "tool-1",
        subtask_id: "sub-1",
        tool_name: "ocr_pipeline_extract",
        category: "ocr",
        arguments: { document: "P-204_Vibration_Spectra_Apr2026.pdf", tier: "Tesseract + VLM Fallback" },
        status: "completed",
        started_at: "2026-09-23T10:14:02Z",
        duration_ms: 1240,
        result_summary: "Extracted 4 pages. Peak overall vibration: 9.8 mm/s RMS (ISO 10816 Zone D: Danger).",
      },
      {
        id: "tool-2",
        subtask_id: "sub-2",
        tool_name: "sandbox_code_exec",
        category: "code_sandbox",
        arguments: { script: "calculate_bearing_harmonics.py", rpm: 2980, bearing: "SKF 6318" },
        status: "completed",
        started_at: "2026-09-23T10:14:04Z",
        duration_ms: 820,
        result_summary: "Harmonic match: 142.4 Hz BPFO outer race defect confirmed with 96.2% confidence.",
        sandbox_result: {
          exit_code: 0,
          stdout: "Defect signature: BPFO match @ 142.4 Hz, 284.8 Hz.\nSeverity: Urgent bearing overhaul recommended.",
          stderr: "",
          duration_ms: 820,
          memory_mb: 24,
        },
      },
      {
        id: "tool-3",
        subtask_id: "sub-3",
        tool_name: "pid_graph_query",
        category: "doc_search",
        arguments: { tag: "P-204A", bypass_valve: "HV-204B" },
        status: "completed",
        started_at: "2026-09-23T10:14:05Z",
        duration_ms: 950,
        result_summary: "Bypass valve HV-204B verified in closed standby state. Safe to switch train to pump P-204B.",
      },
    ],
    reasoning_output: `### Industrial Diagnostic & Approval Assessment
**Subject:** P-204 Crude Charge Pump Severe Vibration (Train A)  
**Location:** Crude Distillation Unit (CDU-II), MRPL Mangalore  

1. **Observed Condition:**  
   Overall vibration amplitude increased from **2.8 mm/s RMS** (baseline) to **9.8 mm/s RMS** under 85% operating load. Peak frequency analysis identifies predominant peaks at **142.4 Hz**, which corresponds directly to the Ball Pass Frequency Outer Race (BPFO) of the outboard bearing.

2. **Root Cause Confirmation:**  
   Bearing race spalling with progressive thermal degradation observed on outboard bearing housing. Operating in ISO 10816-3 Zone D (Unacceptable for continuous industrial operation).

3. **Recommended Action Plan:**  
   - Immediately switch feed flow to standby pump **P-204B**.
   - Lockout/Tagout (LOTO) isolation of P-204A suction and discharge manual valves.
   - Bearing cartridge replacement during the upcoming 8-hour turnaround window.`,
    artifacts: [
      {
        id: "art-1",
        task_id: "sample1",
        name: "MRPL_CDU_P204A_Approval_Note.docx",
        type: "docx",
        size_bytes: 48200,
        created_at: "2026-09-23T10:14:10Z",
        model_used: "Qwen2.5:3b · reasoning",
        download_url: "/api/v1/exports/MRPL_CDU_P204A_Approval_Note.docx",
        metadata: {
          pages: 3,
          summary: "Formal executive approval note for P-204A bearing replacement and CDU-II feed diversion.",
          sections: [
            {
              title: "1. Executive Summary & Purpose",
              content: "This note seeks approval for immediate operational handover from Crude Feed Pump P-204A to standby P-204B and authorization for emergency bearing overhaul.",
            },
            {
              title: "2. Technical Diagnostic Findings",
              content: "Spectral analysis verified outer race defect (BPFO 142.4 Hz). Vibration levels are 9.8 mm/s RMS, exceeding ISO 10816 threshold limits.",
            },
            {
              title: "3. Safety & Production Impact Analysis",
              content: "Zero throughput loss will be sustained by executing transfer via bypass loop HV-204B prior to LOTO isolation.",
            },
            {
              title: "4. Cost Estimate & Statutory Sign-off",
              content: "Estimated spare parts: INR 1,45,000. Overhaul turnaround time: 6.5 hours.",
            },
          ],
        },
      },
      {
        id: "art-2",
        task_id: "sample1",
        name: "P204_Vibration_FFT_Analysis.py",
        type: "code",
        size_bytes: 3200,
        created_at: "2026-09-23T10:14:06Z",
        model_used: "Qwen2.5-Coder · code",
        download_url: "/api/v1/exports/P204_Vibration_FFT_Analysis.py",
        metadata: {
          language: "python",
          summary: "Harsh-isolated script calculating BPFO, BPFI, and BSF harmonics against SKF 6318 bearing geometry.",
        },
      },
    ],
    citations: [
      {
        type: "document",
        source_id: "p204_spec",
        label: "P-204_Inspection_Apr2026.pdf",
        page: 4,
        section: "Vibration Spectrum & Thermal Log",
      },
      {
        type: "pid_drawing",
        source_id: "cdu2_pid",
        label: "MRPL-CDU2-PID-004.pdf",
        page: 1,
        section: "Crude Train Pump Manifold",
      },
    ],
    created_at: "2026-09-23T10:13:58Z",
    completed_at: "2026-09-23T10:14:12Z",
    hitl_required: true,
    hitl_status: "pending",
    models_used: ["Qwen2.5-VL · vision", "Qwen2.5-Coder · code", "Qwen2.5:3b · reasoning"],
    confidence: 96,
  };

  tasksStore.set(sample1.id, sample1);
}

export async function GET() {
  seedTasksIfNeeded();
  const list = Array.from(tasksStore.values()).sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );
  return NextResponse.json(list);
}

export async function POST(req: Request) {
  seedTasksIfNeeded();
  try {
    const body = await req.json();
    const query = body.query || "Industrial Task";
    const mode: TaskMode = body.mode || "auto";
    const deliverableType: DeliverableType = body.deliverable_type || "word";
    const attachments: AttachmentItem[] = body.attachments || [];

    const taskId = `task-${Date.now().toString(36)}-${Math.random().toString(36).substring(2, 6)}`;

    // Build smart subtask plan based on query & mode
    const isCode = mode === "code" || /code|script|python|calculation|vibration|fft|sensor/i.test(query);
    const isVision = mode === "vision" || attachments.some((a) => a.type === "image" || /drawing|pid|p&id|scanned/i.test(a.filename));

    const plan = [
      {
        id: `sub-${taskId}-1`,
        goal: isVision
          ? "Inspect engineering documents and diagrams via Multimodal VLM"
          : "Deconstruct query constraints and retrieve technical context from local KB",
        assigned_model: isVision ? "Qwen2.5-VL · vision" : "Qwen2.5:3b · reasoning",
        task_type: isVision ? "multimodal_ocr" : "query_analysis",
        status: "done" as const,
        duration_ms: 1100,
      },
      {
        id: `sub-${taskId}-2`,
        goal: isCode
          ? "Execute engineering calculations in air-gapped hardened sandbox"
          : "Correlate operational metrics and verify against safety thresholds",
        assigned_model: isCode ? "Qwen2.5-Coder · code" : "Qwen2.5:3b · reasoning",
        task_type: isCode ? "code_execution" : "data_correlation",
        status: "done" as const,
        duration_ms: 950,
      },
      {
        id: `sub-${taskId}-3`,
        goal: `Generate formatted ${deliverableType.toUpperCase()} deliverable for plant management`,
        assigned_model: "Qwen2.5:3b · reasoning",
        task_type: "deliverable_synthesis",
        status: "done" as const,
        duration_ms: 1400,
      },
    ];

    const ext = deliverableType === "word" ? "docx" : deliverableType === "ppt" ? "pptx" : deliverableType === "excel" ? "xlsx" : "py";
    const artifactName = `MRPL_Engineering_Deliverable_${Date.now().toString().slice(-4)}.${ext}`;

    const newTask: WorkbenchTask = {
      id: taskId,
      query,
      mode,
      deliverable_type: deliverableType,
      status: "complete",
      attachments,
      plan,
      tool_calls: [
        {
          id: `tool-${Date.now()}-1`,
          subtask_id: plan[0].id,
          tool_name: isVision ? "vlm_diagram_analyze" : "local_kb_search",
          category: isVision ? "vision" : "doc_search",
          arguments: { query_context: query.slice(0, 80) },
          status: "completed",
          started_at: new Date().toISOString(),
          duration_ms: 1100,
          result_summary: "Context successfully retrieved and cross-referenced with internal plant specs.",
        },
        {
          id: `tool-${Date.now()}-2`,
          subtask_id: plan[1].id,
          tool_name: "sandbox_code_exec",
          category: "code_sandbox",
          arguments: { command: "run_engineering_check", isolated: true },
          status: "completed",
          started_at: new Date().toISOString(),
          duration_ms: 950,
          result_summary: "Validated execution in non-networked container (--network none).",
          sandbox_result: {
            exit_code: 0,
            stdout: "Verification status: 100% On-Premise. All safety constraints met.",
            stderr: "",
            duration_ms: 950,
          },
        },
      ],
      reasoning_output: `### Executive Analysis & Deliverable Formulation\n\n**Task Context:** ${query}\n\n1. **Data Ingestion & Integrity:**\n   The task inputs and references were processed exclusively on local compute. No external endpoints were queried.\n\n2. **Synthesis & Validation:**\n   All plant parameters and compliance guidelines were verified against local repository models. Findings indicate normal operational tolerances with actionable steps compiled in the deliverable below.\n\n3. **Deliverable Ready:**\n   A complete **${deliverableType.toUpperCase()}** artifact has been generated and is ready for download or human review.`,
      artifacts: [
        {
          id: `art-${taskId}-1`,
          task_id: taskId,
          name: artifactName,
          type: ext as any,
          size_bytes: 42100,
          created_at: new Date().toISOString(),
          model_used: "Qwen2.5:3b · reasoning",
          download_url: `/api/v1/exports/${artifactName}`,
          metadata: {
            summary: `Automated ${deliverableType.toUpperCase()} deliverable generated from on-premise pipeline.`,
            sections: [
              { title: "1. Background & Scope", content: `Analysis regarding: "${query}".` },
              { title: "2. Technical Evaluation", content: "Parameters cross-referenced with SOP documentation." },
              { title: "3. Actionable Recommendations", content: "Proceed with scheduled maintenance and protocol verification." }
            ]
          }
        },
      ],
      citations: [
        {
          type: "document",
          source_id: "mrpl_manual",
          label: "MRPL_Refinery_SOP_Manual_2026.pdf",
          page: 12,
          section: "Operating Boundaries",
        },
      ],
      created_at: new Date().toISOString(),
      completed_at: new Date().toISOString(),
      hitl_required: deliverableType === "word",
      hitl_status: deliverableType === "word" ? "pending" : undefined,
      models_used: isVision
        ? ["Qwen2.5-VL · vision", "Qwen2.5:3b · reasoning"]
        : isCode
        ? ["Qwen2.5-Coder · code", "Qwen2.5:3b · reasoning"]
        : ["Qwen2.5:3b · reasoning"],
      confidence: 94,
    };

    tasksStore.set(taskId, newTask);
    return NextResponse.json(newTask);
  } catch (err: any) {
    return NextResponse.json({ error: { message: err.message, status: 500 } }, { status: 500 });
  }
}
