"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { BarChart3, Globe, Ship, DollarSign, Download, ArrowRight, TrendingUp, AlertCircle, Activity, LayoutGrid, ChevronRight, Zap, Loader2 } from "lucide-react"
import Link from "next/link"
import { Badge } from "@/components/ui/badge"
import api from "@/lib/api"

export default function ToolboxPage() {
    const [shocks, setShocks] = useState<any[]>([])
    const [shocksLoading, setShocksLoading] = useState(true)
    const [exporting, setExporting] = useState<string | null>(null)

    useEffect(() => {
        const fetchShocks = async () => {
            try {
                const res = await api.get("/toolbox/shocks")
                const data = res.data
                setShocks(Array.isArray(data) ? data : data.alerts || data.shocks || [])
            } catch {
                setShocks([])
            } finally {
                setShocksLoading(false)
            }
        }
        fetchShocks()
    }, [])

    const handleExport = async (type: string) => {
        setExporting(type)
        try {
            let data: any[] = []
            let filename = ""
            if (type === "trade") {
                const res = await api.get("/toolbox/trade-data")
                data = Array.isArray(res.data) ? res.data : []
                filename = "global_trade_map.csv"
            } else if (type === "fx") {
                const res = await api.get("/toolbox/fx/history?base=USD&quote=EUR&days=30")
                data = Array.isArray(res.data) ? res.data : []
                filename = "fx_volatility_history.csv"
            } else if (type === "freight") {
                const res = await api.get("/toolbox/freight?origin=CHN&dest=USA&equipment=20GP")
                data = res.data ? [res.data] : []
                filename = "freight_index.csv"
            }
            if (data.length === 0) { setExporting(null); return }
            const headers = Object.keys(data[0])
            const csv = [headers.join(","), ...data.map(row => headers.map(h => JSON.stringify(row[h] ?? "")).join(","))].join("\n")
            const blob = new Blob([csv], { type: "text/csv" })
            const url = URL.createObjectURL(blob)
            const a = document.createElement("a")
            a.href = url; a.download = filename; a.click()
            URL.revokeObjectURL(url)
        } catch (e) {
            console.error("Export failed", e)
        } finally {
            setExporting(null)
        }
    }

    const tools = [
        {
            title: "Global Trade Data",
            desc: "Search 50M+ import/export records. HS Codes, Volumes, Core Values.",
            icon: Globe,
            href: "/toolbox/trade-data",
            accent: "group-hover:text-[#f5a623]"
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
                        <div className="p-2 bg-[#f5a623]/10 rounded-lg border border-[#f5a623]/20 backdrop-blur-md">
                            <LayoutGrid className="h-6 w-6 text-[#f5a623]" />
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
                        <Card className="bg-[#12253f]/80 backdrop-blur-xl border border-[#1e3a5f] hover:border-[#f5a623]/30 transition-all cursor-pointer h-full relative group overflow-hidden">
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
                                <div className="mt-6 flex items-center text-[10px] font-bold text-[#f5a623] uppercase tracking-widest opacity-0 group-hover:opacity-100 transition-all transform translate-x-[-10px] group-hover:translate-x-0">
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
                <Card className="lg:col-span-4 bg-[#12253f]/80 backdrop-blur-2xl border border-[#1e3a5f] shadow-2xl relative overflow-hidden">
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
                        {shocksLoading ? (
                            <div className="flex items-center justify-center py-8 text-slate-500">
                                <Loader2 className="h-5 w-5 animate-spin mr-2" /> Loading signals...
                            </div>
                        ) : shocks.length === 0 ? (
                            <div className="text-center py-8 text-slate-500 text-sm">
                                No active market signals. All clear.
                            </div>
                        ) : (
                            shocks.slice(0, 5).map((shock: any, idx: number) => {
                                const severity = shock.severity || shock.level || "info"
                                const colors = severity === "high" ? { border: "hover:border-red-500/30", icon: "bg-red-500/10 border-red-500/20 text-red-400", text: "group-hover:text-red-400" }
                                    : severity === "medium" ? { border: "hover:border-amber-500/30", icon: "bg-amber-500/10 border-amber-500/20 text-amber-400", text: "group-hover:text-amber-400" }
                                    : { border: "hover:border-cyan-500/30", icon: "bg-cyan-500/10 border-cyan-500/20 text-cyan-400", text: "group-hover:text-cyan-400" }
                                return (
                                    <div key={idx} className={`flex items-center justify-between p-4 bg-white/5 rounded-xl border border-white/5 group ${colors.border} transition-all`}>
                                        <div className="flex items-center gap-4">
                                            <div className={`p-3 border rounded-xl ${colors.icon}`}>
                                                {severity === "high" ? <AlertCircle className="h-6 w-6" /> : <TrendingUp className="h-6 w-6" />}
                                            </div>
                                            <div>
                                                <p className={`text-sm font-bold text-white ${colors.text} transition-colors`}>{shock.title || shock.pair || "Signal"}</p>
                                                <p className="text-[11px] text-slate-500 uppercase font-medium mt-0.5">{shock.message || shock.description || ""}</p>
                                            </div>
                                        </div>
                                        <Badge className={`${severity === "high" ? "bg-red-500/20 text-red-400 border-red-500/30" : severity === "medium" ? "bg-amber-500/20 text-amber-400 border-amber-500/30" : "bg-blue-500/20 text-blue-400 border-blue-500/30"} text-[10px] font-bold`}>
                                            {severity.toUpperCase()}
                                        </Badge>
                                    </div>
                                )
                            })
                        )}
                    </CardContent>
                </Card>

                {/* Data Export Port */}
                <Card className="lg:col-span-3 bg-[#12253f]/80 backdrop-blur-2xl border border-[#1e3a5f] shadow-2xl relative">
                    <CardHeader>
                        <CardTitle className="text-white text-lg flex items-center gap-2">
                            <Zap className="h-5 w-5 text-[#f5a623]" /> Data Export Port
                        </CardTitle>
                        <CardDescription className="text-slate-500 text-[10px] uppercase font-bold mt-1">
                            Download raw data for institutional reporting.
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <Button variant="outline" className="w-full justify-between h-14 border-[#1e3a5f] bg-[#0e1e33]/40 text-slate-300 hover:border-[#f5a623] hover:text-[#f5a623] transition-all px-6" onClick={() => handleExport("trade")} disabled={exporting === "trade"}>
                            <span className="flex items-center font-bold text-xs uppercase tracking-widest"><Globe className="mr-3 h-4 w-4" /> Global Trade Map</span>
                            {exporting === "trade" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
                        </Button>
                        <Button variant="outline" className="w-full justify-between h-14 border-[#1e3a5f] bg-[#0e1e33]/40 text-slate-300 hover:border-[#f5a623] hover:text-[#f5a623] transition-all px-6" onClick={() => handleExport("fx")} disabled={exporting === "fx"}>
                            <span className="flex items-center font-bold text-xs uppercase tracking-widest"><DollarSign className="mr-3 h-4 w-4" /> FX Volatility History</span>
                            {exporting === "fx" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
                        </Button>
                        <Button variant="outline" className="w-full justify-between h-14 border-[#1e3a5f] bg-[#0e1e33]/40 text-slate-300 hover:border-[#f5a623] hover:text-[#f5a623] transition-all px-6" onClick={() => handleExport("freight")} disabled={exporting === "freight"}>
                            <span className="flex items-center font-bold text-xs uppercase tracking-widest"><Ship className="mr-3 h-4 w-4" /> Scafi Freight Index</span>
                            {exporting === "freight" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
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
