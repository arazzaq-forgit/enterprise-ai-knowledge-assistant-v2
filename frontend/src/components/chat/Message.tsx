import { Bot, User, Copy, Check } from "lucide-react";
import { useState } from "react";

interface MessageProps {
  role: "user" | "assistant";
  content: string;
  isStreaming?: boolean;
}

export default function Message({ role, content, isStreaming }: MessageProps) {
  const [copied, setCopied] = useState(false);

  const copyToClipboard = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const isUser = role === "user";

  return (
    <div className={`flex gap-3 group ${isUser ? "flex-row-reverse" : "flex-row"}`}>

      {/* Avatar */}
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

      {/* Bubble */}
      <div className={`
        relative max-w-[75%] px-4 py-3 rounded-2xl text-sm leading-relaxed
        ${isUser
          ? "rounded-tr-sm text-white"
          : "rounded-tl-sm text-slate-200"
        }
      `}
        style={isUser
          ? { background: "linear-gradient(135deg, rgba(99,102,241,0.3), rgba(99,102,241,0.15))", border: "1px solid rgba(99,102,241,0.25)" }
          : { background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)" }
        }
      >
        {/* Message text */}
        <p className="whitespace-pre-wrap">{content}</p>

        {/* Streaming cursor */}
        {isStreaming && (
          <span className="inline-block w-2 h-4 ml-1 bg-cyan-400 animate-pulse rounded-sm align-middle" />
        )}

        {/* Copy button — only for AI messages */}
        {!isUser && !isStreaming && content && (
          <button
            onClick={copyToClipboard}
            className="absolute -top-2 -right-2 opacity-0 group-hover:opacity-100 p-1.5 rounded-lg glass border border-white/10 text-slate-400 hover:text-white transition-all"
          >
            {copied
              ? <Check className="w-3 h-3 text-green-400" />
              : <Copy className="w-3 h-3" />
            }
          </button>
        )}
      </div>
    </div>
  );
}