"use client";

import React, { useRef, useState, DragEvent } from "react";
import type { AttachmentItem } from "@/app/types";

interface AttachmentDropzoneProps {
  attachments: AttachmentItem[];
  onChange: (attachments: AttachmentItem[]) => void;
  className?: string;
}

function formatBytes(bytes?: number): string {
  if (!bytes) return "0 B";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function getIcon(name: string): string {
  const ext = name.split(".").pop()?.toLowerCase();
  if (ext === "pdf") return "📕";
  if (["png", "jpg", "jpeg", "webp"].includes(ext || "")) return "🖼️";
  if (["csv", "xlsx", "xls"].includes(ext || "")) return "📊";
  if (["doc", "docx"].includes(ext || "")) return "📄";
  if (["py", "js", "ts", "json"].includes(ext || "")) return "💻";
  return "📎";
}

export default function AttachmentDropzone({
  attachments,
  onChange,
  className = "",
}: AttachmentDropzoneProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleFiles = (files: FileList | null) => {
    if (!files) return;
    const newItems: AttachmentItem[] = Array.from(files).map((f) => ({
      filename: f.name,
      url: URL.createObjectURL(f),
      type: f.type.startsWith("image/") ? "image" : "document",
      size: f.size,
    }));
    onChange([...attachments, ...newItems]);
  };

  const handleDragOver = (e: DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    handleFiles(e.dataTransfer.files);
  };

  const removeAttachment = (index: number) => {
    onChange(attachments.filter((_, i) => i !== index));
  };

  return (
    <div className={`space-y-2 ${className}`}>
      {/* Hidden file input */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={(e) => handleFiles(e.target.files)}
        multiple
        accept=".pdf,.png,.jpg,.jpeg,.docx,.xlsx,.csv,.py,.txt"
        className="hidden"
      />

      {/* Drag & Drop Trigger Bar */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`p-3 rounded-xl border border-dashed transition-all cursor-pointer text-center ${
          isDragging
            ? "border-accent bg-accent/5 text-accent"
            : "border-border hover:border-accent/40 bg-surface-2/40 hover:bg-surface-2 text-text-3 hover:text-text-2"
        }`}
      >
        <div className="flex items-center justify-center gap-2 text-xs">
          <span>📎</span>
          <span className="font-medium">
            Drag & drop engineering files, scanned P&IDs, or vibration logs
          </span>
          <span className="text-[11px] underline opacity-80">(or browse)</span>
        </div>
      </div>

      {/* Attached Files List */}
      {attachments.length > 0 && (
        <div className="flex flex-wrap gap-2 pt-1">
          {attachments.map((file, idx) => (
            <div
              key={idx}
              className="inline-flex items-center gap-2 px-2.5 py-1 rounded-lg bg-surface border border-border text-xs font-mono"
            >
              <span>{getIcon(file.filename)}</span>
              <span className="truncate max-w-[160px] text-text font-medium">
                {file.filename}
              </span>
              <span className="text-[10px] text-text-3">{formatBytes(file.size)}</span>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  removeAttachment(idx);
                }}
                className="text-text-3 hover:text-red leading-none ml-1"
                title="Remove attachment"
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
