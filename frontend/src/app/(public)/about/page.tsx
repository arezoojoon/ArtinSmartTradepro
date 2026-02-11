"use client";

import { Linkedin, Globe, Zap, Shield, Brain, Target, ArrowRight } from "lucide-react";
import Link from "next/link";

export default function AboutPage() {
    return (
        <div className="min-h-screen bg-navy-950 text-white">
            {/* Header */}
            <header className="border-b border-navy-800/50 px-6 py-4">
                <div className="mx-auto max-w-7xl flex items-center justify-between">
                    <Link href="/" className="text-2xl font-bold">
                        <span className="text-gold-400">Artin</span> Smart Trade
                    </Link>
                    <nav className="flex items-center gap-6">
                        <Link href="/pricing" className="text-navy-300 hover:text-white transition-colors">Pricing</Link>
                        <Link href="/auth/login" className="px-4 py-2 rounded-lg border border-navy-600 text-navy-200 hover:border-gold-400 hover:text-gold-400 transition-all">
                            Sign In
                        </Link>
                    </nav>
                </div>
            </header>

            {/* Hero */}
            <section className="py-20 px-6 text-center">
                <h1 className="text-4xl md:text-5xl font-bold mb-6">
                    The <span className="text-gold-400">AI Trade Operating System</span>
                </h1>
                <p className="text-xl text-navy-300 max-w-2xl mx-auto mb-8">
                    We build intelligent tools that help traders, importers, and exporters
                    find the right buyers, at the right time, in the right market — with AI.
                </p>
                <div className="flex items-center justify-center gap-4">
                    <Link href="/pricing" className="px-6 py-3 bg-gold-400 text-navy-950 rounded-xl font-semibold hover:bg-gold-300 transition-all flex items-center gap-2">
                        View Plans <ArrowRight className="h-4 w-4" />
                    </Link>
                </div>
            </section>

            {/* What We Do */}
            <section className="px-6 pb-20">
                <div className="mx-auto max-w-5xl grid grid-cols-1 md:grid-cols-3 gap-6">
                    {[
                        {
                            icon: Target,
                            title: "Lead Intelligence",
                            description: "Find verified buyers and suppliers across 100+ countries with AI-powered lead scoring and intent analysis."
                        },
                        {
                            icon: Brain,
                            title: "Trade Intelligence",
                            description: "Know which product sells best, in which season, in which market — before your competitors do."
                        },
                        {
                            icon: Zap,
                            title: "One-Click Outreach",
                            description: "Reach prospects via WhatsApp with automated follow-ups, campaign tracking, and CRM integration."
                        },
                    ].map((item) => (
                        <div key={item.title} className="bg-navy-900/50 border border-navy-700/30 rounded-xl p-6 hover:border-gold-400/30 transition-all">
                            <item.icon className="h-8 w-8 text-gold-400 mb-4" />
                            <h3 className="text-lg font-bold mb-2">{item.title}</h3>
                            <p className="text-sm text-navy-400">{item.description}</p>
                        </div>
                    ))}
                </div>
            </section>

            {/* Founder Section */}
            <section className="px-6 pb-20">
                <div className="mx-auto max-w-3xl bg-navy-900/50 border border-navy-700/30 rounded-2xl p-8 md:p-12">
                    <div className="flex flex-col md:flex-row items-start gap-8">
                        <div className="flex-shrink-0 w-24 h-24 rounded-full bg-gradient-to-br from-gold-400 to-gold-600 flex items-center justify-center text-navy-950 text-3xl font-bold">
                            AM
                        </div>
                        <div>
                            <h2 className="text-2xl font-bold mb-1">Arezoo Mohammadzadegan</h2>
                            <p className="text-gold-400 font-medium mb-4">Founder & Lead AI Architect</p>
                            <p className="text-navy-300 text-sm leading-relaxed mb-6">
                                With deep expertise in Python, AI systems, and international trade,
                                Arezoo founded Artin Smart Trade to automate the manual processes that
                                waste traders' time and money. Her vision: every trader deserves an
                                AI-powered operations team — accessible with one click, at a fraction
                                of the cost.
                            </p>
                            <p className="text-navy-300 text-sm leading-relaxed mb-6">
                                Previously building enterprise solutions for FMCG and export-import companies,
                                she identified a critical gap: traders spend 80% of their time searching for
                                data instead of closing deals. Artin Smart Trade eliminates that gap.
                            </p>
                            <a
                                href="https://www.linkedin.com/in/arezoomohammadzadegan/"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center gap-2 px-4 py-2 bg-navy-800 border border-navy-600 rounded-lg text-sm text-navy-200 hover:border-gold-400 hover:text-gold-400 transition-all"
                            >
                                <Linkedin className="h-4 w-4" /> LinkedIn Profile
                            </a>
                        </div>
                    </div>
                </div>
            </section>

            {/* Trust Signals */}
            <section className="px-6 pb-20">
                <div className="mx-auto max-w-5xl grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
                    {[
                        { value: "100+", label: "Countries Covered" },
                        { value: "50K+", label: "Leads Generated" },
                        { value: "99.9%", label: "Uptime SLA" },
                        { value: "24/7", label: "Enterprise Support" },
                    ].map((stat) => (
                        <div key={stat.label} className="bg-navy-900/30 border border-navy-800/50 rounded-xl p-6">
                            <p className="text-3xl font-bold text-gold-400">{stat.value}</p>
                            <p className="text-xs text-navy-500 mt-1">{stat.label}</p>
                        </div>
                    ))}
                </div>
            </section>

            {/* Footer */}
            <footer className="border-t border-navy-800/50 px-6 py-8">
                <div className="mx-auto max-w-7xl flex flex-col md:flex-row items-center justify-between gap-4">
                    <p className="text-sm text-navy-500">
                        © 2026 Artin Smart Trade. All rights reserved.
                    </p>
                    <div className="flex items-center gap-6">
                        <Link href="/pricing" className="text-sm text-navy-400 hover:text-white">Pricing</Link>
                        <a href="mailto:support@artinsmartagent.com" className="text-sm text-navy-400 hover:text-white">Contact</a>
                        <a href="https://www.linkedin.com/in/arezoomohammadzadegan/" target="_blank" rel="noopener noreferrer" className="text-navy-400 hover:text-white">
                            <Linkedin className="h-4 w-4" />
                        </a>
                    </div>
                </div>
            </footer>
        </div>
    );
}
