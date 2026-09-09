import MarkdownMessage from "@/app/components/MarkdownMessage";

interface ConclusionSectionProps {
  conclusion: string;
}

export default function ConclusionSection({ conclusion }: ConclusionSectionProps) {
  return (
    <div className="bg-surface border border-border rounded-xl p-6 animate-fade-in-up-small">
      <h3 className="font-[family-name:var(--font-fraunces)] text-sm font-semibold text-text-2 tracking-widest uppercase mb-4">
        AI Conclusion
      </h3>
      <MarkdownMessage content={conclusion} />
    </div>
  );
}
