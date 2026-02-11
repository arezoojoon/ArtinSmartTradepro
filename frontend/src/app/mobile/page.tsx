"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Bell, Zap, TrendingUp, ShieldAlert, DollarSign, Users, Home, Search, Brain, Menu } from "lucide-react"
import api from "@/lib/api"
import Link from "next/link"

export default function MobileDashboard() {
    const [shocks, setShocks] = useState<any[]>([])

    useEffect(() => {
        // Fetch real alerts
        api.get("/api/toolbox/shocks")
            .then(res => setShocks(res.data))
            .catch(err => console.error(err))
    }, [])

    return (
        <div className="min-h-screen bg-slate-50 pb-20">
            {/* Header */}
            <header className="bg-slate-900 text-white p-4 sticky top-0 z-10 shadow-md">
                <div className="flex justify-between items-center">
                    <div>
                        <h1 className="text-lg font-bold">Control Tower 🗼</h1>
                        <p className="text-xs text-slate-400">Artin Smart Trade</p>
                    </div>
                    <Bell className="h-6 w-6" />
                </div>
            </header>

            {/* Widgets Grid */}
            <div className="p-4 space-y-4">

                {/* 1. Market Shock (High Priority) */}
                <Card className="border-l-4 border-l-red-500 shadow-sm">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium flex items-center text-red-600">
                            <Zap className="mr-2 h-4 w-4" /> Market Shocks
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        {shocks.length === 0 ? (
                            <div className="text-sm text-slate-500">No active market alerts.</div>
                        ) : (
                            <div className="space-y-3">
                                {shocks.map((shock, i) => (
                                    <div key={i} className="flex justify-between items-center text-sm border-b pb-2 last:border-0 last:pb-0">
                                        <span>{shock.message}</span>
                                        <Badge variant="destructive" className="ml-2 text-[10px]">{shock.severity}</Badge>
                                    </div>
                                ))}
                            </div>
                        )}
                    </CardContent>
                </Card>

                {/* 2. Today's Opportunities */}
                <Card className="shadow-sm">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium flex items-center">
                            <TrendingUp className="mr-2 h-4 w-4 text-green-600" /> Opportunities
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-3">
                            <div className="flex justify-between items-center text-sm">
                                <span>Saffron to EU</span>
                                <Badge variant="outline" className="bg-green-50 text-green-700">92% Match</Badge>
                            </div>
                            <div className="flex justify-between items-center text-sm">
                                <span>Pistachio to UAE</span>
                                <Badge variant="outline" className="bg-green-50 text-green-700">88% Match</Badge>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* 3. Risk Watch */}
                <Card className="shadow-sm">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium flex items-center">
                            <ShieldAlert className="mr-2 h-4 w-4 text-orange-500" /> Risk Watch
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="flex items-center space-x-2 text-sm">
                            <div className="h-2 w-2 rounded-full bg-orange-500 animate-pulse"></div>
                            <span>Turkey: New tariff update pending</span>
                        </div>
                    </CardContent>
                </Card>

                {/* 4. Cash Flow */}
                <Card className="shadow-sm">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium flex items-center">
                            <DollarSign className="mr-2 h-4 w-4 text-blue-500" /> Cash Flow
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="flex justify-between items-center">
                            <span className="text-sm text-slate-500">Projected (30d)</span>
                            <span className="font-bold text-lg">$145,000</span>
                        </div>
                    </CardContent>
                </Card>

                {/* 5. New leads */}
                <Card className="shadow-sm">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium flex items-center">
                            <Users className="mr-2 h-4 w-4 text-cyan-500" /> New Leads
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">12</div>
                        <p className="text-xs text-muted-foreground">+4 from yesterday</p>
                    </CardContent>
                </Card>

            </div>

            {/* Bottom Nav */}
            <div className="fixed bottom-0 w-full bg-white border-t flex justify-around p-3 pb-6 text-xs text-slate-500">
                <div className="flex flex-col items-center text-blue-600">
                    <Home className="h-6 w-6 mb-1" />
                    Home
                </div>
                <div className="flex flex-col items-center">
                    <Search className="h-6 w-6 mb-1" />
                    Hunter
                </div>
                <div className="flex flex-col items-center">
                    <Brain className="h-6 w-6 mb-1" />
                    Brain
                </div>
                <div className="flex flex-col items-center">
                    <Menu className="h-6 w-6 mb-1" />
                    Menu
                </div>
            </div>
        </div>
    )
}
