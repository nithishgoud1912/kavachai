"use client";

import React, { useEffect } from "react";

export interface ToastMessage {
  id: string;
  type: "success" | "error" | "info" | "warning";
  title: string;
  message?: string;
}

interface ToastProps {
  toast: ToastMessage | null;
  onClose: () => void;
  durationMs?: number;
}

export default function Toast({ toast, onClose, durationMs = 4000 }: ToastProps) {
  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(onClose, durationMs);
    return () => clearTimeout(timer);
  }, [toast, durationMs, onClose]);

  if (!toast) return null;

  let borderColor = "border-border";
  let bgColor = "bg-surface";
  let icon = "ℹ️";

  if (toast.type === "success") {
    borderColor = "border-[#2D794D]/30";
    bgColor = "bg-[#E9F0EC]";
    icon = "✅";
  } else if (toast.type === "error") {
    borderColor = "border-[#B83838]/30";
    bgColor = "bg-[#F2E6E3]";
    icon = "⚠️";
  } else if (toast.type === "warning") {
    borderColor = "border-[#B8860B]/30";
    bgColor = "bg-[#F6ECCF]";
    icon = "🔔";
  }

  return (
    <div className="fixed bottom-6 right-6 z-50 animate-in slide-in-from-bottom-3 duration-200">
      <div
        className={`flex items-start gap-3 p-4 rounded-xl border shadow-lg ${borderColor} ${bgColor} max-w-sm`}
      >
        <span className="text-base">{icon}</span>
        <div className="flex-1 space-y-0.5">
          <p className="text-xs font-semibold text-text">{toast.title}</p>
          {toast.message && <p className="text-xs text-text-2">{toast.message}</p>}
        </div>
        <button
          onClick={onClose}
          className="text-text-3 hover:text-text text-sm leading-none p-1"
          aria-label="Close toast"
        >
          ✕
        </button>
      </div>
    </div>
  );
}
