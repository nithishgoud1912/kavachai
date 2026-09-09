"use client";

import React, { useMemo, useState } from "react";
import { marked } from "marked";
import MermaidDiagram from "@/app/components/MermaidDiagram";

// Configure marked for GitHub-flavored markdown with line breaks
marked.setOptions({
  gfm: true,
  breaks: true,
});

interface MarkdownMessageProps {
  content: string;
  className?: string;
}

interface ContentBlock {
  type: "markdown" | "code";
  lang?: string;
  content: string;
}

// ─── Code Card with Copy Button ───────────────────────────────────────
function CodeCard({ lang, code }: { lang?: string; code: string }) {
  const [copied, setCopied] = useState(false);

  function handleCopy() {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  const displayLang = lang ? lang.toUpperCase() : "CODE";

  return (
    <div
      style={{
        margin: "12px 0",
        borderRadius: "10px",
        overflow: "hidden",
        border: "1px solid var(--color-border)",
        background: "#18181b",
        boxShadow: "0 2px 8px rgba(0, 0, 0, 0.08)",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "6px 14px",
          background: "#27272a",
          borderBottom: "1px solid #3f3f46",
          fontSize: "0.6875rem",
        }}
      >
        <span
          style={{
            fontFamily: "var(--font-mono)",
            fontWeight: 600,
            color: "#a1a1aa",
            letterSpacing: "0.06em",
          }}
        >
          {displayLang}
        </span>
        <button
          type="button"
          onClick={handleCopy}
          style={{
            background: copied ? "rgba(45, 138, 110, 0.2)" : "rgba(255, 255, 255, 0.06)",
            border: "1px solid",
            borderColor: copied ? "var(--color-teal)" : "#52525b",
            borderRadius: "6px",
            padding: "3px 8px",
            color: copied ? "#4ade80" : "#d4d4d8",
            fontSize: "0.6875rem",
            cursor: "pointer",
            display: "inline-flex",
            alignItems: "center",
            gap: "4px",
            transition: "all 0.15s ease",
          }}
        >
          {copied ? "✓ Copied" : "📋 Copy"}
        </button>
      </div>
      <pre
        className="code-card-pre"
        style={{
          margin: 0,
          padding: "14px 16px",
          overflowX: "auto",
          fontSize: "0.8125rem",
          lineHeight: "1.55",
          color: "#f4f4f5",
          background: "#18181b",
          fontFamily: "var(--font-mono)",
        }}
      >
        <code
          className="code-card-code"
          style={{
            background: "transparent",
            color: "#f4f4f5",
            padding: 0,
            borderRadius: 0,
            fontFamily: "var(--font-mono)",
            display: "block",
            whiteSpace: "pre",
          }}
        >
          {code}
        </code>
      </pre>
    </div>
  );
}

// ─── Markdown Parser Using Marked ─────────────────────────────────────
export function renderMarkdown(text: string): string {
  if (!text) return "";
  try {
    return marked.parse(text) as string;
  } catch {
    return text.replace(/\n/g, "<br/>");
  }
}

export function parseMessageBlocks(rawText: string): ContentBlock[] {
  if (!rawText) return [];

  // Normalize pseudo-headings before code fences (e.g. "### ```mermaid")
  const normalized = rawText.replace(/^[ \t]*#{1,6}[ \t]*```/gm, "```");

  const blocks: ContentBlock[] = [];
  // Regex to match code fences (closed OR unclosed at end of message)
  const codeBlockRegex = /```([\w-]*)\s*[\n\r]([\s\S]*?)(?:```|$)/g;

  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = codeBlockRegex.exec(normalized)) !== null) {
    const [fullMatch, lang, code] = match;
    const startIndex = match.index;

    // Push preceding markdown if non-empty
    if (startIndex > lastIndex) {
      const preceding = normalized.substring(lastIndex, startIndex);
      if (preceding.trim()) {
        blocks.push({ type: "markdown", content: preceding });
      }
    }

    blocks.push({
      type: "code",
      lang: lang || "code",
      content: code.trim(),
    });

    lastIndex = startIndex + fullMatch.length;
  }

  // Push remaining text
  if (lastIndex < normalized.length) {
    const remaining = normalized.substring(lastIndex);
    if (remaining.trim()) {
      blocks.push({ type: "markdown", content: remaining });
    }
  }

  // Fallback
  if (blocks.length === 0 && normalized.trim()) {
    blocks.push({ type: "markdown", content: normalized });
  }

  return blocks;
}

export default function MarkdownMessage({ content, className = "" }: MarkdownMessageProps) {
  const blocks = useMemo(() => parseMessageBlocks(content), [content]);

  return (
    <div className={`markdown-message-content ${className}`}>
      {blocks.map((block, index) => {
        if (block.type === "code") {
          if (block.lang?.toLowerCase() === "mermaid") {
            return (
              <MermaidDiagram
                key={`mermaid-${index}-${block.content.substring(0, 15)}`}
                code={block.content}
              />
            );
          }

          return (
            <CodeCard
              key={`code-${index}-${block.content.substring(0, 15)}`}
              lang={block.lang}
              code={block.content}
            />
          );
        }

        return (
          <div
            key={`md-${index}`}
            dangerouslySetInnerHTML={{ __html: renderMarkdown(block.content) }}
          />
        );
      })}
    </div>
  );
}
