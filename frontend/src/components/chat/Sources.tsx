import { useState } from "react"
import { ChevronDown, FileText } from "lucide-react"
import type { SourceCitation } from "@/services/api"

interface SourcesProps {
  sources: SourceCitation[]
}

// Renders a snippet with its matched sentence highlighted, using the
// character offsets computed server-side. Falls back to plain text if
// `matched` is false or the offsets are out of range for any reason —
// this must never crash the message it's attached to.
function HighlightedSnippet({ source }: { source: SourceCitation }) {
  const { snippet, highlight_start, highlight_end, matched } = source

  const offsetsValid =
    matched &&
    highlight_start >= 0 &&
    highlight_end > highlight_start &&
    highlight_end <= snippet.length

  if (!offsetsValid) {
    return <span className="text-slate-400">{snippet}</span>
  }

  return (
    <span className="text-slate-400">
      {snippet.slice(0, highlight_start)}
      <mark className="bg-indigo-500/25 text-indigo-200 rounded px-0.5">
        {snippet.slice(highlight_start, highlight_end)}
      </mark>
      {snippet.slice(highlight_end)}
    </span>
  )
}

export default function Sources({ sources }: SourcesProps) {
  const [open, setOpen] = useState(false)

  if (!sources || sources.length === 0) return null

  return (
    <div className="mt-3 pt-3 border-t border-white/10">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition"
      >
        <FileText className="w-3.5 h-3.5" />
        {sources.length} source{sources.length > 1 ? "s" : ""}
        <ChevronDown className={`w-3 h-3 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>

      {open && (
        <div className="mt-2 space-y-2">
          {sources.map((s, i) => (
            <div
              key={i}
              className="rounded-lg border border-white/10 px-3 py-2 text-xs leading-relaxed"
              style={{ background: "rgba(255,255,255,0.03)" }}
            >
              <div className="flex items-center justify-between mb-1 text-slate-300">
                <span className="font-medium truncate">{s.source}</span>
                {s.page != null && (
                  <span className="text-slate-500 flex-shrink-0 ml-2">p. {s.page}</span>
                )}
              </div>
              <HighlightedSnippet source={s} />
            </div>
          ))}
        </div>
      )}
    </div>
  )
}