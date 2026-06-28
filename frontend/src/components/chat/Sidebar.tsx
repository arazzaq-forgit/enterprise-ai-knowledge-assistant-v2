import { useState } from "react"
import { X, ChevronLeft, ChevronRight, Trash2, FileText, Globe } from "lucide-react"
import UploadZone from "@/components/upload/UploadZone"
import { uploadURL, clearDocuments } from "@/services/api"

interface SidebarProps {
  docs: string[]
  onDocsChange: (docs: string[]) => void
  isOpen: boolean
  onToggle: () => void
}

export default function Sidebar({ docs, onDocsChange, isOpen, onToggle }: SidebarProps) {
  const [urlInput, setUrlInput] = useState("")
  const [showUrlInput, setShowUrlInput] = useState(false)
  const [urlLoading, setUrlLoading] = useState(false)

  const removeDoc = (name: string) => {
    onDocsChange(docs.filter((d) => d !== name))
  }

  const addUrl = async () => {
    const url = urlInput.trim()
    if (!url || docs.includes(url)) return
    setUrlLoading(true)
    try {
      const result = await uploadURL(url)
      if (result.success) {
        onDocsChange([...docs, url])
        setUrlInput("")
        setShowUrlInput(false)
      }
    } catch (err) {
      console.error("URL upload failed", err)
    } finally {
      setUrlLoading(false)
    }
  }

  const handleClearAll = async () => {
    try {
      await clearDocuments()
      onDocsChange([])
    } catch (err) {
      console.error("Clear failed", err)
    }
  }

  return (
    <>
      <aside
        className="relative flex flex-col h-full border-r border-white/10 transition-all duration-300 ease-in-out flex-shrink-0"
        style={{ background: "rgba(10,14,28,0.97)", width: isOpen ? "288px" : "0px", overflow: "hidden" }}>
        {isOpen && (
          <div className="flex flex-col h-full w-72">

            <div className="flex items-center justify-between px-5 py-4 border-b border-white/10">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-lg flex items-center justify-center"
                  style={{ background: "rgba(99,102,241,0.2)" }}>
                  <FileText className="w-4 h-4 text-indigo-400" />
                </div>
                <span className="font-semibold text-white text-sm">Documents</span>
              </div>
              <button onClick={onToggle} title="Close sidebar"
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition">
                <ChevronLeft className="w-4 h-4" />
              </button>
            </div>

            <div className="p-4 border-b border-white/10">
              <UploadZone onUpload={(name) => {
                if (!docs.includes(name)) onDocsChange([...docs, name])
              }} />
            </div>

            <div className="px-4 py-3 border-b border-white/10">
              {showUrlInput ? (
                <div className="flex gap-2">
                  <input type="url" value={urlInput}
                    onChange={(e) => setUrlInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && addUrl()}
                    placeholder="https://example.com"
                    className="flex-1 text-xs px-3 py-2 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 border border-white/10"
                    style={{ background: "rgba(255,255,255,0.05)" }} />
                  <button onClick={addUrl} disabled={urlLoading}
                    className="px-3 py-2 rounded-lg text-xs font-medium text-white transition disabled:opacity-50"
                    style={{ background: "rgba(99,102,241,0.8)" }}>
                    {urlLoading ? "..." : "Add"}
                  </button>
                  <button onClick={() => setShowUrlInput(false)} title="Cancel"
                    className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition">
                    <X className="w-3 h-3" />
                  </button>
                </div>
              ) : (
                <button onClick={() => setShowUrlInput(true)}
                  className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-xs text-slate-400 hover:text-white hover:bg-white/10 transition border border-dashed border-white/10">
                  <Globe className="w-3.5 h-3.5" />
                  Add URL source
                </button>
              )}
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-2">
              {docs.length === 0 ? (
                <div className="text-center py-8 text-slate-600 text-xs">
                  <FileText className="w-8 h-8 mx-auto mb-3 opacity-30" />
                  <p>No documents loaded yet</p>
                  <p className="mt-1 text-slate-700">Upload a file above to get started</p>
                </div>
              ) : (
                docs.map((doc) => (
                  <div key={doc}
                    className="group flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-white/10 transition border border-white/5">
                    <div className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0"
                      style={{ background: "rgba(99,102,241,0.15)" }}>
                      {doc.startsWith("http") ? (
                        <Globe className="w-3.5 h-3.5 text-cyan-400" />
                      ) : (
                        <FileText className="w-3.5 h-3.5 text-indigo-400" />
                      )}
                    </div>
                    <span className="flex-1 text-xs text-slate-300 truncate">{doc}</span>
                    <button onClick={() => removeDoc(doc)} title="Remove document"
                      className="opacity-0 group-hover:opacity-100 p-1 rounded text-slate-500 hover:text-red-400 transition">
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                ))
              )}
            </div>

            <div className="px-4 py-3 border-t border-white/10">
              <div className="flex items-center justify-between text-xs text-slate-500">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full" style={{ background: docs.length > 0 ? "#10B981" : "#475569" }} />
                  <span>{docs.length} document{docs.length !== 1 ? "s" : ""} loaded</span>
                </div>
                {docs.length > 0 && (
                  <button onClick={handleClearAll}
                    className="text-red-400/70 hover:text-red-400 transition flex items-center gap-1">
                    <Trash2 className="w-3 h-3" />
                    Clear all
                  </button>
                )}
              </div>
            </div>

          </div>
        )}
      </aside>

      {!isOpen && (
        <button onClick={onToggle} title="Open sidebar"
          className="absolute left-0 top-1/2 -translate-y-1/2 z-10 p-2 rounded-r-xl border border-white/10 text-slate-400 hover:text-white transition"
          style={{ background: "rgba(10,14,28,0.9)" }}>
          <ChevronRight className="w-4 h-4" />
        </button>
      )}
    </>
  )
}
