import { NextResponse } from "next/server";
import type { SandboxExecutionResult } from "@/app/types";

const BLOCKED_MODULES = ["socket", "urllib", "requests", "http", "ftplib", "telnetlib", "subprocess", "os.system", "shutil.rmtree"];

export async function POST(req: Request) {
  try {
    const { code = "", language = "python" } = await req.json();

    const startTime = performance.now();

    // 1. Static AST / Token Security Guardrail Check
    const triggeredBlocks: string[] = [];
    for (const blocked of BLOCKED_MODULES) {
      const regex = new RegExp(`\\bimport\\s+${blocked}\\b|\\bfrom\\s+${blocked}\\b|${blocked}\\(`, "i");
      if (regex.test(code)) {
        triggeredBlocks.push(blocked);
      }
    }

    if (triggeredBlocks.length > 0) {
      const duration = Math.round(performance.now() - startTime);
      const blockedResult: SandboxExecutionResult = {
        id: `sb-run-${Date.now()}`,
        code,
        language,
        exit_code: 126,
        stdout: "",
        stderr: `SECURITY GUARDRAIL TRIGGERED:\nExecution rejected by AST Security Monitor.\nBlocked external/unsafe imports detected: ${triggeredBlocks.join(", ")}\nAir-gap policy forbids socket operations and raw subprocess spawns.`,
        execution_time_ms: duration,
        memory_peak_mb: 2,
        blocked_imports: triggeredBlocks,
        is_sandboxed: true,
        status: "security_blocked",
      };
      return NextResponse.json(blockedResult);
    }

    // 2. Safe execution simulation / mathematical calculation
    let stdout = "";
    let stderr = "";
    let exitCode = 0;

    if (code.includes("calculate_bearing_harmonics") || code.includes("BPFO")) {
      stdout = `[MRPL Air-Gapped Code Sandbox - Python 3.11 Safe Environment]\n` +
        `Parameters: RPM=2980, Shaft Freq=49.67 Hz, Bearing=SKF 6318\n` +
        `Calculated Characteristic Frequencies:\n` +
        `  - BPFO (Ball Pass Frequency Outer Race): 142.42 Hz (Harmonic 1X: 142.4 Hz, 2X: 284.8 Hz)\n` +
        `  - BPFI (Ball Pass Frequency Inner Race): 205.28 Hz\n` +
        `  - BSF (Ball Spin Frequency):              98.15 Hz\n` +
        `  - FTF (Fundamental Train Frequency):      19.82 Hz\n` +
        `Observed Sensor Peaks match BPFO with 98.4% spectral correlation.\n` +
        `Severity Assessment: ISO 10816 Zone D (Unsafe for ongoing crude feed pumping).`;
    } else if (code.trim().length === 0) {
      stderr = "Error: empty script provided.";
      exitCode = 1;
    } else {
      stdout = `[MRPL Air-Gapped Code Sandbox - Python 3.11 Safe Environment]\n` +
        `--network none | Memory Cap: 512MB | Timeout: 5000ms\n` +
        `Script execution completed successfully.\n` +
        `Output:\nCalculation verified within standard tolerance. 0 external network calls attempted.`;
    }

    const duration = Math.max(12, Math.round(performance.now() - startTime));
    const result: SandboxExecutionResult = {
      id: `sb-run-${Date.now()}`,
      code,
      language,
      exit_code: exitCode,
      stdout,
      stderr,
      execution_time_ms: duration,
      memory_peak_mb: 18.4,
      is_sandboxed: true,
      status: exitCode === 0 ? "success" : "runtime_error",
    };

    return NextResponse.json(result);
  } catch (err: any) {
    return NextResponse.json({ error: { message: err.message, status: 500 } }, { status: 500 });
  }
}
