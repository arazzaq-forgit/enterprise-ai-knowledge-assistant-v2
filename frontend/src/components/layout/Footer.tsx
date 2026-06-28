import { Link } from "react-router-dom";
import { FileText } from "lucide-react";

export default function Footer() {
  return (
    <footer className="border-t border-white/10 py-12 px-6">
      <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
        <Link to="/" className="flex items-center gap-2 text-xl font-bold font-display">
          <FileText className="w-6 h-6 text-indigo-400" />
          DocMind AI
        </Link>
        <p className="text-slate-500 text-sm">
          Built with FastAPI · LangChain · ChromaDB · Ollama · React
        </p>
        <p className="text-slate-600 text-sm">
          © 2026 Mohd Abdul Razzaq
        </p>
      </div>
    </footer>
  );
}