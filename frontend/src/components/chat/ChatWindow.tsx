import { useState, useRef, useEffect } from "react"
import { Send, PanelLeftOpen, FileText, Sparkles } from "lucide-react"
import Message from "./Message"
import { streamChat } from "@/services/api"

interface ChatMessage {
  role: "user" | "assistant"
  content: string
}

interface ChatWindowProps {
  docs: string[]
  onSidebarToggle: () => void
  sidebarOpen: boolean
}

const WELCOME: ChatMessage = {
  role: "assistant",
  content: "Hi! I am your AI document assistant. Upload documents in the sidebar and ask me anything about them. I will give you accurate answers with source citations.",
}

export default function ChatWindow({ docs, onSidebarToggle, sidebarOpen }: ChatWindowProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([WELCOME])
  const [input, setInput] = useState("")
  const [isStreaming, setIsStreaming] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const getHistory = (msgs: ChatMessage[]) => {
    const pairs: { question: string; answer: string }[] = []
    for (let i = 1; i < msgs.length - 1; i += 2) {
      if (msgs[i].role === "user" && msgs[i + 1]?.role === "assistant") {
        pairs.push({ question: msgs[i].content, answer: msgs[i + 1].content })
      }
    }
    return pairs
  }

  const sendMessage = async () => {
    const question = input.trim()
    if (!question || isStreaming) return
    setInput("")
    const userMsg: ChatMessage = { role: "user", content: question }
    const assistantMsg: ChatMessage = { role: "assistant", content: "" }
    setMessages((prev) => [...prev, userMsg, assistantMsg])
    setIsStreaming(true)

    streamChat(
      question,
      getHistory([...messages, userMsg]),
      (token) => {
        setMessages((prev) => {
          const updated = [...prev]
          updated[updated.length - 1] = {
            role: "assistant",
            content: updated[updated.length - 1].content + token,
          }
          return updated
        })
      },
      () => setIsStreaming(false),
      (err) => {
        setMessages((prev) => {
          const updated = [...prev]
          updated[updated.length - 1] = { role: "assistant", content: "Error: " + err }
          return updated
        })
        setIsStreaming(false)
      }
    )
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-3 px-5 py-4 border-b border-white/10 flex-shrink-0"
        style={{ background: "rgba(10,15,30,0.8)", backdropFilter: "blur(12px)" }}>
        {!sidebarOpen && (
          <button onClick={onSidebarToggle} title="Open sidebar"
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-white/10 transition">
            <PanelLeftOpen className="w-5 h-5" />
          </button>
        )}
        <Sparkles className="w-5 h-5 text-indigo-400" />
        <span className="font-semibold text-white">DocMind AI</span>
        <div className="ml-auto">
          {docs.length > 0 ? (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs border border-green-500/20 text-green-400"
              style={{ background: "rgba(255,255,255,0.04)" }}>
              <div className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
              {docs.length} doc{docs.length > 1 ? "s" : ""} loaded
            </div>
          ) : (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs text-slate-500 border border-slate-700"
              style={{ background: "rgba(255,255,255,0.04)" }}>
              <FileText className="w-3 h-3" />
              No documents loaded
            </div>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-5">
        {messages.map((msg, i) => (
          <Message key={i} role={msg.role} content={msg.content}
            isStreaming={isStreaming && i === messages.length - 1 && msg.role === "assistant"} />
        ))}
        <div ref={bottomRef} />
      </div>

      <div className="px-6 py-4 border-t border-white/10 flex-shrink-0"
        style={{ background: "rgba(10,15,30,0.8)", backdropFilter: "blur(12px)" }}>
        <div className="flex items-end gap-3 rounded-2xl px-4 py-3 border border-white/10 focus-within:border-indigo-500/50 transition-colors"
          style={{ background: "rgba(255,255,255,0.05)" }}>
          <textarea value={input} onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={docs.length === 0 ? "Upload a document first..." : "Ask anything about your documents..."}
            rows={1}
            className="flex-1 bg-transparent text-sm text-white placeholder-slate-500 resize-none focus:outline-none max-h-36"
            style={{ lineHeight: "1.6" }} />
          <button onClick={sendMessage} disabled={!input.trim() || isStreaming}
            title="Send message"
            className="p-2.5 rounded-xl flex-shrink-0 transition-all duration-200 hover:scale-105 disabled:opacity-40 disabled:cursor-not-allowed text-white"
            style={{ background: input.trim() && !isStreaming ? "linear-gradient(135deg, #6366F1, #06B6D4)" : "rgba(255,255,255,0.05)" }}>
            <Send className="w-4 h-4" />
          </button>
        </div>
        <p className="text-center text-xs text-slate-600 mt-2">Press Enter to send · Shift+Enter for new line</p>
      </div>
    </div>
  )
}
