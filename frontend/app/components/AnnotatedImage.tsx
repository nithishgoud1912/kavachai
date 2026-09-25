"use client";

import React, { useState } from "react";
import Image from "next/image";
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
  boxes = [],
  caption = "Visual observations require review against the original image.",
  modelUsed,
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
        {/* Use the actual authorized local image. */}
        {imageUrl.startsWith("/") && !imageUrl.startsWith("//") && !imageUrl.includes("\\") ?
          <Image src={imageUrl} alt={alt} fill unoptimized className="object-fill" /> :
          <p>Local source image unavailable</p>}

        {/* Bounding box overlays */}
        {showBoxes && (
          <div className="absolute inset-0 pointer-events-none">
            {boxes.map((box, i) => {
              // Convert 0-1000 scale to %
              if (box.box_2d.length !== 4 || box.box_2d.some(v => !Number.isFinite(v) || v < 0 || v > 1000)) return null;
              const scale = box.box_2d.every(v => v <= 1) ? 100 : 0.1;
              const [ymin, xmin, ymax, xmax] = box.box_2d.map(v => v * scale);
              if (ymax <= ymin || xmax <= xmin) return null;
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
