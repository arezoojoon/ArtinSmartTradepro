"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
    ArrowUpRight,
    ArrowDownRight,
    AlertTriangle,
    TrendingUp,
    Users,
    Wallet,
    Zap,
    Globe,
    Ship
} from "lucide-react";

// Mock Data
const OPPORTUNITIES = [
    { id: 1, title: "Rice Export to UAE", profit: "$12,400", confidence: "94%", type: "Arbitrage" },
    { id: 2, title: "Scrap Metal - Turkey", profit: "$8,200", confidence: "88%", type: "Demand" },
    { id: 3, title: "Saffron - Spain", profit: "$4,500", confidence: "91%", type: "Niche" },
];

const RISKS = [
    { id: 1, title: "Red Sea Shipping Delay", level: "High", impact: "2 Weeks", category: "Logistics" },
    { id: 2, title: "EUR/USD Volatility", level: "Medium", impact: "-2.4%", category: "FX" },
];

const LEADS = [
    { id: 1, name: "Al-Futtaim Group", country: "UAE", source: "Hunter", time: "2h ago" },
    { id: 2, name: "Hamburg Sud", country: "Germany", source: "TradeMap", time: "5h ago" },
    { id: 3, name: "TechParts China", country: "China", source: "UnComtrade", time: "1d ago" },
];

const SHOCKS = [
    { id: 1, asset: "Gold", change: "+1.2%", trend: "up" },
    { id: 2, asset: "Oil (Brent)", change: "-0.8%", trend: "down" },
    { id: 3, asset: "Bitcoin", change: "+3.5%", trend: "up" },
];

export default function MobileDashboard() {
    return (
        <div className="min-h-screen bg-slate-50/50 pb-24 pt-safe animate-in fade-in duration-500">

            {/* Header */}
            <div className="px-6 py-6 sticky top-0 bg-white/80 backdrop-blur-md z-40 border-b border-slate-100">
                <div className="flex justify-between items-center">
                    <div>
                        <h1 className="text-2xl font-bold tracking-tight text-slate-900">Control Tower</h1>
                        <p className="text-sm text-slate-500 font-medium">Good Afternoon, Artin</p>
                    </div>
                    <div className="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-bold border border-blue-200 shadow-sm">
                        A
                    </div>
                </div>
            </div>

            <div className="p-4 space-y-6">

                {/* 1. Cash Flow Widget (Apple Wallet Style) */}
                <section>
                    <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-blue-600 to-indigo-700 p-6 text-white shadow-lg shadow-blue-200/50">
                        <div className="relative z-10">
                            <div className="flex items-center gap-2 text-blue-100 mb-1">
                                <Wallet className="h-4 w-4" />
                                <span className="text-sm font-medium">Total Liquidity</span>
                            </div>
                            <div className="text-3xl font-bold tracking-tight mb-4">$1,240,500.00</div>
                            <div className="flex gap-4">
                                <div className="flex flex-col">
                                    <span className="text-xs text-blue-200">Pending In</span>
                                    <span className="font-semibold flex items-center gap-1">
                                        <ArrowUpRight className="h-3 w-3" /> $45k
                                    </span>
                                </div>
                                <div className="flex flex-col">
                                    <span className="text-xs text-blue-200">Pending Out</span>
                                    <span className="font-semibold flex items-center gap-1">
                                        <ArrowDownRight className="h-3 w-3" /> $12k
                                    </span>
                                </div>
                            </div>
                        </div>
                        {/* Background Decor */}
                        <div className="absolute top-0 right-0 -mr-8 -mt-8 h-32 w-32 rounded-full bg-white/10 blur-2xl"></div>
                    </div>
                </section>

                {/* 2. Today's Opportunities (Cards) */}
                <section>
                    <div className="flex items-center justify-between mb-3 px-1">
                        <h2 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
                            <Zap className="h-4 w-4 text-amber-500" />
                            Opportunities
                        </h2>
                        <Badge variant="outline" className="bg-amber-50 text-amber-700 border-amber-200">3 New</Badge>
                    </div>
                    <div className="space-y-3">
                        {OPPORTUNITIES.map((opp) => (
                            <Card key={opp.id} className="border-0 shadow-sm ring-1 ring-slate-100 active:scale-[0.98] transition-transform duration-200">
                                <CardContent className="p-4 flex justify-between items-center">
                                    <div>
                                        <h3 className="font-semibold text-slate-900">{opp.title}</h3>
                                        <div className="flex items-center gap-2 mt-1">
                                            <Badge variant="secondary" className="text-xs font-normal">
                                                {opp.type}
                                            </Badge>
                                            <span className="text-xs text-slate-500">Conf: {opp.confidence}</span>
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <div className="text-emerald-600 font-bold">{opp.profit}</div>
                                        <div className="text-[10px] text-slate-400 uppercase tracking-wide font-medium">Est. Profit</div>
                                    </div>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                </section>

                {/* 3. Risk Alerts (Banner) */}
                <section>
                    <div className="flex items-center justify-between mb-3 px-1">
                        <h2 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
                            <AlertTriangle className="h-4 w-4 text-rose-500" />
                            Critical Risks
                        </h2>
                    </div>
                    <div className="space-y-3">
                        {RISKS.map((risk) => (
                            <div key={risk.id} className="bg-rose-50 border border-rose-100 rounded-xl p-4 flex gap-3 items-start">
                                <div className="mt-0.5 bg-rose-100 p-1.5 rounded-full">
                                    {risk.category === "Logistics" ? <Ship className="h-4 w-4 text-rose-600" /> : <TrendingUp className="h-4 w-4 text-rose-600" />}
                                </div>
                                <div>
                                    <h4 className="text-sm font-semibold text-rose-900">{risk.title}</h4>
                                    <p className="text-xs text-rose-700 mt-1">
                                        Impact: <span className="font-medium">{risk.impact}</span>
                                    </p>
                                </div>
                            </div>
                        ))}
                    </div>
                </section>

                {/* 4. Market Shocks (Ticker) */}
                <section>
                    <div className="flex items-center justify-between mb-3 px-1">
                        <h2 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
                            <TrendingUp className="h-4 w-4 text-blue-500" />
                            Market Shocks
                        </h2>
                    </div>
                    <ScrollArea className="w-full whitespace-nowrap pb-2">
                        <div className="flex space-x-3">
                            {SHOCKS.map((shock) => (
                                <div key={shock.id} className="inline-flex items-center justify-between space-x-4 bg-white border border-slate-100 rounded-xl p-4 shadow-sm min-w-[140px]">
                                    <div className="flex flex-col">
                                        <span className="text-xs text-slate-500 font-medium">{shock.asset}</span>
                                        <span className={`text-lg font-bold ${shock.trend === "up" ? "text-emerald-600" : "text-rose-600"}`}>
                                            {shock.change}
                                        </span>
                                    </div>
                                    {shock.trend === "up" ? (
                                        <div className="bg-emerald-50 p-1.5 rounded-full">
                                            <ArrowUpRight className="h-4 w-4 text-emerald-600" />
                                        </div>
                                    ) : (
                                        <div className="bg-rose-50 p-1.5 rounded-full">
                                            <ArrowDownRight className="h-4 w-4 text-rose-600" />
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </ScrollArea>
                </section>

                {/* 5. New Leads (Mini List) */}
                <section>
                    <div className="flex items-center justify-between mb-3 px-1">
                        <h2 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
                            <Globe className="h-4 w-4 text-indigo-500" />
                            Fresh Intel
                        </h2>
                        <span className="text-xs font-medium text-indigo-600 cursor-pointer">View All</span>
                    </div>
                    <div className="bg-white rounded-2xl border border-slate-100 shadow-sm divide-y divide-slate-50">
                        {LEADS.map((lead) => (
                            <div key={lead.id} className="p-4 flex items-center justify-between active:bg-slate-50">
                                <div className="flex items-center gap-3">
                                    <div className="h-10 w-10 rounded-full bg-slate-100 flex items-center justify-center text-slate-500">
                                        <Users className="h-5 w-5" />
                                    </div>
                                    <div>
                                        <div className="font-semibold text-sm text-slate-900">{lead.name}</div>
                                        <div className="text-xs text-slate-500 flex items-center gap-1">
                                            {lead.country} • <span className="text-indigo-500">{lead.source}</span>
                                        </div>
                                    </div>
                                </div>
                                <div className="text-xs text-slate-400 font-medium">
                                    {lead.time}
                                </div>
                            </div>
                        ))}
                    </div>
                </section>

                {/* Bottom Padding for Nav */}
                <div className="h-12"></div>
            </div>
        </div>
    );
}
