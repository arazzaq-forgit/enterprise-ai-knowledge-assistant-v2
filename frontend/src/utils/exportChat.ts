import { jsPDF } from "jspdf"
import { Document, Packer, Paragraph, TextRun, HeadingLevel } from "docx"

export interface ExportMessage {
  role: "user" | "assistant"
  content: string
  confidence?: { score: number; label: string }
  hallucination?: { risk_level: string }
}

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

function timestamp(): string {
  return new Date().toISOString().slice(0, 19).replace(/[:T]/g, "-")
}

function metaLine(msg: ExportMessage): string | null {
  if (!msg.confidence) return null
  let line = `Confidence: ${msg.confidence.score}% (${msg.confidence.label})`
  if (msg.hallucination) line += ` · Grounding risk: ${msg.hallucination.risk_level}`
  return line
}

// ---------------------------------------------------------------------
// Markdown
// ---------------------------------------------------------------------
export function exportAsMarkdown(messages: ExportMessage[]) {
  let md = `# DocMind AI — Chat Export\n\n_Exported ${new Date().toLocaleString()}_\n\n---\n\n`

  for (const msg of messages) {
    md += msg.role === "user" ? `### 🧑 You\n\n` : `### 🤖 DocMind AI\n\n`
    md += `${msg.content}\n\n`
    const meta = metaLine(msg)
    if (meta) md += `> ${meta}\n\n`
  }

  downloadBlob(new Blob([md], { type: "text/markdown;charset=utf-8" }), `docmind-chat-${timestamp()}.md`)
}

// ---------------------------------------------------------------------
// PDF (jsPDF — client-side, no backend round-trip)
// ---------------------------------------------------------------------
export function exportAsPDF(messages: ExportMessage[]) {
  const doc = new jsPDF({ unit: "pt", format: "a4" })
  const pageWidth = doc.internal.pageSize.getWidth()
  const pageHeight = doc.internal.pageSize.getHeight()
  const margin = 40
  const maxWidth = pageWidth - margin * 2
  const lineHeight = 14
  let y = margin

  const ensureSpace = (needed: number) => {
    if (y + needed > pageHeight - margin) {
      doc.addPage()
      y = margin
    }
  }

  const addWrapped = (text: string, fontSize: number, bold = false, color = 0) => {
    doc.setFontSize(fontSize)
    doc.setFont("helvetica", bold ? "bold" : "normal")
    doc.setTextColor(color)
    const lines: string[] = doc.splitTextToSize(text, maxWidth)
    for (const line of lines) {
      ensureSpace(lineHeight)
      doc.text(line, margin, y)
      y += lineHeight
    }
  }

  addWrapped("DocMind AI — Chat Export", 16, true)
  addWrapped(`Exported ${new Date().toLocaleString()}`, 9, false, 120)
  y += 10

  for (const msg of messages) {
    y += 8
    addWrapped(msg.role === "user" ? "You" : "DocMind AI", 11, true)
    addWrapped(msg.content, 10)
    const meta = metaLine(msg)
    if (meta) addWrapped(meta, 8, false, 100)
  }

  doc.save(`docmind-chat-${timestamp()}.pdf`)
}

// ---------------------------------------------------------------------
// DOCX (docx package — client-side, builds a real .docx, not an HTML hack)
// ---------------------------------------------------------------------
export async function exportAsDocx(messages: ExportMessage[]) {
  const children: Paragraph[] = [
    new Paragraph({
      heading: HeadingLevel.HEADING_1,
      children: [new TextRun({ text: "DocMind AI — Chat Export" })],
    }),
    new Paragraph({
      children: [new TextRun({ text: `Exported ${new Date().toLocaleString()}`, italics: true, size: 18 })],
    }),
    new Paragraph({ text: "" }),
  ]

  for (const msg of messages) {
    children.push(
      new Paragraph({
        heading: HeadingLevel.HEADING_3,
        children: [new TextRun({ text: msg.role === "user" ? "You" : "DocMind AI", bold: true })],
      })
    )
    children.push(new Paragraph({ children: [new TextRun({ text: msg.content })] }))

    const meta = metaLine(msg)
    if (meta) {
      children.push(
        new Paragraph({ children: [new TextRun({ text: meta, italics: true, size: 18, color: "666666" })] })
      )
    }
    children.push(new Paragraph({ text: "" }))
  }

  const doc = new Document({ sections: [{ children }] })
  const blob = await Packer.toBlob(doc)
  downloadBlob(blob, `docmind-chat-${timestamp()}.docx`)
}