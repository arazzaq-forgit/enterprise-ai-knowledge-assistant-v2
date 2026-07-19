import React from "react";
import { P } from "../theme.js";

export function Ticker({ gates, match }) {
  const busiest = [...gates].sort((a, b) => b.occ - a.occ)[0];
  const items = [
    `⚽ ${match.home} ${match.scoreH}–${match.scoreA} ${match.away} · ${match.minute}' · ${match.stage}`,
    `🚧 Busiest: ${busiest.name} at ${busiest.occ}% capacity`,
    `🌦 24°C, clear · fan-zone conditions normal`,
    `🚌 Metro Line 2 running on schedule`,
  ];
  const doubled = [...items, ...items];
  return (
    <div className="relative overflow-hidden border-b" style={{ borderColor: P.panelBorder, background: "#0D1526" }} aria-hidden="true">
      <div className="ticker-track flex whitespace-nowrap gap-10 f-mono text-[11px] py-1.5 w-max" style={{ color: "#7fdc9a" }}>
        {doubled.map((it, i) => <span key={i} className="px-2">{it}</span>)}
      </div>
      <div className="absolute inset-y-0 left-0 w-10 pointer-events-none" style={{ background: "linear-gradient(90deg, #0D1526, transparent)" }} />
      <div className="absolute inset-y-0 right-0 w-10 pointer-events-none" style={{ background: "linear-gradient(270deg, #0D1526, transparent)" }} />
    </div>
  );
}
