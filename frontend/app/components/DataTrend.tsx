"use client";

interface DataPoint {
  label: string;
  value: number;
}

interface DataTrendProps {
  title: string;
  data: DataPoint[];
  unit?: string;
  threshold?: number;
  thresholdLabel?: string;
}

export default function DataTrend({
  title,
  data,
  unit = "",
  threshold,
  thresholdLabel,
}: DataTrendProps) {
  if (!data || data.length === 0) return null;

  const values = data.map((d) => d.value);
  const min = Math.min(...values, threshold ?? Infinity) * 0.85;
  const max = Math.max(...values, threshold ?? -Infinity) * 1.15;
  const range = max - min || 1;

  const width = 320;
  const height = 140;
  const padding = { top: 20, right: 30, bottom: 35, left: 45 };
  const chartW = width - padding.left - padding.right;
  const chartH = height - padding.top - padding.bottom;

  const xStep = chartW / (data.length - 1 || 1);

  function toY(val: number) {
    return padding.top + chartH - ((val - min) / range) * chartH;
  }

  // Build line path
  const linePath = data
    .map((d, i) => {
      const x = padding.left + i * xStep;
      const y = toY(d.value);
      return `${i === 0 ? "M" : "L"} ${x} ${y}`;
    })
    .join(" ");

  return (
    <div className="bg-surface border border-border rounded-xl p-5 animate-fade-in-up-small">
      <h4 className="text-sm text-text-2 mb-4">{title}</h4>

      <svg viewBox={`0 0 ${width} ${height}`} className="w-full max-w-xs">
        {/* Grid lines */}
        {[0, 0.25, 0.5, 0.75, 1].map((frac) => {
          const y = padding.top + chartH * (1 - frac);
          const val = min + range * frac;
          return (
            <g key={frac}>
              <line
                x1={padding.left}
                y1={y}
                x2={padding.left + chartW}
                y2={y}
                stroke="var(--color-border)"
                strokeWidth="0.5"
                strokeDasharray="3,3"
              />
              <text
                x={padding.left - 6}
                y={y + 3}
                textAnchor="end"
                className="text-[8px] fill-[var(--color-text-3)]"
                fontFamily="var(--font-mono)"
              >
                {val.toFixed(1)}
              </text>
            </g>
          );
        })}

        {/* Threshold line */}
        {threshold !== undefined && (
          <g>
            <line
              x1={padding.left}
              y1={toY(threshold)}
              x2={padding.left + chartW}
              y2={toY(threshold)}
              stroke="var(--color-orange)"
              strokeWidth="1"
              strokeDasharray="5,3"
            />
            <text
              x={padding.left + chartW + 3}
              y={toY(threshold) + 3}
              className="text-[7px] fill-[var(--color-orange)]"
              fontFamily="var(--font-mono)"
            >
              {thresholdLabel || `${threshold}${unit ? ` ${unit}` : ""}`}
            </text>
          </g>
        )}

        {/* Data line */}
        <path
          d={linePath}
          fill="none"
          stroke="var(--color-accent)"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Data points */}
        {data.map((d, i) => {
          const x = padding.left + i * xStep;
          const y = toY(d.value);
          return (
            <g key={i}>
              <circle cx={x} cy={y} r="4" fill="var(--color-accent)" />
              <circle cx={x} cy={y} r="2" fill="var(--color-bg)" />
              {/* X-axis label */}
              <text
                x={x}
                y={height - 8}
                textAnchor="middle"
                className="text-[8px] fill-[var(--color-text-3)]"
                fontFamily="var(--font-mono)"
              >
                {d.label}
              </text>
            </g>
          );
        })}
      </svg>

      {unit && (
        <p className="text-text-3 text-xs font-[family-name:var(--font-mono)] mt-2">
          {unit}
        </p>
      )}
    </div>
  );
}
