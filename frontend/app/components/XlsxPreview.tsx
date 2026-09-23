"use client";

import React, { useState } from "react";
import type { ArtifactItem } from "@/app/types";
import { downloadArtifact } from "@/app/services/fileDownload";
import SovereignBadge from "./SovereignBadge";
import ModelChip from "./ModelChip";

interface XlsxPreviewProps {
  artifact: ArtifactItem;
  className?: string;
}

export default function XlsxPreview({ artifact, className = "" }: XlsxPreviewProps) {
  const defaultSheets = [
    {
      name: "Vibration_Telemetry",
      headers: ["Timestamp", "Sensor_Tag", "RPM", "1X_Harmonic (Hz)", "Peak_RMS (mm/s)", "ISO_Zone", "Status"],
      data: [
        ["2026-09-23 08:00", "P204A_DE_VIB", 2980, 49.67, 3.2, "B (Acceptable)", "NORMAL"],
        ["2026-09-23 09:00", "P204A_DE_VIB", 2980, 49.67, 4.8, "C (Alert)", "EVALUATE"],
        ["2026-09-23 10:00", "P204A_DE_VIB", 2980, 49.67, 9.8, "D (Danger)", "CRITICAL"],
        ["2026-09-23 10:15", "P204A_NDE_VIB", 2980, 49.67, 7.4, "D (Danger)", "CRITICAL"],
        ["2026-09-23 10:30", "P204B_STANDBY", 0, 0.0, 0.1, "A (Good)", "READY"],
      ],
    },
    {
      name: "Cost_Estimation",
      headers: ["Item Code", "Description", "Qty", "Unit Cost (INR)", "Total (INR)", "Formula Indicator"],
      data: [
        ["BRG-6318", "SKF Deep Groove Ball Bearing 6318", 2, 45000, 90000, "=C2*D2"],
        ["SEAL-MECH", "Mechanical Seal Cartridge Replacement", 1, 35000, 35000, "=C3*D3"],
        ["LUBE-ISO68", "Synthetic Turbine Lube ISO VG 68 (Liters)", 40, 500, 20000, "=C4*D4"],
        ["LABOR-TECH", "Specialist Millwright Overhaul Hours", 12, 1200, 14400, "=C5*D5"],
        ["TOTAL_EST", "Total Estimated Turnaround Cost", 1, 159400, 159400, "=SUM(E2:E5)"],
      ],
    },
  ];

  const sheets = artifact.metadata?.sheets || defaultSheets;
  const [activeSheetIndex, setActiveSheetIndex] = useState(0);

  const curr = sheets[activeSheetIndex] || sheets[0];

  const handleDownload = () => {
    // Generate CSV-like text
    const csvContent = `${curr.headers.join(",")}\n${curr.data
      .map((row) => row.join(","))
      .join("\n")}`;
    downloadArtifact(artifact.name, csvContent, "text/csv");
  };

  return (
    <div className={`space-y-4 max-w-5xl mx-auto ${className}`}>
      {/* Top Bar Actions */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-4 bg-surface border border-border rounded-2xl shadow-xs">
        <div className="flex items-center gap-3">
          <span className="text-3xl">📗</span>
          <div>
            <h2 className="font-serif font-bold text-base text-text">{artifact.name}</h2>
            <div className="flex items-center gap-2 pt-0.5 text-xs text-text-3 font-mono">
              <ModelChip model={artifact.model_used} size="sm" />
              <span>·</span>
              <span>{sheets.length} Sheets</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <SovereignBadge size="sm" />
          <button
            onClick={handleDownload}
            className="px-4 py-2 rounded-xl bg-accent text-white hover:bg-accent-hover text-xs font-semibold shadow-xs transition-colors cursor-pointer"
          >
            Download .XLSX
          </button>
        </div>
      </div>

      {/* Sheet Tabs */}
      <div className="flex items-center gap-1.5 border-b border-border pb-1">
        {sheets.map((sh, idx) => (
          <button
            key={idx}
            onClick={() => setActiveSheetIndex(idx)}
            className={`px-3 py-1.5 rounded-t-xl text-xs font-mono font-medium transition-all ${
              activeSheetIndex === idx
                ? "bg-surface border-t border-x border-border text-accent font-semibold shadow-2xs"
                : "text-text-3 hover:text-text hover:bg-surface-2"
            }`}
          >
            📊 {sh.name}
          </button>
        ))}
      </div>

      {/* Spreadsheet Grid Preview */}
      <div className="bg-surface border border-border rounded-2xl overflow-hidden shadow-xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono border-collapse">
            <thead>
              <tr className="bg-surface-2 border-b border-border text-text-2">
                <th className="p-2.5 w-12 text-center text-text-3 border-r border-border">#</th>
                {curr.headers.map((h, i) => (
                  <th key={i} className="p-2.5 font-semibold text-text border-r border-border last:border-r-0">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {curr.data.map((row, rowIdx) => (
                <tr
                  key={rowIdx}
                  className="border-b border-border/70 hover:bg-bg-base/80 transition-colors"
                >
                  <td className="p-2.5 text-center text-text-3 bg-surface-2/40 border-r border-border">
                    {rowIdx + 1}
                  </td>
                  {row.map((cell, cellIdx) => {
                    const isFormula = typeof cell === "string" && cell.startsWith("=");
                    const isCritical = cell === "CRITICAL" || cell === "D (Danger)";

                    return (
                      <td
                        key={cellIdx}
                        className={`p-2.5 border-r border-border/70 last:border-r-0 ${
                          isCritical
                            ? "bg-red/10 text-red font-semibold"
                            : isFormula
                            ? "text-accent font-semibold"
                            : "text-text"
                        }`}
                      >
                        {cell}
                        {isFormula && (
                          <span className="ml-1 text-[9px] px-1 rounded bg-accent/15 text-accent">fx</span>
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="p-3 bg-bg-base border-t border-border flex items-center justify-between text-xs text-text-3">
          <span>Showing read-only preview of {curr.data.length} rows</span>
          <button
            onClick={handleDownload}
            className="text-accent hover:underline font-medium"
          >
            Download spreadsheet to edit formulas in Excel →
          </button>
        </div>
      </div>
    </div>
  );
}
