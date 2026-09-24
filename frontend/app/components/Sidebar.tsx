"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useSession } from "@/app/hooks/useSession";
import { getConversations, getTasks, deleteConversation } from "@/app/services/api";
import type { Conversation, WorkbenchTask } from "@/app/types";
import NetworkStatusPill from "./NetworkStatusPill";

interface SidebarProps {
  activeConversationId?: string | null;
  onNewChat?: () => void;
  onNewTask?: () => void;
  onSelectConversation?: (id: string) => void;
  className?: string;
}

const NAV_ITEMS = [
  { href: "/workspace", label: "Workspace", icon: "⊞" },
  { href: "/tasks", label: "Tasks & History", icon: "📋" },
  { href: "/chat", label: "Grounded Chat", icon: "💬" },
  { href: "/knowledge-base", label: "Knowledge Base", icon: "📚" },
  { href: "/models", label: "Model Router", icon: "🔀" },
  { href: "/sandbox", label: "Code Sandbox", icon: "💻" },
  { href: "/network-monitor", label: "Egress Monitor", icon: "🛡️" },
  { href: "/audit", label: "Audit Trail", icon: "📜" },
  { href: "/settings", label: "Settings", icon: "⚙️" },
];

export default function Sidebar({
  className = "",
}: SidebarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { session, logout } = useSession();

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [tasks, setTasks] = useState<WorkbenchTask[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const [convs, tList] = await Promise.all([
        getConversations().catch(() => []),
        getTasks().catch(() => []),
      ]);
      setConversations(convs.slice(0, 5));
      setTasks(tList.slice(0, 5));
    } catch {
      // Graceful fallback
    } finally {
      setLoadingHistory(false);
    }
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => void loadData(), 0);
    return () => clearTimeout(timer);
  }, [loadData]);

  return (
    <aside
      className={`w-64 bg-bg-sidebar border-r border-border-subtle flex flex-col h-screen sticky top-0 select-none z-30 ${className}`}
    >
      {/* ─── Workbench Brand & Network Status ─────────────────────── */}
      <div className="p-4 border-b border-border-subtle space-y-3">
        <div className="flex items-center justify-between">
          <Link href="/workspace" className="group flex items-center gap-2">
            <div>
              <span className="font-serif text-accent text-xl font-bold tracking-tight group-hover:opacity-90">
                KavachAI
              </span>
              <span className="block text-[10px] text-text-3 uppercase tracking-wider font-mono">
                MRPL Sovereign Workbench
              </span>
            </div>
          </Link>
        </div>

        {/* Persistent Sovereignty Pill */}
        <div className="pt-1">
          <NetworkStatusPill compact={false} className="w-full justify-between" />
        </div>
      </div>

      {/* ─── Primary Navigation ──────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto p-3 space-y-6">
        <div className="space-y-1">
          <p className="px-3 text-[10px] uppercase font-mono font-semibold text-text-3 tracking-wider mb-1.5">
            Core Modules
          </p>
          {NAV_ITEMS.map((item) => {
            const isActive =
              item.href === "/workspace"
                ? pathname === "/workspace" || pathname === "/"
                : pathname.startsWith(item.href);

            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium transition-all ${
                  isActive
                    ? "bg-accent/10 text-accent font-semibold border border-accent/20 shadow-xs"
                    : "text-text-2 hover:text-text hover:bg-surface-2 border border-transparent"
                }`}
              >
                <span className="text-sm shrink-0">{item.icon}</span>
                <span className="truncate">{item.label}</span>
                {isActive && (
                  <span className="ml-auto w-1.5 h-1.5 rounded-full bg-accent" />
                )}
              </Link>
            );
          })}
        </div>

        {/* ─── Knowledge Base Mini Status Widget ─────────────────── */}
        <div className="p-3 bg-surface-2/60 border border-border rounded-xl space-y-1.5 text-xs">
          <div className="flex items-center justify-between text-text-3 text-[10px] font-mono uppercase">
            <span>Local KB Status</span>
            <span className="w-1.5 h-1.5 rounded-full bg-green" />
          </div>
          <p className="font-semibold text-text text-xs">1,240 Chunks Indexed</p>
          <p className="text-[11px] text-text-3">14 SOPs · 4 P&IDs · Native OCR</p>
        </div>

        {/* ─── Recent Tasks Snippet ──────────────────────────────── */}
        {tasks.length > 0 && (
          <div className="space-y-1.5">
            <div className="flex items-center justify-between px-3 text-[10px] font-mono uppercase text-text-3">
              <span>Recent Tasks</span>
              <Link href="/tasks" className="text-accent hover:underline">
                All
              </Link>
            </div>
            <div className="space-y-1">
              {tasks.slice(0, 3).map((t) => (
                <Link
                  key={t.id}
                  href={`/task/${t.id}`}
                  className="block px-3 py-1.5 rounded-lg text-xs hover:bg-surface-2 truncate text-text-2 hover:text-text border border-transparent hover:border-border transition-colors"
                  title={t.query}
                >
                  <div className="truncate font-medium">{t.query}</div>
                  <div className="text-[10px] text-text-3 font-mono capitalize">
                    {t.status.replace(/_/g, " ")}
                  </div>
                </Link>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* ─── Department / Session Footer ─────────────────────────── */}
      <div className="p-3 border-t border-border-subtle bg-bg-base/70">
        <div className="flex items-center justify-between gap-2 p-2 rounded-xl bg-surface border border-border">
          <div className="min-w-0">
            <p className="text-xs font-semibold text-text truncate">
              {session?.name || "Refinery Engineer"}
            </p>
            <p className="text-[10px] font-mono text-accent truncate">
              {session?.department || "OPERATIONS"}
            </p>
          </div>
          <button
            onClick={() => {
              logout();
              router.push("/");
            }}
            className="p-1.5 rounded-lg text-text-3 hover:text-red hover:bg-red/10 transition-colors"
            title="Log out of session"
          >
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
            >
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
              <polyline points="16 17 21 12 16 7" />
              <line x1="21" y1="12" x2="9" y2="12" />
            </svg>
          </button>
        </div>
      </div>
    </aside>
  );
}
