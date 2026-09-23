"use client";

import React, { useState } from "react";
import ModelChip from "./ModelChip";

interface BoundingBox {
  label: string;
  box_2d: number[]; // [ymin, xmin, ymax, xmax] in 0-1000 or 0-1 normalized
  confidence?: number;
}

interface AnnotatedImageProps {
  imageUrl: string;
  alt: string;
  boxes?: BoundingBox[];
  caption?: string;
  modelUsed?: string;
  className?: string;
}

export default function AnnotatedImage({
  imageUrl,
  alt,
  boxes = [
    { label: "P-204A Outboard Bearing (Hot Spot: 78.4°C)", box_2d: [300, 320, 650, 680], confidence: 0.98 },
    { label: "Bypass Valve HV-204B (Standby Closed)", box_2d: [150, 700, 350, 880], confidence: 0.94 },
  ],
  caption = "VLM Object & Anomaly Detection on CDU-II P&ID / Thermal Inspection",
  modelUsed = "Qwen2.5-VL · vision",
  className = "",
}: AnnotatedImageProps) {
  const [showBoxes, setShowBoxes] = useState(true);

  return (
    <div className={`space-y-3 p-4 bg-surface border border-border rounded-2xl shadow-xs ${className}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-base">👁️</span>
          <span className="font-serif font-bold text-sm text-text">Multimodal VLM Inspection</span>
        </div>
        <div className="flex items-center gap-2">
          {modelUsed && <ModelChip model={modelUsed} size="sm" />}
          <button
            onClick={() => setShowBoxes(!showBoxes)}
            className="text-xs px-2.5 py-1 rounded-lg border border-border bg-surface-2 hover:bg-surface text-text font-medium"
          >
            {showBoxes ? "Hide Overlays" : "Show Bounding Boxes"}
          </button>
        </div>
      </div>

      {/* Image with SVG bounding-box overlay */}
      <div className="relative aspect-[16/10] bg-surface-2/60 rounded-xl overflow-hidden border border-border flex items-center justify-center">
        {/* Placeholder SVG diagram if image URL is mock */}
        <div className="absolute inset-0 flex flex-col items-center justify-center p-6 text-center text-text-3">
          <svg className="w-full h-full max-h-56 opacity-25" viewBox="0 0 400 240" fill="none" stroke="currentColor">
            <rect x="80" y="80" width="140" height="90" rx="8" strokeWidth="2" />
            <circle cx="150" cy="125" r="30" strokeWidth="2" />
            <path d="M220 125h80M300 80v90M300 125l50 30" strokeWidth="2" />
          </svg>
        </div>

        {/* Bounding box overlays */}
        {showBoxes && (
          <div className="absolute inset-0 pointer-events-none p-4">
            {boxes.map((box, i) => {
              // Convert 0-1000 scale to %
              const [ymin, xmin, ymax, xmax] = box.box_2d.map((v) => (v > 1 ? v / 10 : v * 100));
              const top = `${ymin}%`;
              const left = `${xmin}%`;
              const width = `${xmax - xmin}%`;
              const height = `${ymax - ymin}%`;

              return (
                <div
                  key={i}
                  style={{ top, left, width, height }}
                  className="absolute border-2 border-accent bg-accent/15 rounded-md pointer-events-auto transition-all hover:bg-accent/25"
                >
                  <span className="absolute -top-6 left-0 px-2 py-0.5 rounded bg-accent text-white text-[10px] font-mono font-semibold whitespace-nowrap shadow-xs">
                    {box.label} {box.confidence ? `(${(box.confidence * 100).toFixed(0)}%)` : ""}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {caption && (
        <p className="text-xs text-text-2 leading-relaxed text-center font-mono">
          {caption}
        </p>
      )}
    </div>
  );
}
