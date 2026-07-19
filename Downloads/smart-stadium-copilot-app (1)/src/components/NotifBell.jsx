import React, { memo, useState } from "react";
import { Bell } from "lucide-react";
import { P, sevColor, glass, glow } from "../theme.js";

function NotifBell({ log }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        className="press relative p-2 rounded-lg hover:bg-white/5"
        aria-haspopup="true"
        aria-expanded={open}
        aria-label={`Notifications, ${log.length} recent`}
      >
        <Bell size={18} color={P.muted} />
        {log.length > 0 && (
          <span className="absolute -top-0.5 -right-0.5 w-4 h-4 rounded-full flex items-center justify-center f-mono text-[9px] text-white pulse-dot" style={{ background: P.red, boxShadow: glow(P.red, 8) }}>
            {Math.min(log.length, 9)}
          </span>
        )}
      </button>
      {open && (
        <div role="region" aria-label="Live activity log" className="fade-up absolute right-0 mt-2 w-80 max-h-96 overflow-y-auto rounded-xl border shadow-2xl z-40" style={glass(P.panelBorder)}>
          <div className="px-3.5 py-2.5 border-b f-body text-xs font-semibold text-white" style={{ borderColor: P.panelBorder }}>Live Activity</div>
          {log.length === 0 && <p className="p-4 f-body text-xs text-[#8B98BE]">No alerts yet.</p>}
          {log.map((n) => (
            <div key={n.id} className="px-3.5 py-2.5 border-b last:border-0" style={{ borderColor: "#182238" }}>
              <div className="flex items-center gap-1.5 mb-0.5">
                <div className="w-1.5 h-1.5 rounded-full" style={{ background: sevColor(n.severity) }} />
                <span className="f-mono text-[9px]" style={{ color: sevColor(n.severity) }}>{n.severity.toUpperCase()}</span>
                <span className="f-mono text-[9px] text-[#54608A] ml-auto">{n.ts.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
              </div>
              <p className="f-body text-xs text-[#dbe4f5]">{n.text}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

const MemoizedNotifBell = memo(NotifBell);
export default MemoizedNotifBell;
export { MemoizedNotifBell as NotifBell };
