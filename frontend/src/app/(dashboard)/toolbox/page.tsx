"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { BarChart3, Globe, Ship, DollarSign, Download, ArrowRight, TrendingUp, AlertCircle, Activity } from "lucide-react"
import Link from "next/link"

export default function ToolboxPage() {
    const tools = [
        {
            title: "Global Trade Data",
            desc: "Search 50M+ import/export records. HS Codes, Volumes, Values.",
            icon: Globe,
            href: "/toolbox/trade-data",
            color: "text-blue-500"
        },
        {
            title: "Freight Rates",
            desc: "Get instant estimates for Air, Sea (20GP/40HC) routes.",
            icon: Ship,
            href: "/toolbox/freight",
            color: "text-cyan-500"
        },
        {
            title: "FX Center",
            desc: "Live rates & volatility analysis for major trading pairs.",
            icon: DollarSign,
            href: "/toolbox/fx",
            color: "text-green-500"
        },
        {
            title: "BI Analytics",
            desc: "KPI Dashboard: DSO, Conversion Rates, Pipeline Health.",
            icon: BarChart3,
            href: "/toolbox/analytics",
            color: "text-purple-500"
        }
    ]

    return (
        <div className="space-y-6 p-4 md:p-8 pt-6">
            <div>
                <h2 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">Trader Toolbox</h2>
                <p className="text-slate-500 dark:text-slate-400 mt-1">Deterministic data sources and analytical tools</p>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                {tools.map((tool) => (
                    <Link href={tool.href} key={tool.title}>
                        <Card className="bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 hover:shadow-md transition-all cursor-pointer h-full">
                            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                <CardTitle className="text-sm font-bold text-slate-900 dark:text-white">
                                    {tool.title}
                                </CardTitle>
                                <tool.icon className={`h-5 w-5 ${tool.color}`} />
                            </CardHeader>
                            <CardContent>
                                <p className="text-xs text-slate-500 dark:text-slate-400 mt-2 font-medium leading-relaxed">
                                    {tool.desc}
                                </p>
                            </CardContent>
                        </Card>
                    </Link>
                ))}
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
                <Card className="col-span-4 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 shadow-sm">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2 text-slate-900 dark:text-white">
                            <Activity className="h-5 w-5 text-red-500" />
                            Market Pulse
                        </CardTitle>
                        <CardDescription className="text-slate-500 dark:text-slate-400">
                            Real-time deterministic signals from your active markets.
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg border border-slate-100 dark:border-slate-700/50">
                            <div className="flex items-center gap-3">
                                <Ship className="h-8 w-8 text-cyan-600 p-1.5 bg-cyan-100 dark:bg-cyan-900/30 rounded-md" />
                                <div>
                                    <p className="text-sm font-bold text-slate-900 dark:text-white">Shanghai to Dubai (Jebel Ali)</p>
                                    <p className="text-xs text-slate-500 dark:text-slate-400">Freight rates spiked +4.2% in last 48h</p>
                                </div>
                            </div>
                            <TrendingUp className="h-5 w-5 text-red-500" />
                        </div>

                        <div className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg border border-slate-100 dark:border-slate-700/50">
                            <div className="flex items-center gap-3">
                                <DollarSign className="h-8 w-8 text-green-600 p-1.5 bg-green-100 dark:bg-green-900/30 rounded-md" />
                                <div>
                                    <p className="text-sm font-bold text-slate-900 dark:text-white">EUR/USD Volatility Alert</p>
                                    <p className="text-xs text-slate-500 dark:text-slate-400">ECB announcement caused 0.8% drop</p>
                                </div>
                            </div>
                            <AlertCircle className="h-5 w-5 text-orange-500" />
                        </div>

                        <div className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg border border-slate-100 dark:border-slate-700/50">
                            <div className="flex items-center gap-3">
                                <Globe className="h-8 w-8 text-blue-600 p-1.5 bg-blue-100 dark:bg-blue-900/30 rounded-md" />
                                <div>
                                    <p className="text-sm font-bold text-slate-900 dark:text-white">HS Code 0901.11 (Coffee)</p>
                                    <p className="text-xs text-slate-500 dark:text-slate-400">New EU import regulations published</p>
                                </div>
                            </div>
                            <AlertCircle className="h-5 w-5 text-blue-500" />
                        </div>
                    </CardContent>
                </Card>

                <Card className="col-span-3 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 shadow-sm">
                    <CardHeader>
                        <CardTitle className="text-slate-900 dark:text-white">Data Export</CardTitle>
                        <CardDescription className="text-slate-500 dark:text-slate-400">
                            Download raw verified data for PowerBI/Excel.
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <Button variant="outline" className="w-full justify-between border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800">
                            <span className="flex items-center"><Globe className="mr-2 h-4 w-4" /> Trade Data (CSV)</span>
                            <Download className="h-4 w-4" />
                        </Button>
                        <Button variant="outline" className="w-full justify-between border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800">
                            <span className="flex items-center"><DollarSign className="mr-2 h-4 w-4" /> FX History (CSV)</span>
                            <Download className="h-4 w-4" />
                        </Button>
                        <Button variant="outline" className="w-full justify-between border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800">
                            <span className="flex items-center"><Ship className="mr-2 h-4 w-4" /> Freight Index (CSV)</span>
                            <Download className="h-4 w-4" />
                        </Button>
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}
