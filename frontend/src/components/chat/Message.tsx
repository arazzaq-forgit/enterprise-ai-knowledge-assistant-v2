import { Bot, User, Copy, Check, ShieldCheck, ShieldAlert, ShieldX } from "lucide-react"
import { useState } from "react"

interface ConfidenceData {
  score: number
  label: string
  percentage: string
  color: string
  explanation?: string
}

interface HallucinationData {
  risk_level: string
  risk_score: number
  color: string
  explanation?: string
  is_grounded: boolean
}

interface MessageProps {
  role: "user" | "assistant"
  content: string
  isStreaming?: boolean
  confidence?: ConfidenceData
  hallucination?: HallucinationData
}

export default function Message({ role, content, isStreaming, confidence, hallucination }: MessageProps) {
  const [copied, setCopied] = useState(false)
  const [showDetails, setShowDetails] = useState(false)
  const isUser = role === "user"

  const copyToClipboard = () => {
    navigator.clipboard.writeText(content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const ConfidenceBadge = () => {
    if (!confidence || isUser || isStreaming) return null
    const { score, label, color, percentage, explanation } = confidence

    const Icon = score >= 75 ? ShieldCheck : score >= 50 ? ShieldAlert : ShieldX

    return (
      <div className="mt-3 pt-3 border-t border-white/10">
        <div className="flex items-center gap-2 flex-wrap">
          <div
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium cursor-pointer hover:opacity-80 transition"
            style={{ background: `${color}20`, border: `1px solid ${color}40`, color }}
            onClick={() => setShowDetails(!showDetails)}
            title="Click for details"
          >
            <Icon className="w-3 h-3" />
            <span>Confidence: {percentage} ({label})</span>
          </div>

          {hallucination && (
            <div
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium"
              style={{
                background: `${hallucination.color}20`,
                border: `1px solid ${hallucination.color}40`,
                color: hallucination.color
              }}
            >
              {hallucination.risk_level === "LOW"
                ? <ShieldCheck className="w-3 h-3" />
                : <ShieldAlert className="w-3 h-3" />
              }
              <span>Grounding: {hallucination.risk_level} risk</span>
            </div>
          )}
        </div>

        {showDetails && (
          <div className="mt-2 text-xs text-slate-400 space-y-1">
            {explanation && <p>{explanation}</p>}
            {hallucination?.explanation && (
              <p className="text-slate-500">{hallucination.explanation}</p>
            )}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className={`flex gap-3 group ${isUser ? "flex-row-reverse" : "flex-row"}`}>

      <div className={`
        w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 mt-1
        ${isUser
          ? "bg-indigo-500/20 border border-indigo-500/30"
          : "bg-cyan-500/10 border border-cyan-500/20"
        }
      `}>
        {isUser
          ? <User className="w-4 h-4 text-indigo-400" />
          : <Bot className="w-4 h-4 text-cyan-400" />
        }
      </div>

      <div
        className={`relative max-w-[75%] px-4 py-3 rounded-2xl text-sm leading-relaxed
          ${isUser ? "rounded-tr-sm text-white" : "rounded-tl-sm text-slate-200"}
        `}
        style={isUser
          ? { background: "linear-gradient(135deg, rgba(99,102,241,0.3), rgba(99,102,241,0.15))", border: "1px solid rgba(99,102,241,0.25)" }
          : { background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)" }
        }
      >
        <p className="whitespace-pre-wrap">{content}</p>

        {isStreaming && (
          <span className="inline-block w-2 h-4 ml-1 bg-cyan-400 animate-pulse rounded-sm align-middle" />
        )}

        <ConfidenceBadge />

        {!isUser && !isStreaming && content && (
          <button
            onClick={copyToClipboard}
            className="absolute -top-2 -right-2 opacity-0 group-hover:opacity-100 p-1.5 rounded-lg glass border border-white/10 text-slate-400 hover:text-white transition-all"
            title="Copy"
          >
            {copied
              ? <Check className="w-3 h-3 text-green-400" />
              : <Copy className="w-3 h-3" />
            }
          </button>
        )}
      </div>
    </div>
  )
}