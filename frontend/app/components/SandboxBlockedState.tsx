"use client";

import React from "react";

interface SandboxBlockedStateProps {
  blockedImports?: string[];
  message?: string;
  onRetry?: () => void;
  className?: string;
}

export default function SandboxBlockedState({
  blockedImports = ["socket"],
  message,
  onRetry,
  className = "",
}: SandboxBlockedStateProps) {
  return (
    <div
      className={`p-4 rounded-xl border border-red/30 bg-[#F2E6E3] text-text ${className}`}
    >
      <div className="flex items-start gap-3">
        <div className="w-8 h-8 rounded-lg bg-red/10 border border-red/20 flex items-center justify-center text-red shrink-0 font-bold text-sm">
          🛡️
        </div>
        <div className="space-y-1.5 flex-1">
          <div className="flex items-center gap-2">
            <h4 className="font-semibold text-red text-sm">Air-Gap Security Guardrail Active</h4>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-red/15 text-red font-semibold uppercase">
              Execution Intercepted
            </span>
          </div>
          <p className="text-xs text-text-2">
            {message ||
              "The AST static code analyzer detected forbidden external networking modules. In compliance with MRPL sovereign air-gap policy, arbitrary socket connections and external HTTP egress are strictly prohibited."}
          </p>

          {blockedImports.length > 0 && (
            <div className="flex items-center gap-2 mt-2 pt-2 border-t border-red/15 text-xs">
              <span className="text-text-3 font-medium">Blocked modules:</span>
              <div className="flex flex-wrap gap-1">
                {blockedImports.map((mod) => (
                  <span
                    key={mod}
                    className="font-mono text-[11px] px-2 py-0.5 rounded bg-surface border border-red/25 text-red font-semibold"
                  >
                    import {mod}
                  </span>
                ))}
              </div>
            </div>
          )}

          {onRetry && (
            <div className="pt-2">
              <button
                onClick={onRetry}
                className="text-xs text-accent hover:text-accent-dim underline font-medium"
              >
                Refactor code to remove blocked imports & retry
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
