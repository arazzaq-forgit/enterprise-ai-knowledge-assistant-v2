import { Link } from "react-router-dom";
import { FileText } from "lucide-react";

export default function Navbar() {
  return (
    <nav className="sticky top-0 z-50 backdrop-blur-xl border-b border-white/10 bg-black/40">
      <div className="max-w-7xl mx-auto px-8 h-20 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-3 text-2xl font-bold">
          <FileText className="w-8 h-8 text-cyan-400" />
          <span>DocMind AI</span>
        </Link>

        <div className="hidden md:flex gap-10 text-gray-300">
          <a href="#features" className="hover:text-white transition">
            Features
          </a>
          <a href="#about" className="hover:text-white transition">
            About
          </a>
          <a href="#contact" className="hover:text-white transition">
            Contact
          </a>
        </div>

        <div className="flex items-center gap-4">
          <button className="px-5 py-2 rounded-xl border border-white/20 hover:bg-white/10 transition">
            Login
          </button>

          <Link
            to="/workspace"
            className="px-5 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 transition font-semibold text-black"
          >
            Launch App
          </Link>
        </div>
      </div>
    </nav>
  );
}