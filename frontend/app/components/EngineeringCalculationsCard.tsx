"use client";

import React from "react";

interface CalculationStep {
  column: string;
  operation: string;
  value: string;
  unit?: string;
  steps?: string[];
}

interface CalculationGroup {
  table?: string;
  filename?: string;
  results?: CalculationStep[];
}

interface EngineeringCalculationsCardProps {
  calculationResults?: CalculationGroup[];
  className?: string;
}

export default function EngineeringCalculationsCard({
  calculationResults = [],
  className = "",
}: EngineeringCalculationsCardProps) {
  if (!calculationResults || calculationResults.length === 0) return null;

  return (
    <div className={`p-5 bg-surface border border-border rounded-2xl shadow-xs space-y-4 ${className}`}>
      <div className="flex items-center justify-between pb-2 border-b border-border-subtle">
        <div className="flex items-center gap-2">
          <span className="text-base">📐</span>
          <div>
            <h3 className="font-serif font-bold text-sm text-text">
              Engineering Calculations with Steps
            </h3>
            <p className="text-xs text-text-3 font-mono">
              Deterministic bounded calculations & telemetry derivations
            </p>
          </div>
        </div>
        <span className="px-2.5 py-1 rounded-full bg-accent/10 text-accent border border-accent/20 text-xs font-mono font-medium">
          Verified Steps
        </span>
      </div>

      <div className="space-y-4">
        {calculationResults.map((group, gIdx) => (
          <div key={gIdx} className="space-y-3">
            {(group.filename || group.table) && (
              <div className="text-[11px] font-mono text-text-3 flex items-center gap-1.5">
                <span>📁</span>
                <span className="font-semibold text-text">{group.filename || "Table"}</span>
                {group.table && <span>({group.table})</span>}
              </div>
            )}

            <div className="grid grid-cols-1 gap-3">
              {group.results?.map((res, rIdx) => (
                <div
                  key={rIdx}
                  className="p-3.5 rounded-xl border border-border bg-bg-base/50 space-y-2.5"
                >
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-text">
                      Metric: <span className="font-mono text-accent">{res.column}</span>
                    </span>
                    <span className="font-mono px-2 py-0.5 rounded bg-surface border border-border text-[11px] uppercase font-bold text-text-2">
                      {res.operation}
                    </span>
                  </div>

                  {res.steps && res.steps.length > 0 ? (
                    <div className="space-y-1.5 pt-1 border-t border-border-subtle/60">
                      <p className="text-[10px] font-mono uppercase text-text-3 font-semibold">
                        Calculation Steps:
                      </p>
                      <ul className="space-y-1 font-mono text-xs text-text-2">
                        {res.steps.map((st, sIdx) => (
                          <li key={sIdx} className="flex items-start gap-2 bg-surface-2/60 p-2 rounded-lg">
                            <span className="w-4 h-4 rounded-full bg-accent/20 text-accent text-[10px] flex items-center justify-center shrink-0 mt-0.5 font-bold">
                              {sIdx + 1}
                            </span>
                            <span>{st}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  ) : null}

                  <div className="flex items-center justify-between pt-1 border-t border-border-subtle text-xs font-mono">
                    <span className="text-text-3">Final Computed Value:</span>
                    <span className="text-accent font-bold text-sm">
                      {res.value} {res.unit || ""}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
