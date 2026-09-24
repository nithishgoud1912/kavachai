"use client";

import { useEffect, useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import { loginWithPassword, verifyLocalMfa, createSession, type LocalAuthResponse } from "@/app/services/api";
import { useSession } from "@/app/hooks/useSession";
import SovereignBadge from "./components/SovereignBadge";
import NetworkStatusPill from "./components/NetworkStatusPill";

const DEPARTMENTS = [
  "OPERATIONS",
  "MAINTENANCE",
  "SAFETY (HSE)",
  "ENGINEERING",
  "REFINERY PROCESS",
  "IT_SECURITY",
  "AUDIT",
];

const DEMO_PRESETS = [
  { label: "Plant Operations", username: "operations_lead", password: "KavachAI_Analyst_2026!", role: "Operations Lead", dept: "OPERATIONS" },
  { label: "Maintenance Eng", username: "maint_eng", password: "KavachAI_Analyst_2026!", role: "Mechanical Lead", dept: "MAINTENANCE" },
  { label: "Safety Officer", username: "safety_reviewer", password: "KavachAI_Reviewer_2026!", role: "HSE Inspector", dept: "SAFETY (HSE)" },
  { label: "Process Engineer", username: "process_eng", password: "KavachAI_KbManager_2026!", role: "CDU Engineer", dept: "REFINERY PROCESS" },
  { label: "System Admin", username: "admin", password: "KavachAI_Admin_2026!", role: "IT Security Admin", dept: "IT_SECURITY" },
  { label: "Statutory Auditor", username: "auditor", password: "KavachAI_Auditor_2026!", role: "Compliance Officer", dept: "AUDIT" },
];

export default function LoginPage() {
  const router = useRouter();
  const { login, isAuthenticated, isLoading } = useSession();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [department, setDepartment] = useState("OPERATIONS");
  const [role, setRole] = useState("Operations Lead");
  const [mfaCode, setMfaCode] = useState("");
  const [pendingAuth, setPendingAuth] = useState<LocalAuthResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoading && isAuthenticated) router.push("/workspace");
  }, [isLoading, isAuthenticated, router]);

  if (isLoading || isAuthenticated) return null;

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      let result: LocalAuthResponse;
      if (pendingAuth) {
        if (!pendingAuth.session_id) throw new Error("Authentication challenge is unavailable.");
        result = await verifyLocalMfa(pendingAuth.session_id, mfaCode);
      } else {
        result = await loginWithPassword(
          username.trim() || "operations_lead",
          password || "KavachAI_Analyst_2026!"
        );
        if (result.mfa_required) {
          setPendingAuth(result);
          setMfaCode("");
          return;
        }
      }

      if (!result.session_id) {
        throw new Error("Authentication succeeded but no session ID was returned.");
      }

      login({
        session_id: result.session_id,
        name: result.username || username.trim() || "Operations Lead",
        department: result.department || department,
        issued_at: new Date().toISOString(),
        expires_at: result.expires_at || undefined,
      });
      router.push("/workspace");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to authenticate.");
    } finally {
      setLoading(false);
    }
  }

  async function handleQuickDemo() {
    setLoading(true);
    setError(null);
    try {
      const demoSession = await createSession(
        username.trim() || "Operations Lead",
        department
      );
      login(demoSession);
      router.push("/workspace");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to initiate demo session.");
    } finally {
      setLoading(false);
    }
  }

  function handleSelectPreset(preset: typeof DEMO_PRESETS[0]) {
    setUsername(preset.username);
    setPassword(preset.password);
    setDepartment(preset.dept);
    setRole(preset.role);
    setError(null);
    setPendingAuth(null);
  }

  return (
    <main className="min-h-screen flex items-center justify-center bg-bg-base px-4 py-8 relative">
      <div className="absolute top-6 right-6">
        <NetworkStatusPill compact={false} />
      </div>

      <section className="w-full max-w-lg bg-surface border border-border-subtle rounded-3xl p-8 sm:p-10 shadow-sm space-y-6">
        {/* Header */}
        <div className="text-center space-y-2">
          <SovereignBadge size="sm" showSubtitle={true} className="mb-2" />
          <h1 className="font-serif text-3xl sm:text-4xl font-bold tracking-tight text-accent">
            KavachAI
          </h1>
          <p className="text-xs text-text-3 font-mono uppercase tracking-wider">
            Mangalore Refinery and Petrochemicals Limited (MRPL)
          </p>
          <p className="text-xs text-text-2 pt-0.5">
            Sovereign On-Premise Agentic AI Workbench
          </p>
        </div>

        {/* Quick Demo Role Selector */}
        {!pendingAuth && (
          <div className="p-3 bg-surface-2/60 border border-border rounded-2xl space-y-2">
            <p className="text-[10px] font-mono font-semibold text-text-3 uppercase tracking-wider">
              Quick-Select Demo Role:
            </p>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5">
              {DEMO_PRESETS.map((p) => {
                const isSelected = username === p.username;
                return (
                  <button
                    key={p.label}
                    type="button"
                    onClick={() => handleSelectPreset(p)}
                    className={`px-2 py-1.5 rounded-lg text-[11px] font-medium transition-all text-left truncate cursor-pointer ${
                      isSelected
                        ? "bg-accent text-white shadow-2xs font-semibold"
                        : "bg-surface border border-border hover:border-accent/40 text-text"
                    }`}
                  >
                    <span className="block truncate font-semibold">{p.label}</span>
                    <span className="block text-[9px] opacity-75 font-mono truncate">{p.dept}</span>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Authentication Form */}
        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          {!pendingAuth ? (
            <>
              <div>
                <label className="block text-text-2 font-medium mb-1 font-mono uppercase text-[11px]">
                  Engineer / User Name
                </label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="e.g. nithish.goud or maint_eng"
                  required
                  className="w-full p-2.5 rounded-xl border border-border bg-bg-base focus:bg-surface focus:outline-none focus:ring-1 focus:ring-accent font-sans"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-text-2 font-medium mb-1 font-mono uppercase text-[11px]">
                    Department Scope
                  </label>
                  <select
                    value={department}
                    onChange={(e) => setDepartment(e.target.value)}
                    className="w-full p-2.5 rounded-xl border border-border bg-bg-base focus:bg-surface focus:outline-none focus:ring-1 focus:ring-accent font-sans"
                  >
                    {DEPARTMENTS.map((d) => (
                      <option key={d} value={d}>
                        {d}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-text-2 font-medium mb-1 font-mono uppercase text-[11px]">
                    Operational Role
                  </label>
                  <input
                    type="text"
                    value={role}
                    onChange={(e) => setRole(e.target.value)}
                    placeholder="e.g. Lead Engineer"
                    className="w-full p-2.5 rounded-xl border border-border bg-bg-base focus:bg-surface focus:outline-none focus:ring-1 focus:ring-accent font-sans"
                  >
                  </input>
                </div>
              </div>

              <div>
                <label className="block text-text-2 font-medium mb-1 font-mono uppercase text-[11px]">
                  Local Station Password
                </label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full p-2.5 rounded-xl border border-border bg-bg-base focus:bg-surface focus:outline-none focus:ring-1 focus:ring-accent font-sans"
                />
              </div>
            </>
          ) : (
            <div>
              <label className="block text-text-2 font-medium mb-1 font-mono uppercase text-[11px]">
                Air-Gapped MFA Code (6 Digits)
              </label>
              <input
                type="text"
                maxLength={6}
                value={mfaCode}
                onChange={(e) => setMfaCode(e.target.value)}
                placeholder="123456"
                className="w-full p-2.5 rounded-xl border border-border bg-bg-base focus:bg-surface focus:outline-none focus:ring-1 focus:ring-accent font-mono text-center tracking-widest text-lg"
              />
            </div>
          )}

          {error && <p className="text-red font-medium text-xs">{error}</p>}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-xl bg-accent text-white font-semibold text-xs hover:bg-accent-hover transition-colors shadow-xs cursor-pointer flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Verifying Air-Gapped Session...</span>
              </>
            ) : (
              <span>Access Sovereign Workbench →</span>
            )}
          </button>

          <div className="relative flex py-1 items-center">
            <div className="flex-grow border-t border-border-subtle"></div>
            <span className="flex-shrink mx-3 text-text-3 font-mono text-[10px] uppercase tracking-wider">
              Or Instant Demo Mode
            </span>
            <div className="flex-grow border-t border-border-subtle"></div>
          </div>

          <button
            type="button"
            onClick={handleQuickDemo}
            disabled={loading}
            className="w-full py-2.5 rounded-xl border border-border text-text-1 hover:bg-surface-elevated font-medium text-xs transition-colors flex items-center justify-center gap-2 cursor-pointer"
          >
            <span>⚡ Launch Quick Guest Session (No Password)</span>
          </button>
        </form>

        <div className="pt-2 border-t border-border-subtle text-center text-[10px] text-text-3 font-mono">
          <span>Protected by Physical Air-Gap · Zero External Dependency</span>
        </div>
      </section>
    </main>
  );
}
