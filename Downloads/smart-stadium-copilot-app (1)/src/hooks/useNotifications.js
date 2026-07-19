import { useState, useEffect, useCallback } from "react";

export function useNotifications(gates) {
  const [toasts, setToasts] = useState([]);
  const [log, setLog] = useState([]);

  const push = useCallback((text, severity = "Low") => {
    const id = Math.random().toString(36).slice(2);
    const entry = { id, text, severity, ts: new Date() };
    setToasts((t) => [...t, entry]);
    setLog((l) => [entry, ...l].slice(0, 30));
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 6000);
  }, []);
  const dismiss = useCallback((id) => setToasts((t) => t.filter((x) => x.id !== id)), []);

  useEffect(() => {
    const templates = [
      () => {
        const busiest = [...gates].sort((a, b) => b.occ - a.occ)[0];
        return busiest.occ >= 80
          ? [`${busiest.name} approaching critical density (${busiest.occ}%) — consider another gate`, "High"]
          : [`${busiest.name} trending upward — worth checking before you head over`, "Medium"];
      },
      () => ["Metro Line 2 running 2 minutes behind schedule", "Low"],
      () => ["Weather holding clear through the final whistle", "Low"],
    ];
    const t = setInterval(() => {
      const [text, sev] = templates[Math.floor(Math.random() * templates.length)]();
      push(text, sev);
    }, 18000);
    return () => clearInterval(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [gates]);

  return { toasts, log, push, dismiss };
}
