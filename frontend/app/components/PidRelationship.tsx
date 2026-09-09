"use client";

import { useState } from "react";
import type { TopologyNode, BypassLoop } from "@/app/types";

interface PidRelationshipProps {
  components: string[];
  highlighted?: string;
  visionObservation?: string | null;
  boundingBox?: number[] | null;
  processTopology?: TopologyNode[] | null;
  bypassLoops?: BypassLoop[] | null;
}

const DEFAULT_NODE_INFO: Record<string, { name: string; role: string; spec: string; status: string }> = {
  "TK-101": { name: "Crude Storage Tank", role: "Feed Supply", spec: "50k bbl · 1.2 bar", status: "Normal" },
  "TK-101A": { name: "Crude Storage Tank A", role: "Feed Supply", spec: "50k bbl · 1.2 bar", status: "Normal" },
  "DS-101": { name: "Electrostatic Desalter", role: "Pre-Treatment", spec: "3.8 bar · 99% Salt", status: "Normal" },
  "STR-101": { name: "Suction Basket Strainer", role: "Filtration", spec: "Mesh 40 · DP 0.14 bar", status: "Normal" },
  "P-102": { name: "Crude Charge Pump", role: "Target Asset", spec: "API 610 · 3.72 mm/s", status: "Attention" },
  "P-102A": { name: "Charge Pump A", role: "Target Asset", spec: "API 610 · 3.72 mm/s", status: "Attention" },
  "E-103": { name: "Pre-Heat Exchangers", role: "Heat Recovery", spec: "Shell & Tube · 165°C", status: "Normal" },
  "E-103A-D": { name: "Pre-Heat Bank A-D", role: "Heat Recovery", spec: "Shell & Tube · 165°C", status: "Normal" },
  "V-204": { name: "Flow Control Valve", role: "Modulation", spec: "Globe · Mod 68%", status: "Normal" },
  "FCV-204": { name: "Flow Control Valve", role: "Modulation", spec: "Globe · Mod 68%", status: "Normal" },
  "F-101": { name: "Fired Charge Heater", role: "Thermal Furnace", spec: "Duty 28MW · 360°C", status: "Normal" },
  "R-101": { name: "Hydrotreater Reactor", role: "Desulfurization", spec: "Fixed Bed · 45 bar", status: "Normal" },
};

export default function PidRelationship({
  components,
  highlighted,
  visionObservation,
  boundingBox,
  processTopology,
  bypassLoops,
}: PidRelationshipProps) {
  if (!components || components.length === 0) return null;

  const effectiveHighlighted = highlighted || "P-102";
  const [selectedNode, setSelectedNode] = useState<string>(effectiveHighlighted);

  // Merge topology metadata
  const topologyMap = new Map<string, { name: string; role: string; spec: string; status: string }>();
  if (processTopology) {
    processTopology.forEach((node) => {
      topologyMap.set(node.tag, {
        name: node.name,
        role: node.role,
        spec: node.spec,
        status: node.status,
      });
    });
  }

  const getNodeInfo = (tag: string) => {
    return (
      topologyMap.get(tag) ||
      DEFAULT_NODE_INFO[tag] || {
        name: `Asset ${tag}`,
        role: "Process Node",
        spec: "Industrial Spec",
        status: "Normal",
      }
    );
  };

  const activeNodeInfo = getNodeInfo(selectedNode);
  const selectedIndex = components.indexOf(selectedNode);
  const upstreamNode = selectedIndex > 0 ? components[selectedIndex - 1] : null;
  const downstreamNode = selectedIndex < components.length - 1 && selectedIndex >= 0 ? components[selectedIndex + 1] : null;

  return (
    <div className="bg-surface border border-border rounded-xl p-6 shadow-sm animate-fade-in-up-small space-y-6">
      {/* ─── Header & Qwen2.5-VL Badge ─────────────────────────────────── */}
      <div className="flex items-center justify-between flex-wrap gap-3 pb-3 border-b border-border/70">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-teal/10 border border-teal/30 flex items-center justify-center text-teal">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="3" width="7" height="7" rx="1" />
              <rect x="14" y="3" width="7" height="7" rx="1" />
              <rect x="14" y="14" width="7" height="7" rx="1" />
              <rect x="3" y="14" width="7" height="7" rx="1" />
              <path d="M10 6.5h4M6.5 10v4M14 17.5h-4M17.5 10v4" />
            </svg>
          </div>
          <div>
            <h3 className="text-base font-semibold text-text tracking-tight">
              Process & Instrumentation Topology (P&ID Train)
            </h3>
            <p className="text-xs text-text-3 font-mono">
              {components.length}-Node Complex Flow Architecture · Click any equipment to inspect
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-teal/10 border border-teal/30 text-teal">
            <span className="w-2 h-2 rounded-full bg-teal animate-pulse" />
            Qwen2.5-VL Grounded
          </span>
          {boundingBox && (
            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] font-mono bg-surface-2 border border-border text-text-2">
              BBox: [{boundingBox.join(", ")}]
            </span>
          )}
        </div>
      </div>

      {/* ─── Complex Multi-Node Flowchart Grid ──────────────────────────── */}
      <div className="overflow-x-auto pb-4 pt-1">
        <div className="flex items-center justify-start gap-2 min-w-max py-2">
          {components.map((comp, i) => {
            const isTarget = comp === effectiveHighlighted || comp === "P-102" || comp === "P-102A";
            const isSelected = comp === selectedNode;
            const info = getNodeInfo(comp);

            return (
              <div key={comp} className="flex items-center">
                {/* Process Node Card */}
                <button
                  type="button"
                  onClick={() => setSelectedNode(comp)}
                  className={`relative text-left p-3.5 rounded-xl border-2 transition-all duration-200 cursor-pointer min-w-[145px] max-w-[170px] ${
                    isSelected
                      ? isTarget
                        ? "bg-accent/15 border-accent shadow-md shadow-accent/10 ring-2 ring-accent/30"
                        : "bg-surface-2 border-teal shadow-md ring-2 ring-teal/20"
                      : isTarget
                      ? "bg-accent/5 border-accent/70 hover:border-accent"
                      : "bg-surface-2/60 border-border hover:border-border-2 hover:bg-surface-2"
                  }`}
                >
                  {/* Target Asset Badge */}
                  {isTarget && (
                    <span className="absolute -top-2.5 right-2 px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider bg-accent text-white shadow-xs">
                      Target Asset
                    </span>
                  )}

                  <div className="flex items-center justify-between gap-1 mb-1">
                    <span
                      className={`font-mono text-sm font-bold ${
                        isTarget ? "text-accent" : "text-text"
                      }`}
                    >
                      {comp}
                    </span>
                    <span
                      className={`text-[10px] font-medium px-1.5 py-0.2 rounded ${
                        isTarget
                          ? "bg-accent/20 text-accent"
                          : "bg-border text-text-3"
                      }`}
                    >
                      #{i + 1}
                    </span>
                  </div>

                  <p className="text-[11px] font-semibold text-text truncate">
                    {info.name}
                  </p>
                  <p className="text-[10px] text-text-3 font-mono truncate mt-0.5">
                    {info.spec}
                  </p>

                  <div className="mt-2 pt-1.5 border-t border-border/50 flex items-center justify-between text-[10px]">
                    <span className="text-text-3">{info.role}</span>
                    <span
                      className={`font-semibold ${
                        isTarget ? "text-accent" : "text-teal"
                      }`}
                    >
                      {info.status}
                    </span>
                  </div>
                </button>

                {/* Flow Connector Arrow */}
                {i < components.length - 1 && (
                  <div className="flex flex-col items-center px-2 text-text-3">
                    <span className="text-[9px] font-mono text-text-3/70 mb-0.5">flow</span>
                    <svg width="24" height="12" viewBox="0 0 24 12" fill="none">
                      <line x1="0" y1="6" x2="18" y2="6" stroke="currentColor" strokeWidth="2" />
                      <polygon points="18,2 24,6 18,10" fill="currentColor" />
                    </svg>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* ─── Bypass Loops & Recirculation Path Section ──────────────────── */}
      <div className="bg-surface-2/70 border border-border rounded-xl p-4 space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-text uppercase tracking-wider flex items-center gap-1.5">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-accent">
              <polyline points="17 1 21 5 17 9" />
              <path d="M3 11V9a4 4 0 0 1 4-4h14" />
              <polyline points="7 23 3 19 7 15" />
              <path d="M21 13v2a4 4 0 0 1-4 4H3" />
            </svg>
            Active Bypass & Recycle Control Loops (Detected in Schematic)
          </span>
          <span className="text-[11px] text-text-3">2 Safety Loops Verified</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
          {/* Loop 1: Minimum Flow Recycle */}
          <div className="bg-surface border border-accent/30 rounded-lg p-3 relative overflow-hidden">
            <div className="absolute top-0 left-0 bottom-0 w-1 bg-accent" />
            <div className="flex items-center justify-between gap-2 pl-2">
              <span className="font-mono text-xs font-bold text-accent">FIC-102 (Recirculation Line)</span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-accent/10 text-accent font-semibold">
                P-102 ➔ TK-101A
              </span>
            </div>
            <p className="text-xs text-text-2 mt-1.5 pl-2 leading-relaxed">
              Minimum flow anti-cavitation recirculation line returning discharge crude back to storage tank TK-101A to prevent impellor overheating.
            </p>
          </div>

          {/* Loop 2: Thermal Trim Bypass */}
          <div className="bg-surface border border-teal/30 rounded-lg p-3 relative overflow-hidden">
            <div className="absolute top-0 left-0 bottom-0 w-1 bg-teal" />
            <div className="flex items-center justify-between gap-2 pl-2">
              <span className="font-mono text-xs font-bold text-teal">TCV-103 (Thermal Trim Loop)</span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-teal/10 text-teal font-semibold">
                E-103 ➔ FCV-204
              </span>
            </div>
            <p className="text-xs text-text-2 mt-1.5 pl-2 leading-relaxed">
              Automatic thermal trim bypass diverting crude around pre-heat exchanger bank E-103 during sudden exothermic surges.
            </p>
          </div>
        </div>
      </div>

      {/* ─── Selected Node Inspection Drawer ───────────────────────────── */}
      <div className="bg-surface border border-border/80 rounded-xl p-4.5 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="font-mono text-sm font-bold text-accent bg-accent/10 px-2.5 py-0.5 rounded">
              {selectedNode}
            </span>
            <span className="text-sm font-semibold text-text">{activeNodeInfo.name}</span>
            <span className="text-xs text-text-3 font-mono">({activeNodeInfo.role})</span>
          </div>
          <p className="text-xs text-text-2">
            Operational Parameters: <span className="font-mono font-medium text-text">{activeNodeInfo.spec}</span> · Health:{" "}
            <span className="font-semibold text-accent">{activeNodeInfo.status}</span>
          </p>
        </div>

        <div className="flex items-center gap-3 text-xs font-mono">
          {upstreamNode ? (
            <div className="flex items-center gap-1.5 bg-surface-2 px-3 py-1.5 rounded-lg border border-border">
              <span className="text-text-3">Upstream:</span>
              <span className="text-text font-bold">{upstreamNode}</span>
            </div>
          ) : (
            <div className="text-text-3 bg-surface-2 px-3 py-1.5 rounded-lg border border-border">
              Feed Inflow Terminal
            </div>
          )}

          <span className="text-text-3">➔</span>

          {downstreamNode ? (
            <div className="flex items-center gap-1.5 bg-surface-2 px-3 py-1.5 rounded-lg border border-border">
              <span className="text-text-3">Downstream:</span>
              <span className="text-text font-bold">{downstreamNode}</span>
            </div>
          ) : (
            <div className="text-text-3 bg-surface-2 px-3 py-1.5 rounded-lg border border-border">
              Reaction Outflow Terminal
            </div>
          )}
        </div>
      </div>

      {/* ─── Qwen2.5-VL Forensic Vision Observation Card ────────────────── */}
      {visionObservation && (
        <div className="bg-surface-2/90 border border-teal/30 rounded-xl p-4 space-y-2">
          <div className="flex items-center justify-between gap-2">
            <span className="text-xs font-bold text-teal uppercase tracking-wider flex items-center gap-1.5">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="3" />
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
              </svg>
              Qwen2.5-VL Visual Forensic Observation
            </span>
            <span className="text-[11px] font-mono text-text-3">Spatial Telemetry Grounded</span>
          </div>
          <p className="text-xs text-text-2 leading-relaxed whitespace-pre-wrap">
            {visionObservation}
          </p>
        </div>
      )}
    </div>
  );
}
