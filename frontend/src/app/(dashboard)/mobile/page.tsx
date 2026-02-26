"use client";

import React, { useState, useEffect } from "react";
import { InsightCard } from "@/components/dashboard/InsightCard";
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

export default function MobileControlTower() {
    const [isLoading, setIsLoading] = useState(true);
    const [data, setData] = useState<any>(null);

    useEffect(() => {
        const fetchDashboardData = async () => {
            try {
                // Using dynamic import of API to avoid CSR cycle issues if any
                const { api } = await import("@/lib/api");
                const response = await api.get("/dashboard/mobile");
                setData(response.data);
            } catch (error) {
                console.error("Failed to load dashboard data", error);
            } finally {
                setIsLoading(false);
            }
        };
        fetchDashboardData();
    }, []);

    if (isLoading || !data) {
        return <div className="min-h-screen flex items-center justify-center"><div className="animate-pulse flex flex-col items-center gap-3"><Globe className="h-8 w-8 text-indigo-500 animate-spin" /><span className="text-slate-500 font-medium">Fetching secure data...</span></div></div>;
    }

    const { opportunities, risks, shocks, leads, liquidity } = data;

    return (
        <div className="min-h-screen pb-24 pt-safe animate-in fade-in duration-500 font-sans">
            {/* Header */}
            <div className="px-5 py-5 sticky top-0 bg-[#0a1628]/80 backdrop-blur-xl z-40 border-b border-white/10 shadow-sm">
                <div className="flex justify-between items-center">
                    <div>
                        <h1 className="text-2xl font-black tracking-tight text-slate-900 dark:text-white">Control Tower</h1>
                        <p className="text-xs text-slate-500 dark:text-slate-400 font-semibold uppercase tracking-wider flex items-center gap-1 mt-1">
                            <span className="relative flex h-2 w-2">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                            </span>
                            Live Data Feed
                        </p>
                    </div>
                </div>
            </div>

            <div className="p-4 space-y-7">

                {/* 1. Cash Flow Widget (Strict) */}
                <section>
                    <div className="bg-slate-900 rounded-2xl p-5 text-white shadow-xl shadow-slate-900/20 border border-slate-800">
                        <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-2 text-slate-400">
                                <Wallet className="h-4 w-4" />
                                <span className="text-xs font-bold uppercase tracking-wider">Liquidity Snapshot</span>
                            </div>
                            <Badge variant="outline" className="border-slate-700 text-slate-300 text-[10px]">REAL-TIME</Badge>
                        </div>
                        <div className="text-3xl font-black tracking-tighter mb-5 font-mono">$1,240,500<span className="text-slate-500 text-xl">.00</span></div>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-1">
                                <span className="text-[10px] text-slate-400 font-bold tracking-wider uppercase">Pending In (7d)</span>
                                <div className="font-mono text-lg text-emerald-400 flex items-center gap-1">
                                    <ArrowUpRight className="h-3 w-3" /> ${liquidity.pending_in.toLocaleString()}
                                </div>
                            </div>
                            <div className="space-y-1">
                                <span className="text-[10px] text-slate-400 font-bold tracking-wider uppercase">Pending Out (7d)</span>
                                <div className="font-mono text-lg text-rose-400 flex items-center gap-1">
                                    <ArrowDownRight className="h-3 w-3" /> ${liquidity.pending_out.toLocaleString()}
                                </div>
                            </div>
                        </div>
                        <div className="mt-4 pt-4 border-t border-slate-800 flex justify-between items-center">
                            <span className="text-[10px] text-slate-500">Source: {liquidity.source}</span>
                            <span className="text-[10px] text-slate-500">DSO: <span className="text-amber-400 font-bold">{liquidity.dso} Days</span></span>
                        </div>
                    </div>
                </section>

                {/* 2. Today's Opportunities */}
                <section>
                    <div className="flex items-center justify-between mb-4 px-1">
                        <h2 className="text-sm font-black text-slate-900 dark:text-white uppercase tracking-widest flex items-center gap-2">
                            <Zap className="h-4 w-4 text-emerald-500" />
                            Top Opportunities
                        </h2>
                    </div>
                    <div className="space-y-4">
                        {opportunities.map((opp: any) => (
                            <InsightCard
                                key={opp.id}
                                title={opp.title}
                                source={opp.source}
                                timestamp={opp.timestamp}
                                confidence={opp.confidence}
                                actionLabel="Open Deal"
                                onAction={() => window.location.href = '/deals'}
                                isInsufficientData={opp.isInsufficientData}
                            >
                                <p className="text-sm text-slate-600 leading-relaxed">
                                    {opp.description}
                                </p>
                            </InsightCard>
                        ))}
                        {/* Example of Insufficient Data */}
                        <InsightCard
                            title="Soybean Export to China"
                            source="AI Master Brain"
                            timestamp={new Date().toISOString()}
                            confidence={0}
                            isInsufficientData={true}
                        />
                    </div>
                </section>

                {/* 3. Risk Alerts */}
                <section>
                    <div className="flex items-center justify-between mb-4 px-1">
                        <h2 className="text-sm font-black text-slate-900 dark:text-white uppercase tracking-widest flex items-center gap-2">
                            <AlertTriangle className="h-4 w-4 text-rose-500" />
                            Critical Risks
                        </h2>
                    </div>
                    <div className="space-y-4">
                        {risks.map((risk: any) => (
                            <InsightCard
                                key={risk.id}
                                title={risk.title}
                                source={risk.source}
                                timestamp={risk.timestamp}
                                confidence={risk.confidence}
                                actionLabel="Mitigate"
                            >
                                <p className="text-sm text-slate-600 leading-relaxed font-medium">
                                    {risk.description}
                                </p>
                            </InsightCard>
                        ))}
                    </div>
                </section>

                {/* 4. Market Shocks */}
                <section>
                    <div className="flex items-center justify-between mb-4 px-1">
                        <h2 className="text-sm font-black text-slate-900 dark:text-white uppercase tracking-widest flex items-center gap-2">
                            <TrendingUp className="h-4 w-4 text-blue-500" />
                            Market Shocks
                        </h2>
                    </div>
                    <ScrollArea className="w-full whitespace-nowrap pb-4">
                        <div className="flex space-x-3">
                            {shocks.map((shock: any) => (
                                <div key={shock.id} className="inline-flex items-center justify-between space-x-4 bg-white border border-slate-200 rounded-xl p-4 shadow-sm min-w-[200px]">
                                    <div className="flex flex-col">
                                        <span className="text-xs text-slate-500 font-bold uppercase tracking-wider">{shock.asset}</span>
                                        <div className="flex items-center gap-2 mt-1">
                                            <span className={`text-xl font-black ${shock.trend === "up" ? "text-emerald-500" : "text-rose-500"}`}>
                                                {shock.change}
                                            </span>
                                            {shock.trend === "up" ? (
                                                <ArrowUpRight className="h-4 w-4 text-emerald-500" />
                                            ) : (
                                                <ArrowDownRight className="h-4 w-4 text-rose-500" />
                                            )}
                                        </div>
                                        <div className="text-[9px] text-slate-400 mt-2 uppercase tracking-widest">
                                            Source: {shock.source} • {shock.confidence}% Conf
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </ScrollArea>
                </section>

                {/* 5. New Leads */}
                <section>
                    <div className="flex items-center justify-between mb-4 px-1">
                        <h2 className="text-sm font-black text-slate-900 dark:text-white uppercase tracking-widest flex items-center gap-2">
                            <Users className="h-4 w-4 text-indigo-500" />
                            Latest Scored Leads
                        </h2>
                    </div>
                    <div className="space-y-4">
                        {leads.map((lead: any) => (
                            <InsightCard
                                key={lead.id}
                                title={lead.title}
                                source={lead.source}
                                timestamp={lead.timestamp}
                                confidence={lead.confidence}
                                actionLabel="View Profile"
                                onAction={() => window.location.href = '/crm/companies'}
                            >
                                <p className="text-sm text-slate-600 leading-relaxed">
                                    {lead.description}
                                </p>
                            </InsightCard>
                        ))}
                    </div>
                </section>

                {/* Bottom Padding for Nav */}
                <div className="h-16"></div>
            </div>
        </div>
    );
}
