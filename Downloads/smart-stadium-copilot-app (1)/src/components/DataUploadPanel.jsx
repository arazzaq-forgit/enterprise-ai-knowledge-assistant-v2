import React, { memo, useState, useRef } from "react";
import { UploadCloud, Download, RotateCcw, CheckCircle2, AlertTriangle } from "lucide-react";
import { P, GRADIENTS, glass, glow } from "../theme.js";
import { parseGatesJSON, parseGatesCSV, SAMPLE_GATES_JSON, SAMPLE_GATES_CSV } from "../lib/gateData.js";

const MAX_FILE_BYTES = 2 * 1024 * 1024;

function DataUploadPanel({ onApply, onReset, simPaused, setSimPaused, hasCustomData }) {
  const [error, setError] = useState("");
  const [fileName, setFileName] = useState("");
  const fileRef = useRef(null);

  const handleFile = async (file) => {
    setError("");
    setFileName(file.name);
    if (file.size > MAX_FILE_BYTES) {
      setError(`File is too large (${Math.round(file.size / 1024)}KB). Maximum is 2MB.`);
      return;
    }
    try {
      const text = await file.text();
      const isCSV = file.name.toLowerCase().endsWith(".csv");
      const parsed = isCSV ? parseGatesCSV(text) : parseGatesJSON(text);
      onApply(parsed);
    } catch (e) {
      setError(e.message);
    }
  };

  const downloadSample = (type) => {
    const content = type === "csv" ? SAMPLE_GATES_CSV : SAMPLE_GATES_JSON;
    const blob = new Blob([content], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = type === "csv" ? "sample-gates.csv" : "sample-gates.json";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="rounded-2xl border p-4 space-y-3 lift-hover" style={glass(P.panelBorder)}>
      <div className="flex items-center gap-2">
        <UploadCloud size={15} color={P.amber} />
        <h3 className="f-body text-sm font-semibold text-white">Judge / Test Data Panel</h3>
      </div>
      <p className="f-body text-[11px] text-[#8B98BE]">
        Don&apos;t have live stadium data? Upload your own gate dataset (JSON or CSV) and every feature above — the map, the chat, and the explainable recommendation engine — will use it immediately.
      </p>
      <div className="flex flex-wrap items-center gap-2">
        <label className="press f-body text-xs font-semibold rounded-lg px-3.5 py-2 cursor-pointer flex items-center gap-1.5"
          style={{ background: GRADIENTS.amber, color: "#2A1B03", boxShadow: glow(P.amber, 12) }}>
          <UploadCloud size={13} /> Upload dataset
          <input ref={fileRef} type="file" accept=".json,.csv" className="hidden" aria-label="Upload gate dataset"
            onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])} />
        </label>
        <button onClick={() => downloadSample("json")} className="f-body text-[11px] text-[#8B98BE] hover:text-white transition-colors flex items-center gap-1">
          <Download size={12} /> Sample .json
        </button>
        <button onClick={() => downloadSample("csv")} className="f-body text-[11px] text-[#8B98BE] hover:text-white transition-colors flex items-center gap-1">
          <Download size={12} /> Sample .csv
        </button>
        {hasCustomData && (
          <button onClick={onReset} className="f-body text-[11px] text-[#8B98BE] hover:text-white transition-colors flex items-center gap-1 ml-auto">
            <RotateCcw size={12} /> Reset to demo data
          </button>
        )}
      </div>
      {fileName && !error && (
        <p className="fade-up f-body text-[11px] flex items-center gap-1.5" style={{ color: P.green }}><CheckCircle2 size={12} /> Loaded &quot;{fileName}&quot; successfully.</p>
      )}
      {error && (
        <p role="alert" className="fade-up f-body text-[11px] rounded-lg p-2 border flex items-start gap-1.5" style={{ color: P.red, borderColor: P.red, background: P.redSoft }}>
          <AlertTriangle size={13} className="shrink-0 mt-0.5" /> {error}
        </p>
      )}
      <label className="flex items-center gap-2 f-body text-[11px] text-[#8B98BE] cursor-pointer">
        <input type="checkbox" checked={!simPaused} onChange={(e) => setSimPaused(!e.target.checked)} className="w-3.5 h-3.5 accent-[#1FBF6B]" />
        Live simulation drift enabled {hasCustomData && "(auto-disabled for uploaded data unless re-checked)"}
      </label>
      <p className="f-body text-[10px] leading-relaxed" style={{ color: P.mutedDark }}>
        Expected columns: <span className="f-mono">id, name, occ (0-100), wait (minutes), accessible (true/false)</span>. Max file size 2MB, 500 rows.
      </p>
    </div>
  );
}

const MemoizedDataUploadPanel = memo(DataUploadPanel);
export default MemoizedDataUploadPanel;
export { MemoizedDataUploadPanel as DataUploadPanel };
