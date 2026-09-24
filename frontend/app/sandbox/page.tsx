"use client";

import React, { useState, useEffect } from "react";
import AppShell from "@/app/components/AppShell";
import SandboxBlockedState from "@/app/components/SandboxBlockedState";
import SovereignBadge from "@/app/components/SovereignBadge";
import { useSandbox } from "@/app/hooks/useSandbox";

const DEFAULT_SCRIPT = `# Standard-library demonstration; no engineering claims.
values = [1, 2, 3]
assert sum(values) == 6
print("Assertions passed:", sum(values))
`;

export default function SandboxPage() {
  const [code, setCode] = useState(DEFAULT_SCRIPT);
  const [language, setLanguage] = useState("python");
  const { execute, running, lastResult, history } = useSandbox();

  useEffect(() => {
    // Check if user came from CodeViewer with preset code
    const preset = sessionStorage.getItem("sandbox_preset_code");
    if (preset) {
      const timer = setTimeout(() => setCode(preset), 0);
      sessionStorage.removeItem("sandbox_preset_code");
      return () => clearTimeout(timer);
    }
  }, []);

  const handleRun = () => {
    execute(code, language);
  };

  const handleTestBlockedImport = () => {
    setCode(`import socket\nimport requests\n\ns = socket.socket()\ns.connect(('8.8.8.8', 53))\nprint("Egress attempt")`);
  };

  return (
    <AppShell
      title="Air-Gapped Code Sandbox"
      subtitle="Hardened Non-Networked Execution (--network none)"
      breadcrumbs={[
        { label: "Workspace", href: "/workspace" },
        { label: "Code Sandbox" },
      ]}
    >
      <div className="space-y-6 max-w-6xl mx-auto pb-12">
        {/* Security Guardrails Header Notice */}
        <div className="p-4 bg-surface border border-border rounded-2xl shadow-xs flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <span className="text-2xl">🛡️</span>
            <div>
              <h3 className="font-serif font-bold text-sm text-text">
                Container Security Policy Active
              </h3>
              <p className="text-xs text-text-3 font-mono">
                Flags: --network none · Read-only rootfs · 512MB RAM cap · 5s timeout · AST import filter
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <SovereignBadge size="sm" />
            <button
              onClick={handleTestBlockedImport}
              className="text-[11px] font-mono px-3 py-1.5 rounded-lg border border-red/30 bg-red/5 text-red hover:bg-red/10 transition-colors cursor-pointer"
            >
              Test AST Block (import socket)
            </button>
          </div>
        </div>

        {/* Editor + Output Columns */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
          {/* Editor Column */}
          <div className="bg-surface border border-border rounded-2xl p-5 shadow-xs space-y-3">
            <div className="flex items-center justify-between border-b border-border-subtle pb-2">
              <div className="flex items-center gap-2 font-mono text-xs text-text-3">
                <span>Language:</span>
                <select
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  className="bg-surface-2 border border-border px-2 py-0.5 rounded text-text font-semibold"
                >
                  <option value="python">Python 3.11</option>
                  <option value="javascript">Node.js (Safe)</option>
                </select>
              </div>

              <button
                onClick={handleRun}
                disabled={running}
                className="px-5 py-2 rounded-xl bg-accent text-white hover:bg-accent-hover font-semibold text-xs transition-colors shadow-xs cursor-pointer flex items-center gap-1.5"
              >
                {running ? (
                  <>
                    <span className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    <span>Executing in Sandbox...</span>
                  </>
                ) : (
                  <>
                    <span>▶ Run Script</span>
                  </>
                )}
              </button>
            </div>

            <textarea
              rows={18}
              value={code}
              onChange={(e) => setCode(e.target.value)}
              className="w-full font-mono text-xs p-4 rounded-xl border border-border bg-[#1E1E1E] text-[#D4D4D4] focus:outline-none focus:ring-1 focus:ring-accent leading-relaxed resize-none"
            />
          </div>

          {/* Output / Result Column */}
          <div className="space-y-4">
            {lastResult && lastResult.status === "security_blocked" && (
              <SandboxBlockedState
                blockedImports={lastResult.blocked_imports}
                message={lastResult.stderr}
                onRetry={() => setCode(DEFAULT_SCRIPT)}
              />
            )}

            <div className="bg-surface border border-border rounded-2xl p-5 shadow-xs space-y-3">
              <div className="flex items-center justify-between border-b border-border-subtle pb-2">
                <span className="font-serif font-bold text-sm text-text">Standard Output & Telemetry</span>
                {lastResult && (
                  <span className="text-[11px] font-mono text-text-3">
                    Exit: {lastResult.exit_code} · {lastResult.execution_time_ms}ms · {lastResult.memory_peak_mb}MB
                  </span>
                )}
              </div>

              <div className="min-h-56 p-4 rounded-xl bg-bg-base border border-border font-mono text-xs overflow-x-auto whitespace-pre-wrap leading-relaxed text-text">
                {lastResult
                  ? lastResult.stdout || lastResult.stderr || "Execution completed with 0 output."
                  : "Click 'Run Script' to execute in the hardened container."}
              </div>
            </div>

            {/* Session Execution History */}
            {history.length > 0 && (
              <div className="bg-surface border border-border rounded-2xl p-4 shadow-xs space-y-2">
                <span className="text-[11px] font-mono uppercase text-text-3 font-semibold">
                  Session Execution History ({history.length})
                </span>
                <div className="space-y-1.5 max-h-40 overflow-y-auto">
                  {history.map((h) => (
                    <div
                      key={h.id}
                      className="p-2 rounded-lg bg-surface-2/50 border border-border flex items-center justify-between text-xs font-mono"
                    >
                      <span className="truncate max-w-[200px] text-text-2">
                        {h.code.split("\n")[0] || "Script"}
                      </span>
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] text-text-3">{h.execution_time_ms}ms</span>
                        <span
                          className={`text-[10px] px-1.5 py-0.2 rounded font-semibold ${
                            h.status === "success"
                              ? "bg-green/10 text-green"
                              : "bg-red/10 text-red"
                          }`}
                        >
                          {h.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
