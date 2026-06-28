import Navbar from "@/components/layout/Navbar"
import Hero from "@/components/landing/Hero"
import Features from "@/components/landing/Features"
import Stats from "@/components/landing/Stats"
import Footer from "@/components/layout/Footer"
import GradientBackground from "@/components/ui/GradientBackground"

export default function Home() {
  return (
    <div className="min-h-screen text-white relative">
      <GradientBackground />
      <Navbar />
      <Hero />
      <Features />
      <Stats />
      <Footer />
    </div>
  )
}
