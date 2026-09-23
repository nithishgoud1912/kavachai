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
  const isSovereign = report?.sovereign ?? true;

  if (compact) {
    return (
      <Link
        href="/network-monitor"
        className={`group inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium transition-all ${
          isSovereign
            ? "bg-[#E9F0EC] text-[#2D794D] border border-[#2D794D]/25 hover:bg-[#E9F0EC]/80"
            : "bg-[#F2E6E3] text-[#B83838] border border-[#B83838]/30 hover:bg-[#F2E6E3]/80 animate-pulse"
        } ${className}`}
        title="Air-Gap Network Monitor: Click to inspect live socket audit logs"
      >
        <span
          className={`w-2 h-2 rounded-full ${
            isSovereign ? "bg-[#2D794D]" : "bg-[#B83838]"
          }`}
        />
        <span>{externalCalls === 0 ? "Air-Gapped" : `${externalCalls} External Alert!`}</span>
      </Link>
    );
  }

  return (
    <Link
      href="/network-monitor"
      className={`group inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium border transition-all ${
        isSovereign
          ? "bg-[#E9F0EC] text-[#2D794D] border-[#2D794D]/30 hover:shadow-sm"
          : "bg-[#F2E6E3] text-[#B83838] border-[#B83838]/40 shadow-sm animate-pulse"
      } ${className}`}
      title="Persistent Egress Monitor: 0 external outbound socket calls detected"
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
      <span className="font-mono">
        {externalCalls === 0 ? "0 external calls" : `${externalCalls} EXTERNAL CALLS!`}
      </span>
      <span className="text-[10px] opacity-75 group-hover:translate-x-0.5 transition-transform">
        →
      </span>
    </Link>
  );
}
