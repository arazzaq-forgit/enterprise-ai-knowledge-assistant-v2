import { Upload, Search, MessageSquare, Shield, Zap, FileText } from "lucide-react";

const features = [
  {
    icon: Upload,
    title: "Upload anything",
    desc: "PDF, DOCX, TXT, Markdown, CSV — drag and drop your files and they're indexed in seconds.",
    color: "#6366F1",
  },
  {
    icon: Search,
    title: "Semantic search",
    desc: "Not keyword matching — actual meaning-based retrieval using vector embeddings.",
    color: "#06B6D4",
  },
  {
    icon: MessageSquare,
    title: "Streaming answers",
    desc: "Get word-by-word responses just like ChatGPT, with cited sources for every answer.",
    color: "#8B5CF6",
  },
  {
    icon: Shield,
    title: "100% private",
    desc: "Everything runs locally via Ollama. Your documents never leave your machine.",
    color: "#10B981",
  },
  {
    icon: Zap,
    title: "Multi-document",
    desc: "Load multiple documents at once and ask questions that span across all of them.",
    color: "#F59E0B",
  },
  {
    icon: FileText,
    title: "Auto summarize",
    desc: "One click to get a structured summary of any loaded document with key insights.",
    color: "#EF4444",
  },
];

export default function Features() {
  return (
    <section id="features" className="py-32 px-6">
      <div className="max-w-6xl mx-auto">

        {/* Header */}
        <div className="text-center mb-20">
          <p className="text-indigo-400 font-semibold text-sm uppercase tracking-widest mb-4">
            What it does
          </p>
          <h2 className="font-display text-5xl md:text-6xl font-bold text-white">
            Everything you need to<br />
            <span className="gradient-text">understand your docs</span>
          </h2>
          <p className="mt-6 text-slate-400 text-lg max-w-xl mx-auto">
            A complete RAG system built with LangChain, ChromaDB, and Ollama
            — no subscriptions, no API keys, no limits.
          </p>
        </div>

        {/* Feature grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((f) => (
            <div
              key={f.title}
              className="glass rounded-2xl p-6 hover:bg-white/[0.07] transition-all duration-300 group cursor-default"
            >
              <div
                className="w-12 h-12 rounded-xl flex items-center justify-center mb-5 transition-transform duration-300 group-hover:scale-110"
                style={{ background: `${f.color}22`, border: `1px solid ${f.color}44` }}
              >
                <f.icon className="w-6 h-6" style={{ color: f.color }} />
              </div>
              <h3 className="text-white font-semibold text-lg mb-2">{f.title}</h3>
              <p className="text-slate-400 text-sm leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}