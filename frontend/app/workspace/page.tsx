"use client";

import { useState, FormEvent, useEffect } from "react";
import { useRouter } from "next/navigation";
import Header from "@/app/components/Header";
import SuggestedQuestions from "@/app/components/SuggestedQuestions";
import { useSession } from "@/app/hooks/useSession";
import { useKnowledgeBase } from "@/app/hooks/useKnowledgeBase";
import { createInvestigation } from "@/app/services/api";

export default function Workspace() {
  const router = useRouter();
  const { session, isAuthenticated, isLoading: sessionLoading } = useSession();
  const { summary, loading: kbLoading } = useKnowledgeBase();
  const [query, setQuery] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!sessionLoading && !isAuthenticated) {
      router.push("/");
    }
  }, [sessionLoading, isAuthenticated, router]);

  if (sessionLoading) {
    return (
      <div className="min-h-screen bg-bg flex flex-col">
        <Header />
        <main className="flex-1 flex flex-col items-center justify-center px-6 pb-20">
          <div className="w-full max-w-2xl space-y-10 animate-pulse">
            <div className="h-10 bg-surface-2 rounded w-2/3 mx-auto" />
            <div className="h-40 bg-surface rounded-xl border border-border" />
          </div>
        </main>
      </div>
    );
  }

  if (!isAuthenticated || !session) return null;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!query.trim() || !session) return;

    setSubmitting(true);
    setError(null);

    try {
      const investigation = await createInvestigation(query.trim(), session.session_id);
      router.push(`/investigation/${investigation.investigation_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start investigation");
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen bg-bg flex flex-col">
      <Header />

      <main className="flex-1 flex flex-col items-center justify-center px-6 pb-20">
        <div className="w-full max-w-2xl space-y-10 animate-fade-in-up">
          {/* Title */}
          <h2 className="font-[family-name:var(--font-fraunces)] text-3xl md:text-4xl text-text text-center font-light">
            What do you want to investigate?
          </h2>

          {/* Query Input */}
          <form onSubmit={handleSubmit} className="relative">
            <div className="bg-surface border border-border rounded-xl overflow-hidden
                            transition-colors duration-200
                            focus-within:border-border-hi">
              <textarea
                id="investigation-query"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Investigate Pump P-102 and determine whether its condition has deteriorated."
                rows={3}
                className="w-full bg-transparent px-5 pt-5 pb-14 text-text resize-none
                           placeholder:text-text-3 font-[family-name:var(--font-mono)] text-sm
                           focus:outline-none"
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    if (query.trim()) handleSubmit(e);
                  }
                }}
              />
              <div className="absolute bottom-3 right-3">
                <button
                  type="submit"
                  disabled={!query.trim() || submitting}
                  className="bg-accent text-bg font-semibold text-sm px-5 py-2 rounded-lg
                             flex items-center gap-2
                             transition-all duration-200
                             hover:brightness-110 hover:-translate-y-0.5
                             disabled:opacity-40 disabled:cursor-not-allowed
                             disabled:hover:translate-y-0 disabled:hover:brightness-100"
                >
                  {submitting ? (
                    <>
                      <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                        <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" opacity="0.3" />
                        <path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
                      </svg>
                      Starting…
                    </>
                  ) : (
                    <>
                      {/* Compass/target icon — NOT paper-plane */}
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <circle cx="12" cy="12" r="10" />
                        <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76" fill="currentColor" stroke="none" />
                      </svg>
                      Investigate
                    </>
                  )}
                </button>
              </div>
            </div>
          </form>

          {error && (
            <div className="text-red text-sm bg-red/10 border border-red/20 rounded-lg px-4 py-3">
              {error}
            </div>
          )}

          {/* Suggested Questions */}
          <SuggestedQuestions onSelect={(q) => setQuery(q)} />
        </div>
      </main>

      {/* Knowledge Base Footer */}
      <footer className="pb-6 text-center">
        {kbLoading ? (
          <p className="text-text-3 text-xs font-[family-name:var(--font-mono)]">
            Loading knowledge base…
          </p>
        ) : summary ? (
          <p className="text-text-3 text-xs font-[family-name:var(--font-mono)]">
            Knowledge base:{" "}
            <span className="text-text-2">{summary.documents}</span> documents ·{" "}
            <span className="text-text-2">{summary.datasets}</span> dataset
            {summary.datasets !== 1 ? "s" : ""} ·{" "}
            <span className="text-text-2">{summary.pid_drawings}</span> P&ID
            {summary.pid_drawings !== 1 ? "s" : ""} loaded
          </p>
        ) : (
          <p className="text-text-3 text-xs font-[family-name:var(--font-mono)]">
            Knowledge base unavailable
          </p>
        )}
      </footer>
    </div>
  );
}
