"use client";

import React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useSession } from "@/app/hooks/useSession";
import NetworkStatusPill from "./NetworkStatusPill";
import SovereignBadge from "./SovereignBadge";

interface HeaderProps {
  title?: string;
  subtitle?: string;
  showNewTaskButton?: boolean;
  breadcrumbs?: { label: string; href?: string }[];
  showBackToWorkspace?: boolean;
  showAuditLink?: boolean;
}

export default function Header({
  title,
  subtitle,
  showNewTaskButton = true,
  breadcrumbs,
  showBackToWorkspace,
  showAuditLink,
}: HeaderProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { session, logout } = useSession();

  return (
    <header className="sticky top-0 z-20 bg-bg-base/90 backdrop-blur-md border-b border-border-subtle h-14 flex items-center justify-between px-6">
      {/* ─── Left: Breadcrumbs or Page Title ───────────────────────── */}
      <div className="flex items-center gap-3 min-w-0">
        {breadcrumbs && breadcrumbs.length > 0 ? (
          <nav className="flex items-center gap-1.5 text-xs text-text-3 font-medium">
            {breadcrumbs.map((crumb, idx) => (
              <React.Fragment key={idx}>
                {idx > 0 && <span className="opacity-40">/</span>}
                {crumb.href ? (
                  <Link
                    href={crumb.href}
                    className="hover:text-accent transition-colors truncate max-w-[140px]"
                  >
                    {crumb.label}
                  </Link>
                ) : (
                  <span className="text-text font-semibold truncate max-w-[200px]">
                    {crumb.label}
                  </span>
                )}
              </React.Fragment>
            ))}
          </nav>
        ) : (
          <div className="flex items-baseline gap-2 truncate">
            {title && (
              <h1 className="font-serif font-bold text-base text-text tracking-tight truncate">
                {title}
              </h1>
            )}
            {subtitle && (
              <span className="text-xs text-text-3 font-mono hidden sm:inline truncate">
                · {subtitle}
              </span>
            )}
          </div>
        )}
      </div>

      {/* ─── Right: Sovereignty Badge, Network Pill, Actions ───────── */}
      <div className="flex items-center gap-3 shrink-0">
        <SovereignBadge size="sm" className="hidden md:inline-flex" />

        <NetworkStatusPill compact={true} />

        {showNewTaskButton && pathname !== "/workspace" && pathname !== "/task/new" && (
          <Link
            href="/workspace"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-accent text-white text-xs font-semibold hover:bg-accent-hover transition-colors shadow-xs"
          >
            <span>+</span>
            <span>New Task</span>
          </Link>
        )}

        {/* User Mini Avatar / Info */}
        {session && (
          <div className="flex items-center gap-2 pl-2 border-l border-border text-xs">
            <span className="w-6 h-6 rounded-full bg-accent/15 text-accent font-bold flex items-center justify-center text-[10px]">
              {session.name.slice(0, 2).toUpperCase()}
            </span>
            <span className="text-text-2 font-medium hidden lg:inline">
              {session.name}
            </span>
          </div>
        )}
      </div>
    </header>
  );
}
