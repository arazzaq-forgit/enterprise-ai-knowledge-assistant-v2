import React, { useState } from "react";
import { Clock, Wifi, LayoutGrid, Sparkles, Languages, Siren, Building2, Bus, Armchair, UtensilsCrossed, Accessibility, PhoneCall } from "lucide-react";
import { P, GRADIENTS, glass, glow } from "./theme.js";
import { VENUES, TRANSIT, LANGUAGES, LANG_CODES } from "./data/venues.js";
import { useLiveGates } from "./hooks/useLiveGates.js";
import { useClock } from "./hooks/useClock.js";
import { useNotifications } from "./hooks/useNotifications.js";
import { FontLoader } from "./components/FontLoader.jsx";
import { ErrorBoundary } from "./components/ErrorBoundary.jsx";
import { Ticker } from "./components/Ticker.jsx";
import { NotifBell } from "./components/NotifBell.jsx";
import { ToastStack } from "./components/ToastStack.jsx";
import { StadiumMap } from "./components/StadiumMap.jsx";
import { GateDetailCard } from "./components/GateDetailCard.jsx";
import { CopilotChat } from "./components/CopilotChat.jsx";
import { SOSPanel } from "./components/SOSPanel.jsx";
import { ExplainableGateFinder } from "./components/ExplainableGateFinder.jsx";
import { DataUploadPanel } from "./components/DataUploadPanel.jsx";

const QUICK_ACTIONS = [
  { icon: Armchair, label: "Find my seat" },
  { icon: UtensilsCrossed, label: "Food near me" },
  { icon: Accessibility, label: "Accessible route" },
  { icon: PhoneCall, label: "Call staff" },
];

export default function SmartStadiumCopilot() {
  const [venueId, setVenueId] = useState(VENUES[0].id);
  const venue = VENUES.find((v) => v.id === venueId);
  const [customGates, setCustomGates] = useState(null);
  const [simPaused, setSimPaused] = useState(false);
  const baseGates = customGates || venue.gates;
  const effectivePaused = simPaused || !!customGates;

  const { gates, history } = useLiveGates(baseGates, effectivePaused);
  const { toasts, log, push, dismiss } = useNotifications(gates);
  const now = useClock();

  const [lang, setLang] = useState("English");
  const [accessMode, setAccessMode] = useState("Standard");
  const [selected, setSelected] = useState(null);
  const [quickQuery, setQuickQuery] = useState(null);
  const [sosOpen, setSosOpen] = useState(false);

  const langCode = LANG_CODES[lang] || "en-US";
  const selectedGate = gates.find((g) => g.id === selected) || null;

  const applyCustomData = (parsed) => { setCustomGates(parsed); setSimPaused(true); setSelected(null); };
  const resetToDemo = () => { setCustomGates(null); setSimPaused(false); setSelected(null); };
  const handleVenueChange = (id) => { setVenueId(id); setCustomGates(null); setSimPaused(false); setSelected(null); };

  const sysPrompt = `You are the Smart Stadium Copilot, a wayfinding and accessibility assistant for FIFA World Cup 2026 fans. Respond ONLY in ${lang}. Keep answers to 2-4 short sentences, mobile-friendly, warm and practical. The fan's accessibility preference is: ${accessMode}. Ground answers in this live venue data: ${JSON.stringify({ gates, transit: TRANSIT, match: venue.match })}. Use exact numbers from this data. Never invent gate names not present.`;

  const handleRoute = (gate) => {
    setQuickQuery(`Give me walking directions to ${gate.name} and tell me the current wait time.`);
    push(`Routing you to ${gate.name} — ${gate.wait} min wait.`, "Low");
  };
  const handleSOS = (reason) => push(`SOS: you reported "${reason}" — staff notified`, "High");

  return (
    <div className="min-h-screen f-body" style={{ background: P.bg }}>
      <FontLoader />

      <header className="relative flex items-center justify-between px-6 py-3 border-b flex-wrap gap-3 overflow-hidden" style={{ borderColor: P.panelBorder }}>
        <div className="absolute inset-0 pointer-events-none" style={{ background: GRADIENTS.headerGlow }} aria-hidden="true" />

        <div className="relative flex items-center gap-4">
          <div>
            <p className="f-mono text-[9px] tracking-[0.2em]" style={{ color: P.mutedDark }}>FIFA WORLD CUP 2026 · FAN NAVIGATION &amp; ACCESSIBILITY</p>
            <h1 className="f-display text-2xl tracking-wide leading-none" style={{
              backgroundImage: GRADIENTS.primary, WebkitBackgroundClip: "text", backgroundClip: "text", color: "transparent",
            }}>STADIUM COPILOT</h1>
          </div>
          <div className="flex items-center gap-1.5 rounded-lg px-2 py-1.5 border ml-2 lift-hover" style={{ ...glass(P.panelBorder) }}>
            <Building2 size={13} color={P.muted} />
            <label htmlFor="venue-select" className="sr-only">Venue</label>
            <select id="venue-select" value={venueId} onChange={(e) => handleVenueChange(e.target.value)} className="bg-transparent text-xs f-body text-white outline-none">
              {VENUES.map((v) => <option key={v.id} className="bg-[#0f1830]" value={v.id}>{v.name} · {v.city}</option>)}
            </select>
          </div>
        </div>
        <div className="relative flex items-center gap-4">
          <div className="flex items-center gap-1.5 f-mono text-xs" style={{ color: P.muted }}>
            <Clock size={13} /> {now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
          </div>
          <div className="flex items-center gap-1.5 f-mono text-xs" style={{ color: P.green }}>
            <span className="relative flex h-2 w-2">
              <span className="pulse-dot absolute inline-flex h-full w-full rounded-full" style={{ background: P.green }} />
            </span>
            <Wifi size={13} color={P.green} /> Connected
          </div>
          <NotifBell log={log} />
        </div>
      </header>

      <Ticker gates={gates} match={venue.match} />

      <main className="p-6 max-w-7xl mx-auto space-y-5">
        <div className="grid xl:grid-cols-5 gap-5 stagger">
          <div className="xl:col-span-3 space-y-4">
            <ErrorBoundary>
              <div className="rounded-2xl border p-4 lift-hover" style={glass(P.panelBorder)}>
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-3 gap-2">
                  <h3 className="f-body text-sm font-semibold text-white flex items-center gap-2">
                    <LayoutGrid size={15} color={P.green} /> Live Stadium Map
                  </h3>
                  <div className="flex gap-1.5 flex-wrap" role="radiogroup" aria-label="Accessibility mode">
                    {["Standard", "Wheelchair", "Sensory-friendly"].map((m) => (
                      <button key={m} onClick={() => setAccessMode(m)} role="radio" aria-checked={accessMode === m}
                        className="press f-body text-[10px] px-2.5 py-1 rounded-full border transition-colors"
                        style={{ borderColor: accessMode === m ? P.green : P.panelBorder, background: accessMode === m ? "rgba(31,191,107,0.14)" : "transparent", color: accessMode === m ? P.green : P.muted }}>
                        {m}
                      </button>
                    ))}
                  </div>
                </div>
                <StadiumMap gates={gates} selected={selected} onSelect={setSelected} highlightAccessible={accessMode !== "Standard"} />
              </div>
            </ErrorBoundary>

            <ErrorBoundary>
              <GateDetailCard gate={selectedGate} onRoute={handleRoute} history={history} />
            </ErrorBoundary>

            <ErrorBoundary>
              <ExplainableGateFinder gates={gates} accessMode={accessMode} lang={lang} onRecommend={setSelected} />
            </ErrorBoundary>

            <div className="grid grid-cols-4 gap-2 stagger">
              {QUICK_ACTIONS.map(({ icon: Icon, label }) => (
                <button key={label} onClick={() => setQuickQuery(label)}
                  className="press lift-hover flex flex-col items-center gap-1.5 rounded-xl border py-3"
                  style={glass(P.panelBorder)}>
                  <Icon size={17} color={P.blue} />
                  <span className="f-body text-[10px] text-[#c8d3ec] text-center leading-tight">{label}</span>
                </button>
              ))}
            </div>

            <ErrorBoundary>
              <DataUploadPanel onApply={applyCustomData} onReset={resetToDemo} simPaused={simPaused} setSimPaused={setSimPaused} hasCustomData={!!customGates} />
            </ErrorBoundary>
          </div>

          <div className="xl:col-span-2 space-y-4">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <h2 className="f-display text-2xl text-white tracking-wide flex items-center gap-2">
                <Sparkles size={17} color={P.green} /> FAN CONCIERGE
              </h2>
              <div className="flex items-center gap-2">
                <button onClick={() => setSosOpen(true)} title="Report an emergency"
                  className="press flex items-center gap-1.5 f-body text-[11px] font-semibold rounded-lg px-2.5 py-1.5 border"
                  style={{ background: P.redSoft, borderColor: P.red, color: P.red, boxShadow: glow(P.red, 8) }}>
                  <Siren size={13} /> SOS
                </button>
                <div className="flex items-center gap-2 rounded-lg px-2 py-1.5 border" style={glass(P.panelBorder)}>
                  <Languages size={14} color={P.muted} />
                  <label htmlFor="lang-select" className="sr-only">Language</label>
                  <select id="lang-select" value={lang} onChange={(e) => setLang(e.target.value)} className="bg-transparent text-xs f-body text-white outline-none">
                    {LANGUAGES.map((l) => <option key={l} className="bg-[#0f1830]" value={l}>{l}</option>)}
                  </select>
                </div>
              </div>
            </div>
            <ErrorBoundary>
              <div style={{ height: 480 }}>
                <CopilotChat
                  title="Ask anything — wayfinding, food, transit, accessibility"
                  accent={P.green}
                  systemPrompt={sysPrompt}
                  placeholder="e.g. Shortest line near an accessible restroom?"
                  suggestions={["Which gate has the shortest wait right now?", "I use a wheelchair — what's the best route in?", "How do I get home fastest after the match?"]}
                  externalInput={quickQuery}
                  langCode={langCode}
                />
              </div>
            </ErrorBoundary>
            <div className="rounded-xl border p-3 flex items-start gap-2 lift-hover" style={glass(P.panelBorder)}>
              <Bus size={14} color={P.blue} className="mt-0.5 shrink-0" />
              <p className="f-body text-[11px] text-[#8B98BE]">
                {TRANSIT[0].name}: <span className="text-white">{TRANSIT[0].eta}</span> · {TRANSIT[1].name}: <span className="text-white">{TRANSIT[1].eta}</span>
              </p>
            </div>
          </div>
        </div>

        <p className="f-body text-[10px] text-center" style={{ color: P.mutedDark }}>
          Single-persona build: Fan Navigation &amp; Accessibility · deterministic, auditable scoring narrated by GenAI · human-reviewable, never autonomous for safety actions.
        </p>
      </main>

      <SOSPanel open={sosOpen} onClose={() => setSosOpen(false)} onReport={handleSOS} />
      <ToastStack toasts={toasts} dismiss={dismiss} />
    </div>
  );
}
