import React, { useState, useMemo } from "react";
import { MapPinned, Loader2, History, ChevronDown, ChevronUp, Sparkles } from "lucide-react";
import { P, GRADIENTS, glass, glow } from "../theme.js";
import { rankGates } from "../lib/gateData.js";
import { askCopilot } from "../lib/askCopilot.js";

function ConfidenceGauge({ value, size = 96, stroke = 9 }) {
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const pct = Math.min(1, Math.max(0, value / 100));
  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <defs>
          <linearGradient id="gaugeGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor={P.green} />
            <stop offset="100%" stopColor={P.cyan} />
          </linearGradient>
        </defs>
        <circle cx={size / 2} cy={size / 2} r={r} stroke="#1A2440" strokeWidth={stroke} fill="none" />
        <circle
          cx={size / 2} cy={size / 2} r={r} stroke="url(#gaugeGrad)" strokeWidth={stroke} fill="none"
          strokeDasharray={c} strokeDashoffset={c * (1 - pct)} strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 0.9s cubic-bezier(0.22,1,0.36,1)", filter: `drop-shadow(0 0 6px ${P.green}88)` }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="f-display text-3xl text-white leading-none">{value}</span>
        <span className="f-body text-[9px] text-[#8B98BE] tracking-wide">SCORE</span>
      </div>
    </div>
  );
}

/**
 * The centerpiece explainable-AI feature. Two-stage design:
 *  1. Deterministic: rankGates() (pure, unit-tested) computes an
 *     auditable factor-by-factor score for EVERY gate.
 *  2. Generative: the model only narrates the already-computed numbers
 *     in the fan's language — it never invents the score itself.
 */
export function ExplainableGateFinder({ gates, accessMode, lang, onRecommend }) {
  const [section, setSection] = useState("");
  const [loading, setLoading] = useState(false);
  const [reasoning, setReasoning] = useState("");
  const [showAll, setShowAll] = useState(false);
  const [history, setHistory] = useState([]);

  const ranked = useMemo(() => {
    try { return rankGates(gates, accessMode); } catch { return []; }
  }, [gates, accessMode]);
  const top = ranked[0] || null;

  const find = async () => {
    if (loading || !top) return;
    setLoading(true);
    setReasoning("");
    const sys = `You are an accessibility-aware wayfinding assistant for FIFA World Cup 2026. Respond ONLY in ${lang}, in 2-3 short sentences, warm and practical. Do NOT invent numbers — reference only the scores given below. A transparent scoring algorithm (not you) has already determined the best gate. Your job is only to explain WHY in clear, human language a fan can quickly understand.

Fan's accessibility preference: ${accessMode}. Fan's seat section: ${section || "not provided"}.
Top-ranked gate: ${top.name} (id ${top.id}) — occupancy score ${top.occupancyScore}/100, wait-time score ${top.waitScore}/100, accessibility-match score ${top.accessibilityScore}/100, overall ${top.overall}/100.
Runner-up for context: ${ranked[1] ? `${ranked[1].name}, overall ${ranked[1].overall}/100` : "none"}.`;
    const out = await askCopilot(sys, "Explain this recommendation to the fan.");
    setReasoning(out);
    setHistory((h) => [{ gate: top.id, overall: top.overall, ts: new Date() }, ...h].slice(0, 6));
    onRecommend(top.id);
    setLoading(false);
  };

  if (!top) {
    return (
      <div className="rounded-2xl border p-4 f-body text-xs text-[#8B98BE]" style={{ borderColor: P.panelBorder, background: P.panel }}>
        No gate data available to score.
      </div>
    );
  }

  const factors = [
    { label: "Occupancy fit", value: top.occupancyScore, grad: "linear-gradient(90deg,#1FBF6B,#5EE8A5)" },
    { label: "Wait time", value: top.waitScore, grad: "linear-gradient(90deg,#4EA8F5,#22D3EE)" },
    { label: "Accessibility match", value: top.accessibilityScore, grad: "linear-gradient(90deg,#F5A524,#FBBF24)" },
  ];

  return (
    <div className="rounded-2xl border p-4 space-y-3 lift-hover" style={{ ...glass(P.panelBorder), boxShadow: reasoning ? glow(P.green, 16) : "none" }}>
      <div className="flex items-center justify-between">
        <h3 className="f-body text-sm font-semibold text-white flex items-center gap-2">
          <MapPinned size={15} color={P.blue} /> Find My Best Gate
        </h3>
        <span className="f-body text-[9px] px-2 py-0.5 rounded-full border flex items-center gap-1" style={{ borderColor: P.panelBorder, color: P.muted }}>
          <Sparkles size={9} /> EXPLAINABLE AI
        </span>
      </div>
      <p className="f-body text-[11px] text-[#8B98BE] -mt-1">
        Every gate is scored by a transparent, published formula (40% occupancy, 30% wait time, 30% accessibility match) —
        the AI&apos;s job is only to explain the result in plain language, never to invent the numbers.
      </p>
      <div className="flex gap-2">
        <input value={section} onChange={(e) => setSection(e.target.value)} placeholder="Seat section (e.g. 214) — optional, for context"
          aria-label="Seat section"
          className="flex-1 f-body text-sm rounded-lg px-3 py-2 text-white placeholder-[#5c6a8c] outline-none border transition-colors focus:border-[#4EA8F5]"
          style={{ background: P.panel2, borderColor: P.panelBorder }} />
        <button onClick={find} disabled={loading}
          className="press f-body text-xs font-semibold rounded-lg px-3.5 py-2 disabled:opacity-50 flex items-center gap-1.5 text-[#06110A]"
          style={{ background: GRADIENTS.blue, boxShadow: glow(P.blue, 14) }}>
          {loading ? <Loader2 size={13} className="animate-spin" /> : <MapPinned size={13} />} Explain Best Gate
        </button>
      </div>

      <div className="fade-up rounded-xl p-4 border space-y-4" style={{ background: P.panel2, borderColor: P.panelBorder }}>
        <div className="flex items-center gap-4">
          <ConfidenceGauge value={top.overall} />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="f-display text-3xl text-white leading-none">Gate {top.id}</span>
              <span className="f-mono text-[10px] px-2 py-0.5 rounded-full" style={{ background: "rgba(31,191,107,0.14)", color: P.green, border: `1px solid ${P.green}44` }}>TOP RANKED</span>
            </div>
            <p className="f-body text-[11px] text-[#8B98BE] mt-1 truncate">{top.name}</p>
          </div>
        </div>

        <div className="space-y-2.5">
          {factors.map((f) => (
            <div key={f.label}>
              <div className="flex justify-between f-body text-[10px] text-[#8B98BE] mb-1">
                <span>{f.label}</span><span className="f-mono text-[#c8d3ec]">{f.value}/100</span>
              </div>
              <div className="h-2 rounded-full overflow-hidden" style={{ background: "#1A2440" }}>
                <div className="grow-bar h-full rounded-full" style={{ width: `${f.value}%`, background: f.grad }} />
              </div>
            </div>
          ))}
        </div>

        {reasoning ? (
          <p className="f-body text-xs text-[#dbe4f5] leading-relaxed border-t pt-3" style={{ borderColor: P.panelBorder }}>{reasoning}</p>
        ) : (
          <p className="f-body text-xs text-[#8B98BE] border-t pt-3" style={{ borderColor: P.panelBorder }}>
            Click &quot;Explain Best Gate&quot; for a plain-language explanation of this ranking.
          </p>
        )}
      </div>

      <button onClick={() => setShowAll((s) => !s)} className="flex items-center gap-1 f-body text-[11px] text-[#8B98BE] hover:text-white transition-colors">
        {showAll ? <ChevronUp size={13} /> : <ChevronDown size={13} />} {showAll ? "Hide" : "Show"} full ranking (all {ranked.length} gates, fully auditable)
      </button>
      {showAll && (
        <div className="space-y-1.5 stagger">
          {ranked.map((g, i) => (
            <div key={g.id} className="flex items-center gap-2 f-body text-[11px] text-[#c8d3ec]">
              <span className="f-mono w-4 text-[#54608A]">{i + 1}</span>
              <span className="w-24 truncate">{g.name}</span>
              <div className="flex-1 h-1.5 rounded-full overflow-hidden" style={{ background: "#1A2440" }}>
                <div className="h-full rounded-full" style={{ width: `${g.overall}%`, background: i === 0 ? GRADIENTS.primary : P.mutedDark }} />
              </div>
              <span className="f-mono w-8 text-right">{g.overall}</span>
            </div>
          ))}
        </div>
      )}

      {history.length > 0 && (
        <div>
          <div className="flex items-center gap-1.5 f-body text-[10px] text-[#54608A] mt-1 mb-1"><History size={11} /> RECOMMENDATION LOG (this session)</div>
          <div className="space-y-1.5 max-h-28 overflow-y-auto pr-1">
            {history.map((h, i) => (
              <div key={i} className="f-body text-[10px] text-[#8B98BE] flex justify-between border-b pb-1" style={{ borderColor: "#182238" }}>
                <span>Gate {h.gate} · score {h.overall}/100</span>
                <span className="f-mono">{h.ts.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
