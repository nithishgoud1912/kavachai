"use client";

import { useEffect, useRef, useState } from "react";

interface ConfidenceRingProps {
  confidence: number; // 0-100
  size?: number;
}

export default function ConfidenceRing({
  confidence,
  size = 100,
}: ConfidenceRingProps) {
  const [animated, setAnimated] = useState(false);
  const ringRef = useRef<SVGCircleElement>(null);

  const strokeWidth = 6;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (confidence / 100) * circumference;

  useEffect(() => {
    // Trigger animation after mount
    const timer = setTimeout(() => setAnimated(true), 100);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          {/* Background track */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="var(--color-surface-2)"
            strokeWidth={strokeWidth}
          />
          {/* Progress ring */}
          <circle
            ref={ringRef}
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="var(--color-accent)"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={animated ? offset : circumference}
            style={{
              transition: "stroke-dashoffset 1.2s cubic-bezier(0.16, 1, 0.3, 1)",
            }}
          />
        </svg>
        {/* Center number */}
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="font-[family-name:var(--font-mono)] text-2xl text-accent font-semibold">
            {confidence}
          </span>
        </div>
      </div>
      <span className="text-text-3 text-xs">Confidence</span>
    </div>
  );
}
