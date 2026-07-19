import { useState, useEffect, useRef } from "react";

/**
 * Drives live-feeling gate occupancy. Resets whenever `initialGates`
 * changes identity (i.e. venue switch or new custom dataset applied).
 * When `paused` is true, no drift is applied — used so judge-uploaded
 * data stays exactly what was uploaded unless simulation is explicitly
 * re-enabled.
 */
export function useLiveGates(initialGates, paused) {
  const [gates, setGates] = useState(initialGates);
  const [history, setHistory] = useState(() => {
    const point = { t: 0 };
    initialGates.forEach((g) => { point[g.id] = g.occ; });
    return [point];
  });
  const tick = useRef(0);

  useEffect(() => {
    tick.current = 0;
    setGates(initialGates);
    const point = { t: 0 };
    initialGates.forEach((g) => { point[g.id] = g.occ; });
    setHistory([point]);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialGates]);

  useEffect(() => {
    if (paused) return undefined;
    const t = setInterval(() => {
      setGates((prev) => {
        const next = prev.map((g) => {
          const drift = Math.round((Math.random() - 0.45) * 6);
          const occ = Math.min(99, Math.max(8, g.occ + drift));
          const wait = Math.max(0, Math.round(occ / 5.2 - 4 + Math.random() * 2));
          return { ...g, occ, wait };
        });
        tick.current += 1;
        setHistory((h) => {
          const point = { t: tick.current };
          next.forEach((g) => { point[g.id] = g.occ; });
          const arr = [...h, point];
          return arr.length > 16 ? arr.slice(arr.length - 16) : arr;
        });
        return next;
      });
    }, 3200);
    return () => clearInterval(t);
  }, [paused]);

  return { gates, history };
}
