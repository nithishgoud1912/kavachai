"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useSession } from "@/app/hooks/useSession";
import { useRouter } from "next/navigation";

interface HeaderProps {
  showAuditLink?: boolean;
  showBackToWorkspace?: boolean;
}

export default function Header({
  showAuditLink = true,
  showBackToWorkspace = false,
}: HeaderProps) {
  const { session, logout } = useSession();
  const router = useRouter();
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 8);
    };

    handleScroll();
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const handleLogout = () => {
    logout();
    router.push("/");
  };

  return (
    <header
      className={`sticky top-0 z-40 transition-all duration-300 border-b ${
        isScrolled
          ? "bg-bg/85 backdrop-blur-[16px] border-border shadow-[0_1px_3px_rgba(45,42,38,0.05)]"
          : "bg-transparent backdrop-blur-none border-transparent"
      }`}
    >
      <div className="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">
        {/* Left — Logo */}
        <div className="flex items-center gap-6">
          <Link href="/workspace" className="flex items-center gap-2 group">
            <span className="font-[family-name:var(--font-playfair)] font-serif text-accent text-xl font-bold tracking-tight transition-transform duration-200 group-hover:scale-[1.02]">
              KavachAI
            </span>
          </Link>
          {showBackToWorkspace && (
            <Link
              href="/workspace"
              className="text-text-3 hover:text-text-2 text-sm transition-colors duration-200 flex items-center gap-1"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <path d="M19 12H5M12 19l-7-7 7-7" />
              </svg>
              Workspace
            </Link>
          )}
        </div>

        {/* Right — User info + nav */}
        <div className="flex items-center gap-4">
          {session && (
            <span className="text-text-2 text-sm">
              <span className="text-text">{session.name}</span>
              <span className="text-text-3 mx-1.5">·</span>
              <span className="font-[family-name:var(--font-mono)] text-text-3 text-xs">
                {session.department}
              </span>
            </span>
          )}

          {showAuditLink && (
            <Link
              href="/audit"
              className="text-sm text-text-3 hover:text-teal border border-border hover:border-teal/30
                         rounded-lg px-3 py-1.5 transition-all duration-200"
            >
              Audit Log
            </Link>
          )}

          {session && (
            <button
              onClick={handleLogout}
              className="text-sm text-text-3 hover:text-red transition-colors duration-200"
              title="End session"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                <polyline points="16 17 21 12 16 7" />
                <line x1="21" y1="12" x2="9" y2="12" />
              </svg>
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
