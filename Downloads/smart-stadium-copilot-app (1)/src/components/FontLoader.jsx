import React from "react";

export function FontLoader() {
  return (
    <style>{`
      @import url('https://fonts.googleapis.com/css2?family=Teko:wght@500;600;700&family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap');
      .f-display { font-family: 'Teko', sans-serif; letter-spacing: 0.02em; }
      .f-body { font-family: 'Inter', sans-serif; }
      .f-mono { font-family: 'JetBrains Mono', monospace; }

      /* live ticker */
      @keyframes ticker { 0% { transform: translateX(0%); } 100% { transform: translateX(-50%); } }
      .ticker-track { animation: ticker 34s linear infinite; }

      /* pulsing status dots */
      @keyframes pulseDot { 0%,100% { opacity: 1; } 50% { opacity: 0.3; } }
      .pulse-dot { animation: pulseDot 1.6s ease-in-out infinite; }

      /* critical gate ring */
      @keyframes ringPulse { 0% { box-shadow: 0 0 0 0 rgba(239,68,68,0.55); } 100% { box-shadow: 0 0 0 14px rgba(239,68,68,0); } }
      .ring-pulse { animation: ringPulse 1.8s ease-out infinite; }

      /* toast entrance — slide only, never opacity-dependent */
      @keyframes slideIn { from { transform: translateX(60px); } to { transform: translateX(0); } }
      .toast-in { animation: slideIn 0.35s cubic-bezier(0.22,1,0.36,1); }

      /* card/content entrance — subtle slide only. Deliberately NOT an
         opacity fade: if this animation is ever interrupted, skipped, or
         throttled (e.g. by battery saver), content must stay fully
         visible the entire time rather than getting stuck transparent. */
      @keyframes fadeUp { from { transform: translateY(8px); } to { transform: translateY(0); } }
      .fade-up { animation: fadeUp 0.4s cubic-bezier(0.22,1,0.36,1) both; }

      /* staggered entrance for grids/lists — same non-opacity approach */
      .stagger > * { animation: fadeUp 0.45s cubic-bezier(0.22,1,0.36,1) both; }
      .stagger > *:nth-child(1) { animation-delay: 0.03s; }
      .stagger > *:nth-child(2) { animation-delay: 0.09s; }
      .stagger > *:nth-child(3) { animation-delay: 0.15s; }
      .stagger > *:nth-child(4) { animation-delay: 0.21s; }
      .stagger > *:nth-child(5) { animation-delay: 0.27s; }
      .stagger > *:nth-child(6) { animation-delay: 0.33s; }

      /* mic recording state */
      @keyframes micPulse { 0%,100% { box-shadow: 0 0 0 0 rgba(239,68,68,0.5); } 50% { box-shadow: 0 0 0 8px rgba(239,68,68,0); } }
      .mic-live { animation: micPulse 1.2s ease-in-out infinite; }

      /* score bars filling in */
      @keyframes growBar { from { width: 0%; } }
      .grow-bar { animation: growBar 0.9s cubic-bezier(0.22,1,0.36,1) both; }

      /* soft ambient glow breathing behind hero elements */
      @keyframes breatheGlow { 0%,100% { opacity: 0.55; transform: scale(1); } 50% { opacity: 0.9; transform: scale(1.04); } }
      .breathe-glow { animation: breatheGlow 4.5s ease-in-out infinite; }

      /* floodlight sweep across the header */
      @keyframes sweep { 0% { transform: translateX(-30%); } 100% { transform: translateX(130%); } }
      .sweep { animation: sweep 8s linear infinite; }

      /* crowd dots near busy gates */
      @keyframes crowdDrift { 0%,100% { transform: translate(0,0); opacity: 0.5; } 50% { transform: translate(2px,-2px); opacity: 1; } }
      .crowd-dot { animation: crowdDrift 2.4s ease-in-out infinite; }

      /* card hover lift */
      .lift-hover { transition: transform 0.25s cubic-bezier(0.22,1,0.36,1), box-shadow 0.25s ease, border-color 0.25s ease; }
      .lift-hover:hover { transform: translateY(-2px); }

      /* button press feedback */
      .press { transition: transform 0.15s ease, filter 0.15s ease, box-shadow 0.15s ease; }
      .press:active { transform: scale(0.97); }
      .press:hover { filter: brightness(1.08); }

      /* number count-up flicker for live stats */
      @keyframes numberIn { from { transform: translateY(3px); } to { transform: translateY(0); } }
      .number-in { animation: numberIn 0.3s ease-out; }

      /* shimmer for skeleton/loading */
      @keyframes shimmer { 0% { background-position: -200% 0; } 100% { background-position: 200% 0; } }
      .shimmer { background: linear-gradient(90deg, #111B33 25%, #182449 37%, #111B33 63%); background-size: 400% 100%; animation: shimmer 1.6s ease-in-out infinite; }

      *:focus-visible { outline: 2px solid #4EA8F5; outline-offset: 2px; border-radius: 4px; }
      ::-webkit-scrollbar { width: 6px; height: 6px; }
      ::-webkit-scrollbar-thumb { background: #24304d; border-radius: 4px; }
      ::selection { background: rgba(31,191,107,0.35); }

      @media (prefers-reduced-motion: reduce) {
        .fade-up, .stagger > *, .toast-in, .number-in { animation: none !important; transform: none !important; }
      }
    `}</style>
  );
}
