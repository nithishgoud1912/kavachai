"use client";

import React from "react";
import Link from "next/link";
import { useNetworkMonitor } from "@/app/hooks/useNetworkMonitor";

interface NetworkStatusPillProps {
  compact?: boolean;
  className?: string;
}

export default function NetworkStatusPill({
  compact = false,
  className = "",
}: NetworkStatusPillProps) {
  const { report } = useNetworkMonitor();

  const externalCalls = report?.external_recorded ?? 0;
  const isSovereign = externalCalls === 0;

  if (compact) {
    return (
      <Link
        href="/network-monitor"
        className={`group inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium transition-all ${
          isSovereign
            ? "bg-[#E9F0EC] text-[#2D794D] border border-[#2D794D]/30 hover:bg-[#E9F0EC]/80 hover:shadow-xs"
            : "bg-[#F2E6E3] text-[#B83838] border border-[#B83838]/40 hover:bg-[#F2E6E3]/80 animate-pulse"
        } ${className}`}
        title="Sovereign Air-Gap Monitor: Click to inspect live socket audit logs and allowlist"
      >
        <span className="relative flex h-2 w-2">
          <span
            className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
              isSovereign ? "bg-[#2D794D]" : "bg-[#B83838]"
            }`}
          />
          <span
            className={`relative inline-flex rounded-full h-2 w-2 ${
              isSovereign ? "bg-[#2D794D]" : "bg-[#B83838]"
            }`}
          />
        </span>
        <span className="font-mono text-[11px] font-semibold">
          {externalCalls === 0 ? "Air-Gapped (0 Egress)" : `${externalCalls} Disallowed Egress!`}
        </span>
      </Link>
    );
  }

  return (
    <Link
      href="/network-monitor"
      className={`group inline-flex items-center justify-between gap-2 px-3 py-1.5 rounded-xl text-xs font-medium border transition-all ${
        isSovereign
          ? "bg-[#E9F0EC]/70 text-[#2D794D] border-[#2D794D]/30 hover:bg-[#E9F0EC] hover:shadow-xs"
          : "bg-[#F2E6E3] text-[#B83838] border-[#B83838]/40 shadow-xs animate-pulse"
      } ${className}`}
      title="Persistent Sovereign Egress Monitor: 0 external outbound socket calls detected"
    >
      <div className="flex items-center gap-2">
        <span className="relative flex h-2 w-2">
          <span
            className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
              isSovereign ? "bg-[#2D794D]" : "bg-[#B83838]"
            }`}
          />
          <span
            className={`relative inline-flex rounded-full h-2 w-2 ${
              isSovereign ? "bg-[#2D794D]" : "bg-[#B83838]"
            }`}
          />
        </span>
        <span className="font-mono text-[11px]">
          {externalCalls === 0 ? "100% Air-Gapped" : `${externalCalls} Egress Blocked`}
        </span>
      </div>
      <span className="text-[10px] opacity-75 group-hover:translate-x-0.5 transition-transform font-mono">
        →
      </span>
    </Link>
  );
}
