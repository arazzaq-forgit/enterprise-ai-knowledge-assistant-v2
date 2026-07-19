import React from "react";
import { Accessibility, Navigation } from "lucide-react";
import { P, GRADIENTS, occColor, glass, glow } from "../theme.js";
import { Sparkline } from "./Sparkline.jsx";

export function GateDetailCard({ gate, onRoute, history }) {
  if (!gate) return (
    <div className="rounded-xl border p-4 f-body text-xs text-[#8B98BE] flex items-center gap-2" style={{ borderColor: P.panelBorder, background: P.panel2 }}>
      <Navigation size={13} className="opacity-50" /> Tap a gate on the map to see live details.
    </div>
  );
  const series = history.map((h) => h[gate.id]).filter((v) => v !== undefined);
  const color = occColor(gate.occ);
  return (
    <div className="fade-up rounded-xl border p-4 lift-hover" style={{ ...glass(P.panelBorder), boxShadow: glow(color, 10) }}>
      <div className="flex items-center justify-between mb-2">
        <p className="f-body text-sm font-semibold text-white">{gate.name}</p>
        {gate.accessible && <Accessibility size={15} color={P.green} aria-label="Wheelchair accessible" />}
      </div>
      <div className="flex items-center justify-between mb-3">
        <div className="flex gap-4">
          <div>
            <p className="f-display text-2xl leading-none number-in" style={{ color }}>{gate.occ}%</p>
            <p className="f-body text-[10px] text-[#8B98BE] mt-1">occupancy</p>
          </div>
          <div>
            <p className="f-display text-2xl leading-none text-white number-in">{gate.wait}<span className="text-xs text-[#8B98BE] f-body"> min</span></p>
            <p className="f-body text-[10px] text-[#8B98BE] mt-1">est. wait</p>
          </div>
        </div>
        <Sparkline series={series} color={color} />
      </div>
      <button onClick={() => onRoute(gate)}
        className="press w-full f-body text-xs font-semibold rounded-lg py-2 flex items-center justify-center gap-1.5"
        style={{ background: GRADIENTS.primary, color: "#06170D", boxShadow: glow(P.green, 12) }}>
        <Navigation size={13} /> Route me here
      </button>
    </div>
  );
}
