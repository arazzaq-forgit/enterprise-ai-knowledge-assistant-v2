export default function GradientBackground() {
  return (
    <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
      <div className="absolute inset-0" style={{backgroundColor: "#0A0F1E"}} />
      <div className="animate-aurora absolute -top-40 -left-40 w-[700px] h-[700px] rounded-full"
        style={{background: "radial-gradient(circle, rgba(99,102,241,0.3) 0%, transparent 70%)"}} />
      <div className="animate-aurora absolute -bottom-40 -right-20 w-[600px] h-[600px] rounded-full"
        style={{background: "radial-gradient(circle, rgba(6,182,212,0.2) 0%, transparent 70%)", animationDelay: "-3s"}} />
      <div className="animate-aurora absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] rounded-full"
        style={{background: "radial-gradient(circle, rgba(139,92,246,0.15) 0%, transparent 70%)", animationDelay: "-5s"}} />
    </div>
  )
}
