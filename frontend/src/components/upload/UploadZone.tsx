import { useCallback, useState } from "react"
import { useDropzone } from "react-dropzone"
import { Upload, CheckCircle, Loader2, AlertCircle } from "lucide-react"
import { uploadFile } from "@/services/api"

interface UploadZoneProps {
  onUpload: (filename: string) => void
}

type State = "idle" | "uploading" | "success" | "error"

export default function UploadZone({ onUpload }: UploadZoneProps) {
  const [state, setState] = useState<State>("idle")
  const [message, setMessage] = useState("")

  const onDrop = useCallback(async (files: File[]) => {
    if (!files.length) return
    setState("uploading")
    setMessage("Indexing document...")
    try {
      for (const file of files) {
        const result = await uploadFile(file)
        if (result.success) onUpload(result.filename)
      }
      setState("success")
      setMessage(files.length === 1 ? "Indexed successfully!" : `${files.length} files indexed!`)
      setTimeout(() => { setState("idle"); setMessage("") }, 3000)
    } catch (err: any) {
      setState("error")
      setMessage(err?.response?.data?.detail || "Upload failed")
      setTimeout(() => { setState("idle"); setMessage("") }, 3000)
    }
  }, [onUpload])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
      "text/plain": [".txt"],
      "text/markdown": [".md"],
      "text/csv": [".csv"],
    },
    multiple: true,
    disabled: state === "uploading",
  })

  return (
    <div {...getRootProps()}
      className="cursor-pointer rounded-xl border-2 border-dashed p-4 text-center transition-all duration-200"
      style={{
        borderColor: isDragActive ? "#6366F1" : state === "success" ? "#10B981" : state === "error" ? "#EF4444" : "rgba(255,255,255,0.1)",
        background: isDragActive ? "rgba(99,102,241,0.1)" : "transparent",
      }}>
      <input {...getInputProps()} />
      {state === "uploading" && (
        <div className="flex flex-col items-center gap-2 py-2">
          <Loader2 className="w-6 h-6 text-indigo-400 animate-spin" />
          <p className="text-xs text-slate-400">{message}</p>
        </div>
      )}
      {state === "success" && (
        <div className="flex flex-col items-center gap-2 py-2">
          <CheckCircle className="w-6 h-6 text-green-400" />
          <p className="text-xs text-green-400">{message}</p>
        </div>
      )}
      {state === "error" && (
        <div className="flex flex-col items-center gap-2 py-2">
          <AlertCircle className="w-6 h-6 text-red-400" />
          <p className="text-xs text-red-400">{message}</p>
        </div>
      )}
      {state === "idle" && (
        <div className="flex flex-col items-center gap-2 py-2">
          <Upload className="w-6 h-6 text-slate-500" />
          <p className="text-xs text-slate-400">{isDragActive ? "Drop files here" : "Drop files or click to upload"}</p>
          <p className="text-xs text-slate-600">PDF · DOCX · TXT · MD · CSV</p>
        </div>
      )}
    </div>
  )
}
