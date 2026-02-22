"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { BarChart3, Globe, Ship, DollarSign, Download, ArrowRight, TrendingUp, AlertCircle, Activity, LayoutGrid, ChevronRight, Zap } from "lucide-react"
import Link from "next/link"
import { Badge } from "@/components/ui/badge"

export default function ToolboxPage() {
    const tools = [
        {
            title: "Global Trade Data",
            desc: "Search 50M+ import/export records. HS Codes, Volumes, Core Values.",
            icon: Globe,
            href: "/toolbox/trade-data",
            accent: "group-hover:text-[#D4AF37]"
        },
        {
            title: "Freight Rates",
            desc: "Get instant estimates for Air, Sea (20GP/40HC) routes with volatility bands.",
            icon: Ship,
            href: "/toolbox/freight",
            accent: "group-hover:text-cyan-400"
        },
        {
            title: "FX Center",
            desc: "Live rates & volatility analysis for 120+ global trading pairs.",
            icon: DollarSign,
            href: "/toolbox/fx",
            accent: "group-hover:text-emerald-400"
        },
        {
            title: "BI Analytics",
            desc: "KPI Intelligence Board: DSO, Conversion Rates, Pipeline Health Matrix.",
            icon: BarChart3,
            href: "/toolbox/analytics",
            accent: "group-hover:text-purple-400"
        }
    ]

    return (
        <div className="space-y-8 max-w-[1400px] mx-auto p-4 md:p-8 pt-6 min-h-screen">
            {/* Header Section */}
            <div className="flex flex-col md:flex-row md:justify-between md:items-end gap-6 border-b border-white/10 pb-6">
                <div>
                    <div className="flex items-center gap-3 mb-2">
                        <div className="p-2 bg-[#D4AF37]/10 rounded-lg border border-[#D4AF37]/20 backdrop-blur-md">
                            <LayoutGrid className="h-6 w-6 text-[#D4AF37]" />
                        </div>
                        <h2 className="text-3xl font-bold tracking-tight text-white">Trader Toolbox</h2>
                    </div>
                    <p className="text-slate-400 text-sm">Deterministic data sources and deterministic analytical terminals.</p>
                </div>
            </div>

            {/* Quick Access Grid */}
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
                {tools.map((tool) => (
                    <Link href={tool.href} key={tool.title}>
                        <Card className="bg-black/40 backdrop-blur-xl border border-white/10 hover:border-[#D4AF37]/30 transition-all cursor-pointer h-full relative group overflow-hidden">
                            <div className="absolute top-0 right-0 w-32 h-32 bg-white/5 rounded-full blur-3xl -mr-16 -mt-16 transition-opacity opacity-0 group-hover:opacity-100"></div>
                            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 relative z-10">
                                <CardTitle className="text-xs font-bold text-slate-400 uppercase tracking-widest group-hover:text-white transition-colors">
                                    {tool.title}
                                </CardTitle>
                                <tool.icon className={`h-5 w-5 text-slate-500 transition-colors ${tool.accent}`} />
                            </CardHeader>
                            <CardContent className="relative z-10">
                                <p className="text-xs text-slate-500 mt-2 font-medium leading-relaxed group-hover:text-slate-300 transition-colors">
                                    {tool.desc}
                                </p>
                                <div className="mt-6 flex items-center text-[10px] font-bold text-[#D4AF37] uppercase tracking-widest opacity-0 group-hover:opacity-100 transition-all transform translate-x-[-10px] group-hover:translate-x-0">
                                    Launch Terminal <ChevronRight className="h-3 w-3 ml-1" />
                                </div>
                            </CardContent>
                        </Card>
                    </Link>
                ))}
            </div>

            {/* Market Pulse & Terminal Logic */}
            <div className="grid gap-6 lg:grid-cols-7 mt-8">

                {/* Market Pulse (Bloomberg Style) */}
                <Card className="lg:col-span-4 bg-black/40 backdrop-blur-2xl border border-white/10 shadow-2xl relative overflow-hidden">
                    <div className="h-[2px] w-full bg-gradient-to-r from-transparent via-red-500 to-transparent opacity-20"></div>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2 text-white text-lg">
                            <Activity className="h-5 w-5 text-red-500" />
                            Market Pulse Terminal
                        </CardTitle>
                        <CardDescription className="text-slate-500 text-xs uppercase font-bold tracking-tighter mt-1">
                            Real-time deterministic signals from global trade registries.
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="flex items-center justify-between p-4 bg-white/5 rounded-xl border border-white/5 group hover:border-cyan-500/30 transition-all">
                            <div className="flex items-center gap-4">
                                <div className="p-3 bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 rounded-xl">
                                    <Ship className="h-6 w-6" />
                                </div>
                                <div>
                                    <p className="text-sm font-bold text-white group-hover:text-cyan-400 transition-colors">Shanghai &rarr; Jebel Ali (Freight Index)</p>
                                    <p className="text-[11px] text-slate-500 uppercase font-medium mt-0.5">Rates spiked +4.2% in last 48h (Congestion Alert)</p>
                                </div>
                            </div>
                            <TrendingUp className="h-5 w-5 text-red-500 animate-pulse" />
                        </div>

                        <div className="flex items-center justify-between p-4 bg-white/5 rounded-xl border border-white/5 group hover:border-emerald-500/30 transition-all">
                            <div className="flex items-center gap-4">
                                <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-xl">
                                    <DollarSign className="h-6 w-6" />
                                </div>
                                <div>
                                    <p className="text-sm font-bold text-white group-hover:text-emerald-400 transition-colors">EUR/USD Volatility Pulse</p>
                                    <p className="text-[11px] text-slate-500 uppercase font-medium mt-0.5">ECB announcement caused 0.8% liquidity drop</p>
                                </div>
                            </div>
                            <AlertCircle className="h-5 w-5 text-orange-500" />
                        </div>

                        <div className="flex items-center justify-between p-4 bg-white/5 rounded-xl border border-white/5 group hover:border-blue-500/30 transition-all">
                            <div className="flex items-center gap-4">
                                <div className="p-3 bg-blue-500/10 border border-blue-500/20 text-blue-400 rounded-xl">
                                    <Globe className="h-6 w-6" />
                                </div>
                                <div>
                                    <p className="text-sm font-bold text-white group-hover:text-blue-400 transition-colors">HS Code 0901.11 (Regulatory Update)</p>
                                    <p className="text-[11px] text-slate-500 uppercase font-medium mt-0.5">New EU Green-Deal import sanctions published</p>
                                </div>
                            </div>
                            <Badge className="bg-blue-500/20 text-blue-400 border border-blue-500/30 text-[10px] font-bold">INFO</Badge>
                        </div>
                    </CardContent>
                </Card>

                {/* Data Export Port */}
                <Card className="lg:col-span-3 bg-black/40 backdrop-blur-2xl border border-white/10 shadow-2xl relative">
                    <CardHeader>
                        <CardTitle className="text-white text-lg flex items-center gap-2">
                            <Zap className="h-5 w-5 text-[#D4AF37]" /> Data Export Port
                        </CardTitle>
                        <CardDescription className="text-slate-500 text-[10px] uppercase font-bold mt-1">
                            Download raw data for institutional reporting.
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <Button variant="outline" className="w-full justify-between h-14 border-white/10 bg-black/40 text-slate-300 hover:border-[#D4AF37] hover:text-[#D4AF37] transition-all px-6">
                            <span className="flex items-center font-bold text-xs uppercase tracking-widest"><Globe className="mr-3 h-4 w-4" /> Global Trade Map</span>
                            <Download className="h-4 w-4" />
                        </Button>
                        <Button variant="outline" className="w-full justify-between h-14 border-white/10 bg-black/40 text-slate-300 hover:border-[#D4AF37] hover:text-[#D4AF37] transition-all px-6">
                            <span className="flex items-center font-bold text-xs uppercase tracking-widest"><DollarSign className="mr-3 h-4 w-4" /> FX Volatility History</span>
                            <Download className="h-4 w-4" />
                        </Button>
                        <Button variant="outline" className="w-full justify-between h-14 border-white/10 bg-black/40 text-slate-300 hover:border-[#D4AF37] hover:text-[#D4AF37] transition-all px-6">
                            <span className="flex items-center font-bold text-xs uppercase tracking-widest"><Ship className="mr-3 h-4 w-4" /> Scafi Freight Index</span>
                            <Download className="h-4 w-4" />
                        </Button>

                        <div className="pt-4 text-center">
                            <p className="text-[9px] text-slate-600 font-bold uppercase tracking-[0.3em]">Institutional Grade Data Access</p>
                        </div>
                    </CardContent>
                </Card>

            </div>
        </div>
    )
}
