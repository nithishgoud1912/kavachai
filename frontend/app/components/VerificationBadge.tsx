"use client";

import type { VerificationStatus } from "@/app/types";

interface VerificationBadgeProps {
  status: VerificationStatus;
  size?: "sm" | "md";
}

const BADGE_CONFIG: Record<
  VerificationStatus,
  { icon: string; label: string; color: string; bg: string }
> = {
  verified: {
    icon: "✓",
    label: "Verified",
    color: "text-green",
    bg: "bg-green/10",
  },
  partially_verified: {
    icon: "⚠",
    label: "Partially Verified",
    color: "text-orange",
    bg: "bg-orange/10",
  },
  unverified: {
    icon: "✕",
    label: "Unverified — do not act without review",
    color: "text-red",
    bg: "bg-red/10",
  },
};

export default function VerificationBadge({
  status,
  size = "md",
}: VerificationBadgeProps) {
  const config = BADGE_CONFIG[status] || BADGE_CONFIG.verified;
  const sizeClasses = size === "sm" ? "text-xs px-2.5 py-1" : "text-sm px-3.5 py-1.5";

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full font-medium
                  ${config.bg} ${config.color} ${sizeClasses}`}
    >
      <span>{config.icon}</span>
      {config.label}
    </span>
  );
}
