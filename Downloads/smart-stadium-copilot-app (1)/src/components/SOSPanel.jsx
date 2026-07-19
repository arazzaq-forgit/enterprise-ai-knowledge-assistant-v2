import React, { memo, useState, useEffect } from "react";
import { Siren, CheckCircle2 } from "lucide-react";
import { P, glow } from "../theme.js";
import { SOS_REASONS } from "../data/venues.js";

function SOSPanel({ open, onClose, onReport }) {
  const [reported, setReported] = useState(false);
  useEffect(() => { if (open) setReported(false); }, [open]);
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/65 backdrop-blur-sm" onClick={onClose} role="dialog" aria-modal="true" aria-label="Emergency assistance">
      <div onClick={(e) => e.stopPropagation()} className="fade-up w-full max-w-sm rounded-2xl border p-5"
        style={{ background: P.panel, borderColor: P.red, boxShadow: glow(P.red, 26) }}>
        {!reported ? (
          <>
            <div className="flex items-center gap-2 mb-3">
              <Siren size={20} color={P.red} className="pulse-dot" />
              <h3 className="f-body text-base font-semibold text-white">Need help right now?</h3>
            </div>
            <p className="f-body text-xs text-[#8B98BE] mb-4">This instantly alerts stadium staff with your nearest gate — no need to wait on the chat.</p>
            <div className="space-y-2 stagger">
              {SOS_REASONS.map((r) => (
                <button key={r} onClick={() => { setReported(true); onReport(r); }}
                  className="press w-full text-left f-body text-sm rounded-lg px-3 py-2.5 border hover:bg-white/5 text-[#dbe4f5] transition-colors"
                  style={{ background: P.panel2, borderColor: P.panelBorder }}>
                  {r}
                </button>
              ))}
            </div>
            <button onClick={onClose} className="w-full mt-3 f-body text-xs text-[#54608A] hover:text-white transition-colors">Cancel</button>
          </>
        ) : (
          <div className="text-center py-3 fade-up">
            <CheckCircle2 size={32} color={P.green} className="mx-auto mb-2" style={{ filter: `drop-shadow(0 0 8px ${P.green}88)` }} />
            <p className="f-body text-sm font-semibold text-white mb-1">Staff have been notified</p>
            <p className="f-body text-xs text-[#8B98BE] mb-4">Stay where you are if possible. The nearest medical point is roughly 2 minutes away, and a team member is on the way.</p>
            <button onClick={onClose} className="press f-body text-xs font-semibold rounded-lg px-4 py-2" style={{ background: P.green, color: "#06170D" }}>Done</button>
          </div>
        )}
      </div>
    </div>
  );
}

const MemoizedSOSPanel = memo(SOSPanel);
export default MemoizedSOSPanel;
export { MemoizedSOSPanel as SOSPanel };
