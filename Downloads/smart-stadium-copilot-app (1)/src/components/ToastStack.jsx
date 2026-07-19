import React from "react";
import { X } from "lucide-react";
import { P, sevColor, glass, glow } from "../theme.js";

export function ToastStack({ toasts, dismiss }) {
  return (
    <div className="fixed top-20 right-5 z-50 flex flex-col gap-2 w-80" aria-live="polite" aria-label="Live alerts">
      {toasts.map((t) => (
        <div key={t.id} className="toast-in f-body rounded-xl border px-3.5 py-3 shadow-lg flex items-start gap-2.5"
          style={{ ...glass(P.panelBorder), boxShadow: glow(sevColor(t.severity), 14) }}>
          <div className="mt-0.5 w-2 h-2 rounded-full shrink-0 pulse-dot" style={{ background: sevColor(t.severity) }} />
          <div className="flex-1">
            <p className="text-[10px] font-semibold tracking-wide" style={{ color: sevColor(t.severity) }}>{t.severity.toUpperCase()}</p>
            <p className="text-xs text-[#dbe4f5] mt-0.5 leading-snug">{t.text}</p>
          </div>
          <button onClick={() => dismiss(t.id)} aria-label="Dismiss alert" className="text-[#54608A] hover:text-white transition-colors">
            <X size={14} />
          </button>
        </div>
      ))}
    </div>
  );
}
