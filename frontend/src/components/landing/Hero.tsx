import { Link } from "react-router-dom"
import { ArrowRight, FileText, Zap, Shield } from "lucide-react"

export default function Hero() {
  const btn = { background: "linear-gradient(135deg, #6366F1, #06B6D4)" }
  return (
    <section className="min-h-screen flex items-center justify-center px-6">
      <div className="text-center max-w-4xl mx-auto">

        <h1 className="text-7xl font-bold leading-tight mb-8">
          Chat with your{" "}
          <span className="gradient-text">documents</span>
          <br />like never before.
        </h1>

        <p className="text-xl text-slate-400 max-w-2xl mx-auto mb-12">
          Upload any document. Ask questions in plain English.
          Get instant cited answers. 100% local AI.
        </p>

        <div className="flex flex-col sm:flex-row gap-4 justify-center mb-10">
          <Link to="/workspace" style={btn}
            className="inline-flex items-center gap-2 px-8 py-4 rounded-2xl font-semibold text-white text-lg hover:opacity-90 transition-all">
            Start chatting free
            <ArrowRight className="w-5 h-5" />
          </Link>
          <a href="#features"
            className="px-8 py-4 rounded-2xl font-semibold text-slate-300 text-lg border border-white/10 hover:bg-white/10 transition-all">
            See how it works
          </a>
        </div>

        <div className="flex flex-wrap justify-center gap-8 text-sm text-slate-500">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-indigo-400" />
            <span>PDF · DOCX · TXT · MD · CSV</span>
          </div>
          <div className="flex items-center gap-2">
            <Zap className="w-4 h-4 text-indigo-400" />
            <span>Streaming responses</span>
          </div>
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-indigo-400" />
            <span>100% local. No API key</span>
          </div>
        </div>

      </div>
    </section>
  )
}
