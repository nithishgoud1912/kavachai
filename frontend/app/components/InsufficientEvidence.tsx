"use client";

interface InsufficientEvidenceProps {
  message?: string;
  onBackToWorkspace?: () => void;
}

export default function InsufficientEvidence({
  message,
  onBackToWorkspace,
}: InsufficientEvidenceProps) {
  return (
    <div className="animate-fade-in-up">
      <div className="bg-surface border-2 border-orange/30 rounded-xl p-8 max-w-xl mx-auto">
        {/* Icon */}
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-full bg-orange/10 flex items-center justify-center flex-shrink-0">
            <svg
              width="22"
              height="22"
              viewBox="0 0 24 24"
              fill="none"
              className="text-orange"
            >
              <path
                d="M12 9v4m0 4h.01M12 2L2 20h20L12 2z"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </div>
          <h2 className="font-[family-name:var(--font-fraunces)] text-xl text-orange font-semibold tracking-wide">
            INSUFFICIENT EVIDENCE
          </h2>
        </div>

        {/* Message */}
        <div className="space-y-4 text-text-2 text-sm leading-relaxed">
          <p>
            {message ||
              "I couldn't find reliable information about this in the KavachAI knowledge base for this plant."}
          </p>
          <p className="text-text-3">
            This system is designed to avoid answering beyond its verified
            organizational knowledge.
          </p>
        </div>

        {/* Action */}
        {onBackToWorkspace && (
          <div className="mt-8">
            <button
              onClick={onBackToWorkspace}
              className="text-sm text-teal hover:text-accent transition-colors duration-200
                         flex items-center gap-2"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <path d="M19 12H5M12 19l-7-7 7-7" />
              </svg>
              Start a new investigation
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
