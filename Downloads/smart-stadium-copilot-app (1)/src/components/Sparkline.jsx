import React, { memo } from "react";

function Sparkline({ series, color, width = 110, height = 30 }) {
  if (!series || series.length < 2) return <div style={{ height }} />;
  const pts = series.map((v, i) => {
    const x = (i / (series.length - 1)) * width;
    const y = height - (v / 100) * height;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(" ");
  return (
    <svg width={width} height={height} role="img" aria-label="Occupancy trend, last few minutes">
      <polyline points={pts} fill="none" stroke={color} strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

const MemoizedSparkline = memo(Sparkline);
export default MemoizedSparkline;
export { MemoizedSparkline as Sparkline };
