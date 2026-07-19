import React, { useState, useEffect, useRef, useCallback } from "react";
import { Sparkles, Loader2, Mic, MicOff, Volume2, Send } from "lucide-react";
import { P, glass, glow } from "../theme.js";
import { askCopilot } from "../lib/askCopilot.js";
import { useVoiceInput, speak } from "../hooks/useVoice.js";

export function CopilotChat({ title, accent, systemPrompt, placeholder, suggestions, externalInput, langCode = "en-US" }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const endRef = useRef(null);

  const send = useCallback(async (text) => {
    const t = text ?? input;
    if (!t.trim() || loading) return;
    setMessages((m) => [...m, { role: "user", text: t }]);
    setInput("");
    setLoading(true);
    const reply = await askCopilot(systemPrompt, t);
    setMessages((m) => [...m, { role: "assistant", text: reply }]);
    setLoading(false);
  }, [input, loading, systemPrompt]);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, loading]);
  // `send` is intentionally omitted: it's a new function reference on every
  // keystroke (useCallback depends on `input`), so including it here would
  // re-fire this effect constantly. We only want to react to a NEW
  // externalInput value (e.g. a quick-action click), not to typing.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { if (externalInput) send(externalInput); }, [externalInput]);

  const { listening, toggle, supported } = useVoiceInput(langCode, (transcript) => setInput(transcript));

  return (
    <div className="flex flex-col rounded-2xl border overflow-hidden h-full" style={{ ...glass(P.panelBorder), boxShadow: glow(accent, 14) }}>
      <div className="flex items-center gap-2 px-4 py-3 border-b" style={{ borderColor: P.panelBorder, background: `linear-gradient(90deg, ${accent}1E, transparent)` }}>
        <Sparkles size={16} color={accent} className="pulse-dot" />
        <span className="f-body text-sm font-semibold text-white">{title}</span>
      </div>
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3" style={{ minHeight: 220, maxHeight: 380 }} role="log" aria-live="polite" aria-label="Conversation">
        {messages.length === 0 && (
          <div className="space-y-2 stagger">
            <p className="f-body text-xs text-[#7d8bab]">Try asking:</p>
            {suggestions.map((s, i) => (
              <button key={i} onClick={() => send(s)}
                className="press block w-full text-left f-body text-xs text-[#c8d3ec] rounded-lg px-3 py-2 transition-colors border hover:bg-white/5"
                style={{ background: P.panel2, borderColor: P.panelBorder }}>
                {s}
              </button>
            ))}
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`fade-up flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`group relative f-body text-[13px] leading-relaxed rounded-xl px-3 py-2 max-w-[85%] whitespace-pre-wrap ${m.role === "user" ? "text-[#06110A]" : "text-[#dbe4f5] border"}`}
              style={m.role === "user" ? { background: accent, boxShadow: glow(accent, 10) } : { background: P.panel2, borderColor: P.panelBorder }}>
              {m.text}
              {m.role === "assistant" && (
                <button onClick={() => speak(m.text, langCode)} title="Read aloud" aria-label="Read this response aloud"
                  className="absolute -right-2 -bottom-2 rounded-full p-1.5 border opacity-0 group-hover:opacity-100 focus-visible:opacity-100 transition-opacity"
                  style={{ background: P.panel, borderColor: P.panelBorder }}>
                  <Volume2 size={11} color={P.muted} />
                </button>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div role="status" className="flex items-center gap-2 text-[#7d8bab] f-body text-xs">
            <Loader2 size={14} className="animate-spin" /> Copilot is thinking…
          </div>
        )}
        <div ref={endRef} />
      </div>
      <div className="flex items-center gap-2 border-t p-2" style={{ borderColor: P.panelBorder }}>
        {supported && (
          <button onClick={toggle} title={listening ? "Stop listening" : "Speak your question"}
            aria-label={listening ? "Stop voice input" : "Start voice input"}
            className={`press rounded-lg p-2 border ${listening ? "mic-live" : ""}`}
            style={{ background: listening ? P.redSoft : P.panel2, borderColor: listening ? P.red : P.panelBorder }}>
            {listening ? <MicOff size={16} color={P.red} /> : <Mic size={16} color={P.muted} />}
          </button>
        )}
        <input value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key === "Enter" && send()}
          placeholder={placeholder} aria-label="Message the concierge"
          className="flex-1 f-body text-sm rounded-lg px-3 py-2 text-white placeholder-[#5c6a8c] outline-none border transition-colors focus:border-[#3a4f82]"
          style={{ background: P.panel2, borderColor: P.panelBorder }} />
        <button onClick={() => send()} disabled={loading} aria-label="Send message"
          className="press rounded-lg p-2 disabled:opacity-40" style={{ background: accent, boxShadow: glow(accent, 10) }}>
          <Send size={16} color="#06110A" />
        </button>
      </div>
    </div>
  );
}
