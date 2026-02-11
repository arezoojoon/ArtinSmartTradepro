import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ChevronRight, Shield, Globe, Bot, BarChart3, Users, Zap } from "lucide-react";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-navy-950 text-white selection:bg-gold-500 selection:text-navy-900">
      {/* Navbar */}
      <nav className="fixed top-0 w-full z-50 border-b border-navy-800 bg-navy-950/80 backdrop-blur-md">
        <div className="container mx-auto flex h-16 items-center justify-between px-4">
          <div className="flex items-center space-x-2">
            <div className="h-8 w-8 rounded bg-gold-500 flex items-center justify-center">
              <Bot className="h-5 w-5 text-navy-900" />
            </div>
            <span className="text-xl font-bold tracking-tight">Artin <span className="text-gold-400">Smart Trade</span></span>
          </div>
          <div className="hidden md:flex items-center space-x-8 text-sm font-medium text-gray-300">
            <Link href="#features" className="hover:text-gold-400 transition-colors">Features</Link>
            <Link href="#pricing" className="hover:text-gold-400 transition-colors">Pricing</Link>
            <Link href="#testimonials" className="hover:text-gold-400 transition-colors">Success Stories</Link>
          </div>
          <div className="flex items-center space-x-4">
            <Link href="/login" className="text-sm font-medium text-white hover:text-gold-400">Log in</Link>
            <Link href="/register">
              <Button variant="gold" className="rounded-full px-6">Get Started</Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-32 pb-20 md:pt-48 md:pb-32 overflow-hidden">
        <div className="absolute inset-0 z-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-navy-800 via-navy-950 to-navy-950 opacity-40"></div>
        <div className="container relative z-10 mx-auto px-4 text-center">
          <div className="inline-flex items-center rounded-full border border-gold-500/30 bg-gold-500/10 px-3 py-1 text-sm font-medium text-gold-400 mb-8 backdrop-blur-sm">
            <span className="flex h-2 w-2 rounded-full bg-gold-400 mr-2 animate-pulse"></span>
            Now available for Global Trade
          </div>
          <h1 className="mx-auto max-w-4xl text-5xl font-extrabold tracking-tight md:text-7xl lg:text-8xl">
            The World's First <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-gold-300 via-gold-500 to-gold-300 animate-gradient">AI Trade Operating System</span>
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg text-gray-400 md:text-xl">
            Automate your B2B sales, find leads specifically for your industry, and close deals on WhatsApp 24/7. Powered by Gemini Vision & Voice.
          </p>
          <div className="mt-10 flex flex-col items-center justify-center space-y-4 md:flex-row md:space-x-6 md:space-y-0">
            <Link href="/register">
              <Button size="lg" className="h-14 bg-gold-500 text-navy-900 hover:bg-gold-600 font-bold px-8 text-lg rounded-full">
                Start Free Trial <ChevronRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
            <Link href="/demo">
              <Button variant="outline" size="lg" className="h-14 border-navy-700 bg-navy-900 text-white hover:bg-navy-800 hover:text-gold-400 px-8 text-lg rounded-full">
                View Live Demo
              </Button>
            </Link>
          </div>

          {/* Dashboard Preview */}
          <div className="mt-20 relative mx-auto max-w-5xl rounded-xl border border-navy-800 bg-navy-900/50 p-2 shadow-2xl backdrop-blur-sm lg:p-4">
            <div className="aspect-video w-full rounded-lg bg-navy-950/80 border border-navy-800 overflow-hidden relative group">
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-gray-600">High-Fidelity Dashboard Preview Image Here</span>
              </div>
            </div>
            <div className="absolute -inset-1 z-[-1] rounded-xl bg-gradient-to-r from-gold-500/20 to-navy-500/20 blur opacity-30"></div>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section id="features" className="py-24 bg-navy-900/50">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold tracking-tight text-white md:text-5xl">Built for Modern Traders</h2>
            <p className="mt-4 text-lg text-gray-400">Everything you need to scale your B2B business in one platform.</p>
          </div>
          <div className="grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-3">
            {[
              { title: "Global Lead Hunter", icon: Globe, desc: "Scrape thousands of verified leads from Google Maps & Directories in seconds." },
              { title: "Smart Scanner", icon: Zap, desc: "Scan business cards with Gemini Vision. Extracts data with 99% accuracy." },
              { title: "Verified Marketplace", icon: Shield, desc: "Connect with trusted suppliers and buyers in a secure environment." },
              { title: "AI Negotiation", icon: Bot, desc: "Let AI handle initial price negotiations and objection handling 24/7." },
              { title: "Profit Analytics", icon: BarChart3, desc: "Real-time margin analysis and cost leakage detection." },
              { title: "CRM & Pipeline", icon: Users, desc: "Built-in CRM to manage your buyers, sellers, and trade documents." }
            ].map((feature, i) => (
              <div key={i} className="group relative rounded-2xl border border-navy-800 bg-navy-950 p-8 hover:border-gold-500/50 transition-colors">
                <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-lg bg-navy-900 text-gold-400 group-hover:bg-gold-500 group-hover:text-navy-900 transition-colors">
                  <feature.icon className="h-6 w-6" />
                </div>
                <h3 className="mb-2 text-xl font-bold text-white">{feature.title}</h3>
                <p className="text-gray-400">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 relative overflow-hidden">
        <div className="absolute inset-0 bg-gold-500"></div>
        <div className="container relative mx-auto px-4 text-center">
          <h2 className="mx-auto max-w-2xl text-4xl font-bold text-navy-900 md:text-5xl">Ready to automate your trade?</h2>
          <p className="mx-auto mt-4 max-w-xl text-lg text-navy-800 font-medium">Join 500+ global traders using Artin Smart Agent today.</p>
          <div className="mt-8 flex justify-center">
            <Link href="/register">
              <Button size="lg" className="h-14 bg-navy-900 text-white hover:bg-navy-800 font-bold px-8 text-lg rounded-full">
                Get Started Now
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-navy-800 bg-navy-950 py-12">
        <div className="container mx-auto px-4 text-center text-gray-400 text-sm">
          <p>&copy; 2026 Artin Smart Trade. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
