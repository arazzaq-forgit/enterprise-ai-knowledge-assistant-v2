const stats = [
  { value: "50MB",  label: "Max file size",        sub: "per document" },
  { value: "5",     label: "File formats",          sub: "PDF DOCX TXT MD CSV" },
  { value: "100%",  label: "Private & local",       sub: "zero data sent out" },
  { value: "<2s",   label: "Retrieval speed",       sub: "per question" },
];

export default function Stats() {
  return (
    <section className="py-20 px-6">
      <div className="max-w-5xl mx-auto">
        <div className="glass-strong rounded-3xl p-12 grid grid-cols-2 md:grid-cols-4 gap-8 border border-indigo-500/20">
          {stats.map((s) => (
            <div key={s.label} className="text-center">
              <div className="font-display text-5xl font-bold gradient-text mb-2">
                {s.value}
              </div>
              <div className="text-white font-medium mb-1">{s.label}</div>
              <div className="text-slate-500 text-xs">{s.sub}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}