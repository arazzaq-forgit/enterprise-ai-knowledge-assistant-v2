import axios from "axios"

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

export const streamChat = (
  question: string,
  chatHistory: { question: string; answer: string }[],
  onToken: (token: string) => void,
  onDone: () => void,
  onError: (err: string) => void
) => {
  fetch(`${BASE_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, chat_history: chatHistory, stream: true }),
  }).then(async (res) => {
    const reader = res.body?.getReader()
    const decoder = new TextDecoder()
    if (!reader) return onError("No response stream")
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      const text = decoder.decode(value)
      const lines = text.split("\n").filter((l) => l.startsWith("data: "))
      for (const line of lines) {
        try {
          const json = JSON.parse(line.replace("data: ", ""))
          if (json.token) onToken(json.token)
          if (json.done) onDone()
          if (json.error) onError(json.error)
        } catch {}
      }
    }
  }).catch((err) => onError(err.message))
}
