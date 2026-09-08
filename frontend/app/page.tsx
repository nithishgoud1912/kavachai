"use client";

import { useState, useEffect, FormEvent } from "react";
import { useRouter } from "next/navigation";
import { createSession } from "@/app/services/api";
import { useSession } from "@/app/hooks/useSession";

const DEPARTMENTS = [
  "Operations",
  "HSE",
  "Maintenance",
  "Engineering",
  "Safety",
  "Management",
];

export default function SessionEntry() {
  const router = useRouter();
  const { login, isAuthenticated, isLoading } = useSession();
  const [name, setName] = useState("");
  const [department, setDepartment] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // If already authenticated, redirect safely in an effect
  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.push("/workspace");
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading || isAuthenticated) {
    return null;
  }

  const isValid = name.trim().length > 0 && department.length > 0;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!isValid) return;

    setLoading(true);
    setError(null);

    try {
      const session = await createSession(name.trim(), department);
      login(session);
      router.push("/workspace");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to create session"
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-bg px-4 section-padding">
      <div className="w-full max-w-md">
        <div className="bg-surface border border-border rounded-2xl p-8 sm:p-10 card-shadow card-hover">
          {/* Wordmark Hero Element 1 */}
          <div className="text-center mb-9 hero-fade-in-up hero-stagger-1">
            <h1 className="font-[family-name:var(--font-playfair)] font-serif text-4xl sm:text-5xl font-bold tracking-tight text-accent mb-2.5">
              KavachAI
            </h1>
            <p className="font-[family-name:var(--font-sans)] text-text-2 text-sm">
              Sovereign Industrial AI Workbench
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Name Input Hero Element 2 */}
            <div className="hero-fade-in-up hero-stagger-2">
              <label
                htmlFor="session-name"
                className="block text-sm font-medium text-text-2 mb-2"
              >
                Name
              </label>
              <input
                id="session-name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Enter your name"
                autoComplete="name"
                className="w-full bg-surface-2 border border-border rounded-lg px-4 py-3 text-text
                           placeholder:text-text-3 font-[family-name:var(--font-sans)]
                           transition-all duration-200
                           hover:border-border-hi
                           focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/20"
              />
            </div>

            {/* Department Select Hero Element 3 */}
            <div className="hero-fade-in-up hero-stagger-3">
              <label
                htmlFor="session-department"
                className="block text-sm font-medium text-text-2 mb-2"
              >
                Department
              </label>
              <select
                id="session-department"
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
                className="w-full bg-surface-2 border border-border rounded-lg px-4 py-3 text-text
                           font-[family-name:var(--font-sans)] appearance-none cursor-pointer
                           transition-all duration-200
                           hover:border-border-hi
                           focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/20"
                style={{
                  backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='%2391887b' viewBox='0 0 16 16'%3E%3Cpath d='M4.646 5.646a.5.5 0 0 1 .708 0L8 8.293l2.646-2.647a.5.5 0 0 1 .708.708l-3 3a.5.5 0 0 1-.708 0l-3-3a.5.5 0 0 1 0-.708z'/%3E%3C/svg%3E")`,
                  backgroundRepeat: "no-repeat",
                  backgroundPosition: "right 14px center",
                  paddingRight: "42px",
                }}
              >
                <option value="" disabled className="text-text-3">
                  Select department
                </option>
                {DEPARTMENTS.map((dept) => (
                  <option key={dept} value={dept} className="bg-surface text-text">
                    {dept}
                  </option>
                ))}
              </select>
            </div>

            {error && (
              <div className="text-red text-sm bg-red/10 border border-red/20 rounded-lg px-4 py-3">
                {error}
              </div>
            )}

            {/* Submit Button Hero Element 4 */}
            <div className="hero-fade-in-up hero-stagger-4">
              <button
                type="submit"
                disabled={!isValid || loading}
                className="w-full bg-accent text-[#faf8f5] font-semibold py-3 px-6 rounded-lg
                           transition-all duration-200
                           hover:brightness-105 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-accent/20
                           disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:translate-y-0
                           disabled:hover:shadow-none disabled:hover:brightness-100
                           active:translate-y-0"
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" opacity="0.3" />
                      <path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
                    </svg>
                    Connecting…
                  </span>
                ) : (
                  "Enter Workbench"
                )}
              </button>
            </div>
          </form>

          {/* Sovereignty Statement Hero Element 5 */}
          <div className="mt-8 flex items-start gap-2 text-text-3 hero-fade-in-up hero-stagger-5">
            <span className="text-green text-sm mt-0.5">●</span>
            <p className="font-[family-name:var(--font-mono)] text-xs leading-relaxed">
              Local inference only — no data leaves this network
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
