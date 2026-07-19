import React, { useMemo } from "react";
import { Accessibility } from "lucide-react";
import { P, GRADIENTS, occColor, glow } from "../theme.js";

export function StadiumMap({ gates, selected, onSelect, highlightAccessible }) {
  const positions = useMemo(() => {
    const n = gates.length;
    return gates.map((g, i) => {
      const angle = (-90 + i * (360 / n)) * (Math.PI / 180);
      return { ...g, x: 50 + 42 * Math.cos(angle), y: 50 + 40 * Math.sin(angle) };
    });
  }, [gates]);

  return (
    <div
      className="relative w-full select-none"
      role="group"
      aria-label="Interactive stadium gate map"
      // Explicit inline sizing (not a Tailwind arbitrary class) — guarantees
      // this box always has real height, so the absolutely-positioned gate
      // buttons inside it can never collapse and bleed into the UI above.
      style={{ aspectRatio: "10 / 8", minHeight: 240 }}
    >
      <div className="absolute breathe-glow" aria-hidden="true" style={{
        left: "50%", top: "50%", width: "70%", height: "60%", transform: "translate(-50%,-50%)",
        background: "radial-gradient(ellipse at center, rgba(31,191,107,0.16) 0%, rgba(31,191,107,0) 70%)",
        filter: "blur(4px)", pointerEvents: "none",
      }} />

      <div className="absolute rounded-[2rem] border shadow-2xl" style={{
        left: "27%", top: "26%", width: "46%", height: "48%",
        background: GRADIENTS.pitch, borderColor: "#1FBF6B44",
        boxShadow: `${glow(P.green, 30)}, inset 0 0 40px rgba(0,0,0,0.35)`,
      }} aria-hidden="true">
        <div className="absolute inset-2 rounded-[1.6rem] border border-[#1FBF6B33]" />
        <div className="absolute left-1/2 top-1/2 w-10 h-10 -translate-x-1/2 -translate-y-1/2 rounded-full border border-[#1FBF6B44]" />
        <div className="absolute left-1/2 top-0 bottom-0 w-px" style={{ background: "#1FBF6B33" }} />
      </div>

      {positions.map((g) => {
        const active = selected === g.id;
        const critical = g.occ >= 85;
        const busy = g.occ >= 60;
        const color = occColor(g.occ);
        return (
          <div key={g.id} className="absolute -translate-x-1/2 -translate-y-1/2" style={{ left: `${g.x}%`, top: `${g.y}%`, zIndex: 2 }}>
            {busy && (
              <>
                <span className="crowd-dot absolute rounded-full" style={{ width: 4, height: 4, background: color, top: -10, left: -14 }} aria-hidden="true" />
                <span className="crowd-dot absolute rounded-full" style={{ width: 3, height: 3, background: color, top: -6, left: 16, animationDelay: "0.5s" }} aria-hidden="true" />
                {critical && <span className="crowd-dot absolute rounded-full" style={{ width: 3, height: 3, background: color, top: 14, left: -18, animationDelay: "1s" }} aria-hidden="true" />}
              </>
            )}
            <button
              onClick={() => onSelect(g.id)}
              aria-pressed={active}
              aria-label={`${g.name}, ${g.occ}% occupancy, ${g.wait} minute wait${g.accessible ? ", wheelchair accessible" : ""}`}
              className={`press lift-hover relative rounded-full flex flex-col items-center justify-center f-display ${critical ? "ring-pulse" : ""}`}
              style={{
                width: active ? 68 : 58, height: active ? 68 : 58,
                background: active ? `linear-gradient(145deg, ${color}33, ${color}11)` : `${color}1A`,
                backdropFilter: "blur(6px)",
                border: `2px solid ${active ? P.ice : color}`,
                color: P.ice,
                boxShadow: active ? `0 0 0 4px rgba(255,255,255,0.08), ${glow(color, 18)}` : glow(color, 10),
              }}
            >
              {highlightAccessible && g.accessible && (
                <div className="absolute -top-1 -right-1 rounded-full bg-[#0A0F1D] p-0.5" style={{ boxShadow: glow(P.green, 8) }}>
                  <Accessibility size={12} color={P.green} />
                </div>
              )}
              <span className="text-2xl leading-none">{g.id}</span>
              <span className="f-mono text-[9px] leading-none mt-0.5" style={{ color }}>{g.occ}%</span>
            </button>
          </div>
        );
      })}
    </div>
  );
}
