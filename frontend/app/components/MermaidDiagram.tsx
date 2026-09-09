"use client";

import { useEffect, useRef, useState, useId } from "react";
import mermaid from "mermaid";

interface MermaidDiagramProps {
  code: string;
  className?: string;
}

let mermaidInitialized = false;

function initMermaid() {
  if (mermaidInitialized || typeof window === "undefined") return;
  mermaid.initialize({
    startOnLoad: false,
    securityLevel: "loose",
    theme: "base",
    themeVariables: {
      primaryColor: "#f5efe6",
      primaryTextColor: "#2d2a26",
      primaryBorderColor: "#c7bcab",
      lineColor: "#655f56",
      secondaryColor: "#ffffff",
      tertiaryColor: "#eee8df",
      background: "#ffffff",
      mainBkg: "#faf8f5",
      nodeBorder: "#c7bcab",
      clusterBkg: "#faf8f5",
      clusterBorder: "#d9d0c3",
      titleColor: "#2d2a26",
      fontFamily: "Outfit, -apple-system, BlinkMacSystemFont, sans-serif",
      fontSize: "13px",
      edgeLabelBackground: "#ffffff",
    },
    flowchart: {
      htmlLabels: true,
      curve: "basis",
    },
  });
  mermaidInitialized = true;
}

function sanitizeMermaidCode(raw: string): string {
  let code = raw.trim();

  // Strip wrapping markdown code fences if present
  code = code.replace(/^```(?:mermaid)?\s*/i, "").replace(/```$/, "").trim();

  // If header has statements on the same line, split with newline
  code = code.replace(/^(graph\s+[A-Za-z]{2}|flowchart\s+[A-Za-z]{2})\s+([^\n]+)$/i, "$1\n$2");

  // If subgraph is immediately followed by other items on the same line
  code = code.replace(/(subgraph\s+"[^"]+"|subgraph\s+[\w-]+)\s+(?!\n)/gi, "$1\n");

  // Fix pseudo-connectors like "--connects to--" -> "-->"
  code = code.replace(/--\s*connects\s+to\s*--/gi, "-->");

  // Clean lines
  const lines = code.split("\n").map((line) => {
    let l = line.trim();
    if (!l) return "";

    // If line is an arrow definition commented out with // e.g. "// A --> B"
    if (l.match(/^\/\/\s*[\w\d_-]+\s*(?:-->|---|->|-\.-)\s*[\w\d_-]+/i)) {
      return l.replace(/^\/\/\s*/, "");
    }

    // Convert other // comments to %% comments
    if (l.startsWith("//")) {
      return "%%" + l.substring(2);
    }
    if (l.includes("//")) {
      const parts = l.split("//");
      return parts[0].trimEnd() + " %%" + parts.slice(1).join("//");
    }
    return line;
  });

  // Deduplicate excessive repeating lines from LLM looping
  const deduplicated: string[] = [];
  let prevLine = "";
  let repeatCount = 0;

  for (const line of lines) {
    if (line === prevLine && line.trim()) {
      repeatCount++;
      if (repeatCount <= 2) {
        deduplicated.push(line);
      }
    } else {
      repeatCount = 0;
      prevLine = line;
      deduplicated.push(line);
    }
  }

  code = deduplicated.join("\n");

  // Balance unclosed subgraphs if LLM truncated output
  const subgraphCount = (code.match(/\bsubgraph\b/gi) || []).length;
  const endCount = (code.match(/\bend\b/gi) || []).length;
  if (subgraphCount > endCount) {
    const missingEnds = subgraphCount - endCount;
    code = code + "\n" + Array(missingEnds).fill("end").join("\n");
  }

  return code;
}

export default function MermaidDiagram({ code, className = "" }: MermaidDiagramProps) {
  const [svg, setSvg] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [showCode, setShowCode] = useState<boolean>(false);
  const [copied, setCopied] = useState<boolean>(false);
  const [zoom, setZoom] = useState<number>(1);
  const rawId = useId().replace(/:/g, "_");
  const diagramId = `mermaid_${rawId}`;
  const containerRef = useRef<HTMLDivElement>(null);

  const cleanCode = sanitizeMermaidCode(code);

  useEffect(() => {
    let isCancelled = false;

    async function renderChart() {
      try {
        initMermaid();
        setError(null);

        // Render the diagram
        const { svg: renderedSvg } = await mermaid.render(
          diagramId,
          cleanCode
        );

        if (!isCancelled) {
          setSvg(renderedSvg);
        }
      } catch (err: any) {
        if (!isCancelled) {
          console.warn("[MermaidDiagram] Render error:", err);
          setError(err?.message || "Invalid Mermaid diagram syntax");
          // Remove any stray error elements inserted into DOM by mermaid
          const strayError = document.getElementById(`d${diagramId}`);
          if (strayError) strayError.remove();
        }
      }
    }

    renderChart();

    return () => {
      isCancelled = true;
    };
  }, [cleanCode, diagramId]);

  function handleCopy() {
    navigator.clipboard.writeText(cleanCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  function handleZoomIn() {
    setZoom((z) => Math.min(z + 0.15, 2.5));
  }

  function handleZoomOut() {
    setZoom((z) => Math.max(z - 0.15, 0.5));
  }

  function handleResetZoom() {
    setZoom(1);
  }

  return (
    <div
      className={`mermaid-container ${className}`}
      style={{
        margin: "14px 0",
        border: "1px solid var(--color-border)",
        borderRadius: "12px",
        background: "var(--color-surface)",
        boxShadow: "0 2px 8px rgba(45, 42, 38, 0.04)",
        overflow: "hidden",
      }}
    >
      {/* Header Toolbar */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "8px 14px",
          background: "var(--color-surface-2)",
          borderBottom: "1px solid var(--color-border)",
          fontSize: "0.75rem",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "4px",
              fontWeight: 600,
              color: "var(--color-accent)",
              textTransform: "uppercase",
              letterSpacing: "0.05em",
              fontSize: "0.6875rem",
            }}
          >
            <span>📊</span>
            <span>Mermaid Diagram</span>
          </span>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          {/* Zoom Controls (only shown when rendered and not in code mode) */}
          {!showCode && svg && !error && (
            <div style={{ display: "flex", alignItems: "center", gap: "2px", marginRight: "6px" }}>
              <button
                type="button"
                onClick={handleZoomOut}
                title="Zoom Out"
                style={{
                  background: "var(--color-surface)",
                  border: "1px solid var(--color-border)",
                  borderRadius: "4px",
                  width: "22px",
                  height: "22px",
                  display: "inline-flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: "0.75rem",
                  cursor: "pointer",
                  color: "var(--color-text-2)",
                }}
              >
                -
              </button>
              <button
                type="button"
                onClick={handleResetZoom}
                title="Reset Zoom"
                style={{
                  background: "var(--color-surface)",
                  border: "1px solid var(--color-border)",
                  borderRadius: "4px",
                  padding: "0 6px",
                  height: "22px",
                  display: "inline-flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: "0.6875rem",
                  cursor: "pointer",
                  color: "var(--color-text-2)",
                  fontFamily: "var(--font-mono)",
                }}
              >
                {Math.round(zoom * 100)}%
              </button>
              <button
                type="button"
                onClick={handleZoomIn}
                title="Zoom In"
                style={{
                  background: "var(--color-surface)",
                  border: "1px solid var(--color-border)",
                  borderRadius: "4px",
                  width: "22px",
                  height: "22px",
                  display: "inline-flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: "0.75rem",
                  cursor: "pointer",
                  color: "var(--color-text-2)",
                }}
              >
                +
              </button>
            </div>
          )}

          {/* Toggle Code / Diagram */}
          <button
            type="button"
            onClick={() => setShowCode(!showCode)}
            style={{
              background: showCode ? "var(--color-surface-3)" : "var(--color-surface)",
              border: "1px solid var(--color-border)",
              borderRadius: "6px",
              padding: "4px 8px",
              cursor: "pointer",
              fontSize: "0.6875rem",
              color: "var(--color-text-2)",
              display: "flex",
              alignItems: "center",
              gap: "4px",
            }}
          >
            <span>{showCode ? "🖼️ Diagram" : "📝 Code"}</span>
          </button>

          {/* Copy Code */}
          <button
            type="button"
            onClick={handleCopy}
            style={{
              background: "var(--color-surface)",
              border: "1px solid var(--color-border)",
              borderRadius: "6px",
              padding: "4px 8px",
              cursor: "pointer",
              fontSize: "0.6875rem",
              color: copied ? "var(--color-teal)" : "var(--color-text-2)",
              display: "flex",
              alignItems: "center",
              gap: "4px",
            }}
          >
            <span>{copied ? "✓ Copied" : "📋 Copy"}</span>
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      {showCode ? (
        <pre
          style={{
            margin: 0,
            padding: "16px",
            background: "#1e1e1e",
            color: "#d4d4d4",
            fontSize: "0.8125rem",
            fontFamily: "var(--font-mono)",
            overflowX: "auto",
            lineHeight: 1.5,
          }}
        >
          <code>{cleanCode}</code>
        </pre>
      ) : error ? (
        <div style={{ padding: "16px" }}>
          <div
            style={{
              padding: "10px 14px",
              background: "rgba(186, 56, 56, 0.08)",
              border: "1px solid rgba(186, 56, 56, 0.25)",
              borderRadius: "8px",
              color: "var(--color-red)",
              fontSize: "0.75rem",
              marginBottom: "12px",
            }}
          >
            <strong>Mermaid syntax error:</strong> {error}
          </div>
          <pre
            style={{
              margin: 0,
              padding: "12px",
              background: "var(--color-surface-2)",
              border: "1px solid var(--color-border)",
              borderRadius: "8px",
              fontSize: "0.75rem",
              fontFamily: "var(--font-mono)",
              overflowX: "auto",
            }}
          >
            <code>{cleanCode}</code>
          </pre>
        </div>
      ) : svg ? (
        <div
          ref={containerRef}
          style={{
            padding: "20px",
            overflowX: "auto",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            minHeight: "140px",
            background: "var(--color-surface)",
          }}
        >
          <div
            style={{
              transform: `scale(${zoom})`,
              transformOrigin: "center center",
              transition: "transform 0.15s ease",
              width: "100%",
              display: "flex",
              justifyContent: "center",
            }}
            dangerouslySetInnerHTML={{ __html: svg }}
          />
        </div>
      ) : (
        <div
          style={{
            padding: "32px",
            textAlign: "center",
            color: "var(--color-text-3)",
            fontSize: "0.8125rem",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "8px",
          }}
        >
          <svg className="animate-spin" width="16" height="16" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" opacity="0.3" />
            <path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
          </svg>
          <span>Rendering diagram…</span>
        </div>
      )}
    </div>
  );
}
