"use client";

interface PidRelationshipProps {
  components: string[];
  highlighted?: string;
}

export default function PidRelationship({
  components,
  highlighted,
}: PidRelationshipProps) {
  if (!components || components.length === 0) return null;

  return (
    <div className="bg-surface border border-border rounded-xl p-6 animate-fade-in-up-small">
      <h3 className="text-sm font-medium text-text-2 mb-5">P&ID Relationship</h3>

      <div className="flex items-center justify-center gap-0 flex-wrap py-4 overflow-x-auto">
        {components.map((comp, i) => {
          const isHighlighted = comp === highlighted || (
            !highlighted && i === 1 // Default: highlight second component (queried equipment)
          );

          return (
            <div key={comp} className="flex items-center">
              {/* Component Node */}
              <div
                className={`px-4 py-2.5 rounded-lg border-2 font-[family-name:var(--font-mono)] text-sm
                            transition-colors duration-200
                            ${
                              isHighlighted
                                ? "bg-accent/10 border-accent text-accent font-semibold"
                                : "bg-surface-2 border-border text-text-2"
                            }`}
              >
                {comp}
              </div>

              {/* Arrow */}
              {i < components.length - 1 && (
                <div className="flex items-center px-1 text-text-3">
                  <svg width="28" height="12" viewBox="0 0 28 12" fill="none">
                    <line x1="0" y1="6" x2="22" y2="6" stroke="currentColor" strokeWidth="1.5" />
                    <path d="M18 2l6 4-6 4" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
