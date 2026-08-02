import axios from "axios"

// Reads VITE_API_URL from .env / .env.local (see frontend/.env.example).
// Falls back to production only if no env var is set — this way local
// dev naturally talks to your local backend instead of silently hitting
// the live Render deployment.
const BASE_URL = import.meta.env.VITE_API_URL || "https://enterprise-ai-knowledge-assistant-v2.onrender.com"

const API = axios.create({ baseURL: BASE_URL })

export const uploadFile = async (file: File) => {
  const form = new FormData()
  form.append("file", file)
  const res = await API.post("/api/upload", form)
  return res.data
}

export const uploadURL = async (url: string) => {
  const res = await API.post("/api/upload/url", { url })
  return res.data
}

export const getDocuments = async () => {
  const res = await API.get("/api/documents")
  return res.data
}

export const clearDocuments = async () => {
  const res = await API.delete("/api/documents")
  return res.data
}

export const deleteDocument = async (filename: string) => {
  const res = await API.delete(`/api/documents/${encodeURIComponent(filename)}`)
  return res.data
}

// NOTE: the old chatWithEvaluation() (POST /api/chat/evaluate) was removed
// from here. Confidence + hallucination scores now arrive as a final
// "eval" event on the streamChat() SSE stream below — no second request.

export interface EvalPayload {
  sources: unknown[]
  confidence: {
    score: number
    label: string
    percentage: string
    color: string
    explanation?: string
  }
  hallucination_check: {
    risk_level: string
    risk_score: number
    color: string
    explanation?: string
    is_grounded: boolean
  }
}

export const streamChat = (
  question: string,
  chatHistory: { question: string; answer: string }[],
  onToken: (token: string) => void,
  onDone: () => void,
  onError: (err: string) => void,
  onEval?: (evalData: EvalPayload) => void
) => {
  fetch(`${BASE_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, chat_history: chatHistory, stream: true }),
  }).then(async (res) => {
    const reader = res.body?.getReader()
    const decoder = new TextDecoder()
    if (!reader) return onError("No response stream")
    let buffer = ""
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split("\n\n")
      buffer = lines.pop() ?? ""
      for (const line of lines) {
        if (!line.startsWith("data: ")) continue
        try {
          const json = JSON.parse(line.replace("data: ", ""))
          if (json.token) onToken(json.token)
          if (json.eval && onEval) {
            onEval({
              sources: json.sources,
              confidence: json.confidence,
              hallucination_check: json.hallucination_check,
            })
          }
          if (json.done) onDone()
          if (json.error) onError(json.error)
        } catch {}
      }
    }
  }).catch((err) => onError(err.message))
}