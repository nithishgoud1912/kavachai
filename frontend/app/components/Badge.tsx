"use client";

import React from "react";

export type BadgeVariant =
  | "verified"
  | "partial"
  | "unverified"
  | "running"
  | "queued"
  | "complete"
  | "failed"
  | "sovereign"
  | "info";

interface BadgeProps {
  variant: BadgeVariant | string;
  label?: string;
  children?: React.ReactNode;
  size?: "sm" | "md";
  className?: string;
}

export default function Badge({
  variant,
  label,
  children,
  size = "md",
  className = "",
}: BadgeProps) {
  const content = label || children;

  let colorClasses = "bg-surface-2 text-text border-border";
  let dotColor = "bg-text-3";

  switch (variant) {
    case "verified":
    case "complete":
      colorClasses = "bg-[#E9F0EC] text-[#2D794D] border-[#2D794D]/25";
      dotColor = "bg-[#2D794D]";
      break;
    case "partial":
    case "awaiting_review":
      colorClasses = "bg-[#F6ECCF] text-[#B8860B] border-[#B8860B]/30";
      dotColor = "bg-[#B8860B]";
      break;
    case "unverified":
    case "failed":
      colorClasses = "bg-[#F2E6E3] text-[#B83838] border-[#B83838]/25";
      dotColor = "bg-[#B83838]";
      break;
    case "running":
      colorClasses = "bg-[#C35C3E]/10 text-[#C35C3E] border-[#C35C3E]/30";
      dotColor = "bg-[#C35C3E] animate-pulse";
      break;
    case "sovereign":
      colorClasses = "bg-[#C35C3E]/10 text-[#C35C3E] border-[#C35C3E]/30 font-semibold";
      dotColor = "bg-[#C35C3E]";
      break;
    case "info":
    case "insufficient_evidence":
      colorClasses = "bg-[#F0ECF3] text-[#744C95] border-[#744C95]/25";
      dotColor = "bg-[#744C95]";
      break;
    case "queued":
      colorClasses = "bg-surface-2 text-text-3 border-border";
      dotColor = "bg-text-3";
      break;
  }

  const sizeClasses =
    size === "sm" ? "px-2 py-0.5 text-[11px] gap-1.5" : "px-2.5 py-1 text-xs gap-1.5";

  return (
    <span
      className={`inline-flex items-center rounded-full border font-medium tracking-tight ${sizeClasses} ${colorClasses} ${className}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${dotColor}`} />
      <span>{content}</span>
    </span>
  );
}
