"use client";

import { useState } from "react";
import { runSandbox } from "@/app/services/api";
import type { SandboxExecutionResult } from "@/app/types";

export function useSandbox() {
  const [running, setRunning] = useState(false);
  const [lastResult, setLastResult] = useState<SandboxExecutionResult | null>(null);
  const [history, setHistory] = useState<SandboxExecutionResult[]>([]);
  const [error, setError] = useState<string | null>(null);

  const execute = async (code: string, language: string = "python") => {
    setRunning(true);
    setError(null);
    try {
      const result = await runSandbox(code, language);
      setLastResult(result);
      setHistory((prev) => [result, ...prev]);
      return result;
    } catch (err: any) {
      setError(err.message || "Failed to execute code in sandbox");
      throw err;
    } finally {
      setRunning(false);
    }
  };

  return { execute, running, lastResult, history, error };
}
