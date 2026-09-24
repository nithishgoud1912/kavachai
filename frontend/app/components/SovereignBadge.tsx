"use client";

import React from "react";

interface SovereignBadgeProps {
  size?: "sm" | "md" | "lg";
  className?: string;
  showSubtitle?: boolean;
}

export default function SovereignBadge({
  size = "md",
  className = "",
  showSubtitle = false,
}: SovereignBadgeProps) {
  const isSm = size === "sm";
  const isLg = size === "lg";

  return (
    <div
      className={`inline-flex items-center gap-2 rounded-full border border-accent/30 bg-accent/10 text-accent font-medium ${
        isSm
          ? "px-2.5 py-0.5 text-[11px]"
          : isLg
          ? "px-4 py-1.5 text-sm"
          : "px-3 py-1 text-xs"
      } ${className}`}
      title="Configured for local inference; deployment air-gap requires independent verification"
    >
      <span className="relative flex h-2 w-2">
        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent opacity-75" />
        <span className="relative inline-flex rounded-full h-2 w-2 bg-accent" />
      </span>
      <div className="flex items-center gap-1.5">
        <span className="font-semibold tracking-wide">Local Workbench</span>
        {showSubtitle && (
          <>
            <span className="text-accent/40">|</span>
            <span className="font-normal opacity-90">Deployment verification required</span>
          </>
        )}
      </div>
    </div>
  );
}
