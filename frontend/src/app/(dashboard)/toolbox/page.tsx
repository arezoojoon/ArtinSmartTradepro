"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { BarChart3, Globe, Ship, DollarSign, Download, ArrowRight } from "lucide-react"
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
        <div className="space-y-6">
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                {tools.map((tool) => (
                    <Link href={tool.href} key={tool.title}>
                        <Card className="hover:bg-accent/50 transition-colors cursor-pointer h-full">
                            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                <CardTitle className="text-sm font-medium">
                                    {tool.title}
                                </CardTitle>
                                <tool.icon className={`h-4 w-4 ${tool.color}`} />
                            </CardHeader>
                            <CardContent>
                                <div className="text-2xl font-bold hidden"></div>
                                <p className="text-xs text-muted-foreground mt-2">
                                    {tool.desc}
                                </p>
                            </CardContent>
                        </Card>
                    </Link>
                ))}
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
                <Card className="col-span-4">
                    <CardHeader>
                        <CardTitle>Market Pulse 💓</CardTitle>
                        <CardDescription>
                            Real-time signals from your active markets.
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="flex items-center justify-center h-[200px] text-muted-foreground">
                            Select a tool to view detailed data.
                        </div>
                    </CardContent>
                </Card>

                <Card className="col-span-3">
                    <CardHeader>
                        <CardTitle>Data Export</CardTitle>
                        <CardDescription>
                            Download raw data for Excel/PowerBI.
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <Button variant="outline" className="w-full justify-between">
                            <span className="flex items-center"><Globe className="mr-2 h-4 w-4" /> Trade Data (CSV)</span>
                            <Download className="h-4 w-4" />
                        </Button>
                        <Button variant="outline" className="w-full justify-between">
                            <span className="flex items-center"><DollarSign className="mr-2 h-4 w-4" /> FX History (CSV)</span>
                            <Download className="h-4 w-4" />
                        </Button>
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}
