"use client";

interface SuggestedQuestionsProps {
  onSelect: (question: string) => void;
}

const SUGGESTIONS = [
  {
    label: "Fire emergency procedure",
    query: "What should an employee do during a fire emergency?",
  },
  {
    label: "PPE required — Zone A",
    query: "What personal protective equipment is required in Zone A?",
  },
  {
    label: "P-102 health trend",
    query:
      "Investigate Pump P-102 and determine whether its condition has deteriorated.",
  },
];

export default function SuggestedQuestions({ onSelect }: SuggestedQuestionsProps) {
  return (
    <div className="space-y-3">
      <p className="text-text-3 text-sm">Suggested investigations</p>
      <div className="flex flex-wrap gap-3">
        {SUGGESTIONS.map((s, i) => (
          <button
            key={i}
            onClick={() => onSelect(s.query)}
            className="bg-surface-2 border border-border text-text-2 text-sm px-4 py-2.5 rounded-lg
                       transition-all duration-200
                       hover:border-border-hi hover:text-accent hover:bg-surface-3 hover:-translate-y-0.5 hover:shadow-sm
                       focus-visible:ring-2 focus-visible:ring-accent/30
                       animate-fade-in-up-small"
            style={{ animationDelay: `${(i + 1) * 100}ms` }}
          >
            {s.label}
          </button>
        ))}
      </div>
    </div>
  );
}
