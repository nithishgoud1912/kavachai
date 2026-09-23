import { NextResponse } from "next/server";
import type { ModelRegistryEntry, RoutingRule, RoutingDecisionLog } from "@/app/types";

let modelsRegistry: ModelRegistryEntry[] = [
  {
    id: "qwen2.5:3b",
    name: "qwen2.5:3b",
    display_name: "Qwen 2.5 (3B Instruct)",
    provider: "ollama",
    size: "1.9 GB",
    quantization: "Q4_K_M",
    context_length: 32768,
    capabilities: ["reasoning", "extraction"],
    status: "loaded",
    vram_usage_gb: 2.1,
    max_vram_gb: 8.0,
    latency_p95_ms: 120,
    endpoint: "http://localhost:11434",
  },
  {
    id: "qwen2.5-coder:3b",
    name: "qwen2.5-coder:3b",
    display_name: "Qwen 2.5 Coder (3B)",
    provider: "ollama",
    size: "1.9 GB",
    quantization: "Q4_K_M",
    context_length: 32768,
    capabilities: ["code", "reasoning"],
    status: "loaded",
    vram_usage_gb: 2.2,
    max_vram_gb: 8.0,
    latency_p95_ms: 95,
    endpoint: "http://localhost:11434",
  },
  {
    id: "qwen2.5vl:3b",
    name: "qwen2.5vl:3b",
    display_name: "Qwen 2.5 VL (3B Multimodal)",
    provider: "ollama",
    size: "2.3 GB",
    quantization: "Q4_K_M",
    context_length: 16384,
    capabilities: ["vision", "extraction", "reasoning"],
    status: "loaded",
    vram_usage_gb: 2.8,
    max_vram_gb: 8.0,
    latency_p95_ms: 240,
    endpoint: "http://localhost:11434",
  },
  {
    id: "codellama:7b",
    name: "codellama:7b",
    display_name: "CodeLlama (7B Instruct)",
    provider: "ollama",
    size: "3.8 GB",
    quantization: "Q4_0",
    context_length: 16384,
    capabilities: ["code"],
    status: "warm",
    vram_usage_gb: 0.0,
    max_vram_gb: 8.0,
    latency_p95_ms: 310,
    endpoint: "http://localhost:11434",
  },
  {
    id: "nomic-embed-text",
    name: "nomic-embed-text",
    display_name: "Nomic Embed Text v1.5",
    provider: "local",
    size: "274 MB",
    quantization: "F16",
    context_length: 8192,
    capabilities: ["embedding"],
    status: "loaded",
    vram_usage_gb: 0.4,
    max_vram_gb: 8.0,
    latency_p95_ms: 18,
    endpoint: "http://localhost:8000/embed",
  },
];

let routingRules: RoutingRule[] = [
  {
    id: "rule-1",
    task_type: "Code Generation & Calculations",
    preferred_model_id: "qwen2.5-coder:3b",
    fallback_model_id: "codellama:7b",
    condition_description: "Routes script synthesis, harmonic calculations, and math verification.",
    enabled: true,
  },
  {
    id: "rule-2",
    task_type: "P&ID Drawings & Visual Inspection",
    preferred_model_id: "qwen2.5vl:3b",
    fallback_model_id: "qwen2.5:3b",
    condition_description: "Routes scanned diagrams, P&ID topology, and thermal defect inspection.",
    enabled: true,
  },
  {
    id: "rule-3",
    task_type: "Document Summaries & Approval Notes",
    preferred_model_id: "qwen2.5:3b",
    fallback_model_id: "qwen2.5-coder:3b",
    condition_description: "Routes executive notes, SOP queries, and compliance summaries.",
    enabled: true,
  },
  {
    id: "rule-4",
    task_type: "Vector Embedding & Retrieval",
    preferred_model_id: "nomic-embed-text",
    condition_description: "Routes KB chunk embedding and similarity search.",
    enabled: true,
  },
];

let routingLogs: RoutingDecisionLog[] = [
  {
    id: "log-1",
    timestamp: new Date(Date.now() - 1000 * 60 * 3).toISOString(),
    task_id: "task-mrpl-101",
    query_snippet: "P-204 Vibration Spectra: Extract BPFO peak harmonics",
    detected_intent: "code_generation / vibration_math",
    selected_model: "Qwen 2.5 Coder (3B)",
    reason: "rule-1 match: script calculations & harmonic verification",
    confidence: 0.98,
  },
  {
    id: "log-2",
    timestamp: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
    task_id: "task-mrpl-101",
    query_snippet: "P&ID topology for pump bypass valve HV-204B",
    detected_intent: "vision / diagram_ocr",
    selected_model: "Qwen 2.5 VL (3B Multimodal)",
    reason: "rule-2 match: engineering schematic topology lookup",
    confidence: 0.95,
  },
  {
    id: "log-3",
    timestamp: new Date(Date.now() - 1000 * 60 * 12).toISOString(),
    task_id: "task-mrpl-101",
    query_snippet: "Draft MRPL Executive Approval Note for CDU-II",
    detected_intent: "document_synthesis",
    selected_model: "Qwen 2.5 (3B Instruct)",
    reason: "rule-3 match: formal deliverable note formulation",
    confidence: 0.96,
  },
];

export async function GET(req: Request) {
  const url = new URL(req.url);
  const type = url.searchParams.get("type");

  if (type === "rules") {
    return NextResponse.json(routingRules);
  }
  if (type === "logs") {
    return NextResponse.json(routingLogs);
  }

  // Attempt to check if Ollama is running live at localhost:11434
  try {
    const res = await fetch("http://localhost:11434/api/tags", { signal: AbortSignal.timeout(1000) });
    if (res.ok) {
      const data = await res.json();
      const liveNames = new Set((data.models || []).map((m: any) => m.name));
      modelsRegistry = modelsRegistry.map((m) => ({
        ...m,
        status: liveNames.has(m.name) ? "loaded" : m.status,
      }));
    }
  } catch {
    // Offline / fallback silently
  }

  return NextResponse.json(modelsRegistry);
}

export async function POST(req: Request) {
  try {
    const body = await req.json();
    if (body.rule) {
      const rule = body.rule as RoutingRule;
      const index = routingRules.findIndex((r) => r.id === rule.id);
      if (index >= 0) {
        routingRules[index] = rule;
      } else {
        routingRules.push(rule);
      }
      return NextResponse.json(rule);
    }
    if (body.model) {
      const model = body.model as ModelRegistryEntry;
      modelsRegistry.push(model);
      return NextResponse.json(model);
    }
    return NextResponse.json({ ok: true });
  } catch (err: any) {
    return NextResponse.json({ error: { message: err.message, status: 500 } }, { status: 500 });
  }
}
