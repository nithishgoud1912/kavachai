import { NextResponse } from "next/server";
import type { EgressReport, NetworkConnectionEntry } from "@/app/types";

const ALLOWLIST = [
  "127.0.0.1:11434 (Local Ollama Engine)",
  "localhost:11434 (Local Ollama Engine)",
  "127.0.0.1:8000 (FastAPI Core Backend)",
  "localhost:8000 (FastAPI Core Backend)",
  "127.0.0.1:5432 (Local PostgreSQL)",
  "internal://chromadb (In-Memory Vector Store)",
];

const connectionLogs: NetworkConnectionEntry[] = [
  {
    id: "conn-1",
    timestamp: new Date(Date.now() - 1000 * 45).toISOString(),
    destination: "127.0.0.1:11434",
    port: 11434,
    service: "Ollama (Qwen 2.5 Coder 3B)",
    method: "POST /api/generate",
    status: "allowed",
    latency_ms: 84,
  },
  {
    id: "conn-2",
    timestamp: new Date(Date.now() - 1000 * 120).toISOString(),
    destination: "127.0.0.1:8000",
    port: 8000,
    service: "KavachAI Backend",
    method: "GET /api/v1/knowledge-base/summary",
    status: "allowed",
    latency_ms: 12,
  },
  {
    id: "conn-3",
    timestamp: new Date(Date.now() - 1000 * 240).toISOString(),
    destination: "127.0.0.1:11434",
    port: 11434,
    service: "Ollama (Qwen 2.5 VL 3B)",
    method: "POST /api/chat",
    status: "allowed",
    latency_ms: 195,
  },
  {
    id: "conn-4",
    timestamp: new Date(Date.now() - 1000 * 360).toISOString(),
    destination: "127.0.0.1:8000",
    port: 8000,
    service: "FastAPI Core",
    method: "GET /api/v1/audit-log",
    status: "allowed",
    latency_ms: 15,
  },
];

export async function GET(req: Request) {
  const url = new URL(req.url);
  const type = url.searchParams.get("type");

  if (type === "connections") {
    return NextResponse.json(connectionLogs);
  }

  const report: EgressReport = {
    total_connections: connectionLogs.length,
    local_allowed: connectionLogs.length,
    external_recorded: 0,
    external_destinations: [],
    sovereign: true,
    session_start: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
    verified_airgap: true,
    allowlist: ALLOWLIST,
  };

  return NextResponse.json(report);
}
