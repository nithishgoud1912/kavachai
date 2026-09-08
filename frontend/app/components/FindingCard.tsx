"use client";

import type { Finding } from "@/app/types";

interface FindingCardProps {
  finding: Finding;
  index: number;
  onCitationClick: (sourceId: string) => void;
}

const VERIFICATION_COLORS: Record<string, string> = {
  supported: "border-l-green",
  partially_supported: "border-l-orange",
  unsupported: "border-l-red",
};

const VERIFICATION_ICONS: Record<string, { icon: string; label: string; color: string }> = {
  supported: { icon: "✓", label: "Supported", color: "text-green" },
  partially_supported: { icon: "⚠", label: "Partially Supported", color: "text-orange" },
  unsupported: { icon: "✕", label: "Unsupported", color: "text-red" },
};

export default function FindingCard({
  finding,
  index,
  onCitationClick,
}: FindingCardProps) {
  const verification = VERIFICATION_ICONS[finding.verification_status] || VERIFICATION_ICONS.supported;
  const borderColor = VERIFICATION_COLORS[finding.verification_status] || "border-l-green";

  return (
    <div
      className={`bg-surface border border-border rounded-lg border-l-[3px] ${borderColor}
                  animate-fade-in-up-small`}
      style={{ animationDelay: `${(index + 1) * 100}ms` }}
    >
      <div className="p-5 space-y-3">
        {/* Finding Number + Title */}
        <div className="flex items-start gap-3">
          <span className="font-[family-name:var(--font-mono)] text-text-3 text-sm flex-shrink-0">
            {index + 1}.
          </span>
          <h4 className="text-text font-medium text-sm">{finding.title}</h4>
        </div>

        {/* Detail — render technical values in mono */}
        <p className="text-text-2 text-sm font-[family-name:var(--font-mono)] pl-7 leading-relaxed">
          {finding.detail}
        </p>

        {/* Verification + Citations */}
        <div className="flex items-center gap-2 pl-7 flex-wrap">
          <span className={`text-sm font-medium ${verification.color} flex items-center gap-1`}>
            <span>{verification.icon}</span>
            {verification.label}
          </span>

          {finding.evidence.length > 0 && (
            <>
              <span className="text-text-3 text-xs">·</span>
              <div className="flex flex-wrap gap-1.5">
                {finding.evidence.map((ev, i) => (
                  <button
                    key={`${ev.source_id}-${i}`}
                    onClick={() => onCitationClick(ev.source_id)}
                    className="text-teal text-xs hover:text-accent transition-colors duration-200
                               underline decoration-teal/30 hover:decoration-accent/50
                               cursor-pointer"
                  >
                    {ev.label}
                    {ev.page ? `, p. ${ev.page}` : ""}
                    {ev.section ? `, §${ev.section}` : ""}
                  </button>
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
