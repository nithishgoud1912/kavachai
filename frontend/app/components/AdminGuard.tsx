"use client";

import React from "react";
import Link from "next/link";
import { useSession } from "@/app/hooks/useSession";

interface AdminGuardProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export default function AdminGuard({ children, fallback }: AdminGuardProps) {
  const { session } = useSession();

  // Admin access granted to IT_SECURITY or users with "admin" in name
  const isAdmin =
    session?.department === "IT_SECURITY" ||
    session?.department === "ADMIN" ||
    (session?.name && session.name.toLowerCase().includes("admin"));

  if (isAdmin) {
    return <>{children}</>;
  }

  if (fallback) {
    return <>{fallback}</>;
  }

  return (
    <div className="p-8 max-w-xl mx-auto text-center space-y-4 my-12 bg-surface border border-border rounded-2xl shadow-sm">
      <div className="w-12 h-12 rounded-full bg-accent/10 border border-accent/20 text-accent flex items-center justify-center text-xl mx-auto">
        🔒
      </div>
      <h3 className="font-serif text-xl font-bold text-text">Administrator Clearance Required</h3>
      <p className="text-sm text-text-2">
        You are currently authenticated as <span className="font-semibold text-text">{session?.name || "Guest"}</span> ({session?.department || "General"}). This section contains governance parameters for on-premise model weights, air-gap retention policies, and compute caps.
      </p>
      <div className="pt-2 flex justify-center gap-3">
        <Link
          href="/"
          className="px-4 py-2 text-xs font-medium rounded-lg bg-surface border border-border text-text hover:bg-surface-2 transition-colors"
        >
          Switch to Admin Demo Role
        </Link>
        <Link
          href="/workspace"
          className="px-4 py-2 text-xs font-medium rounded-lg bg-accent text-white hover:bg-accent-hover transition-colors"
        >
          Return to Workspace
        </Link>
      </div>
    </div>
  );
}
