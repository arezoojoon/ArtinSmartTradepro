"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
    Activity, AlertTriangle, BrainCircuit,
    Globe, Landmark, Radar, Scale, Send, ShoppingCart, 
    Target, TrendingUp, ArrowRight, Zap, Loader2
} from "lucide-react";
import Link from "next/link";
import api from "@/lib/api";

function formatCurrency(val: number): string {
    if (val >= 1_000_000) return `$${(val / 1_000_000).toFixed(1)}M`;
    if (val >= 1_000) return `$${(val / 1_000).toFixed(0)}K`;
    return `$${val.toFixed(0)}`;
}

export default function GlobalCommandCenter() {
    const [data, setData] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchDashboard = async () => {
            try {
                const res = await api.get("/dashboard/main");
                setData(res.data);
            } catch (e) {
                console.error("Dashboard fetch failed:", e);
            } finally {
                setLoading(false);
            }
        };
        fetchDashboard();
    }, []);

    const kpi = data?.kpi_summary || {};
    const pipelineValue = kpi.total_pipeline_value || 0;
    const marginOpps = data?.margin_overview?.length || 0;
    const riskCount = kpi.high_risk_countries || 0;
    const cashHealth = kpi.cash_flow_health || "unknown";
    const riskItems = data?.risk_heatmap || [];
    const margins = data?.margin_overview || [];

    return (
        <div className="min-h-screen bg-[#050A15] text-slate-300 p-4 md:p-8 pt-6 selection:bg-[#D4AF37] selection:text-black space-y-8">
            
            {/* 1. Header & Global Status */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-6 border-b border-[#1E293B] pb-6">
                <div>
                    <div className="flex items-center gap-3 mb-2">
                        <div className="p-2 bg-[#D4AF37]/10 rounded-md border border-[#D4AF37]/30 shadow-[0_0_15px_rgba(212,175,55,0.15)]">
                            <Globe className="h-6 w-6 text-[#D4AF37]" />
                        </div>
                        <h1 className="text-3xl font-bold tracking-tight text-white uppercase">Global Command Center</h1>
                    </div>
                    <p className="text-[#94A3B8] text-sm flex items-center gap-2">
                        <Activity className="w-4 h-4 text-emerald-400" />
                        {loading ? "Loading live data..." : `System Status: ${cashHealth === "positive" ? "Healthy" : "Attention Needed"}. Live data from CRM & Billing.`}
                    </p>
                </div>
                
                <div className="flex items-center gap-3">
                    <Link href="/hunter">
                        <Button className="bg-[#D4AF37] text-[#050A15] hover:bg-[#F3E5AB] font-bold uppercase tracking-wider h-11 shadow-[0_0_20px_rgba(212,175,55,0.3)]">
                            <Radar className="w-5 h-5 mr-2" /> Launch Hunter
                        </Button>
                    </Link>
                </div>
            </div>

            {loading ? (
                <div className="flex items-center justify-center py-20">
                    <Loader2 className="h-8 w-8 animate-spin text-[#D4AF37]" />
                    <span className="ml-3 text-slate-400">Loading dashboard data...</span>
                </div>
            ) : (
            <>
            {/* 2. Executive KPIs — Real Data */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Card className="bg-[#0F172A] border-[#1E293B] hover:border-[#D4AF37]/30 transition-colors">
                    <CardContent className="p-5">
                        <div className="text-[10px] text-[#94A3B8] uppercase tracking-widest mb-1 flex items-center justify-between">
                            Active Pipeline <TrendingUp className="w-3 h-3 text-[#D4AF37]"/>
                        </div>
                        <div className="text-3xl font-bold text-white">{formatCurrency(pipelineValue)}</div>
                        <div className="text-xs text-[#94A3B8] mt-2 font-medium">From CRM Deals</div>
                    </CardContent>
                </Card>
                <Card className="bg-[#0F172A] border-[#1E293B] hover:border-[#D4AF37]/30 transition-colors">
                    <CardContent className="p-5">
                        <div className="text-[10px] text-[#94A3B8] uppercase tracking-widest mb-1 flex items-center justify-between">
                            Active Leads <ShoppingCart className="w-3 h-3 text-blue-400"/>
                        </div>
                        <div className="text-3xl font-bold text-white">{kpi.active_leads ?? 0}</div>
                        <div className="text-xs text-[#94A3B8] mt-2 font-medium">From Hunter</div>
                    </CardContent>
                </Card>
                <Card className="bg-[#0F172A] border-[#1E293B] shadow-[inset_0_-2px_0_rgba(212,175,55,1)]">
                    <CardContent className="p-5">
                        <div className="text-[10px] text-[#94A3B8] uppercase tracking-widest mb-1 flex items-center justify-between">
                            Margin Opportunities <Scale className="w-3 h-3 text-[#D4AF37]"/>
                        </div>
                        <div className="text-3xl font-bold text-[#D4AF37]">{marginOpps}</div>
                        <div className="text-xs text-[#D4AF37]/80 mt-2 font-medium">
                            {kpi.weighted_margin ? `Avg ${kpi.weighted_margin.toFixed(1)}% Margin` : "No data yet"}
                        </div>
                    </CardContent>
                </Card>
                <Card className={`${riskCount > 0 ? "bg-[#450a0a]/20 border-red-900/30" : "bg-[#0F172A] border-[#1E293B]"}`}>
                    <CardContent className="p-5">
                        <div className={`text-[10px] ${riskCount > 0 ? "text-red-400" : "text-emerald-400"} uppercase tracking-widest mb-1 flex items-center justify-between`}>
                            Risk Alerts <AlertTriangle className={`w-3 h-3 ${riskCount > 0 ? "text-red-500" : "text-emerald-500"}`}/>
                        </div>
                        <div className={`text-3xl font-bold ${riskCount > 0 ? "text-red-500" : "text-emerald-400"}`}>{riskCount}</div>
                        <div className={`text-xs ${riskCount > 0 ? "text-red-400/80" : "text-emerald-400/80"} mt-2 font-medium`}>
                            {riskCount > 0 ? "High-Risk Countries" : "All Clear"}
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* 3. Main Dashboard Body */}
            <div className="grid lg:grid-cols-12 gap-8">
                
                {/* LEFT: Intelligence Feed — from real data */}
                <div className="lg:col-span-8 space-y-4">
                    <div className="flex items-center justify-between mb-2">
                        <h3 className="text-lg font-bold text-white uppercase tracking-widest flex items-center gap-2">
                            <BrainCircuit className="h-5 w-5 text-[#D4AF37]" /> Intelligence Feed
                        </h3>
                        <Badge className="bg-[#D4AF37]/10 text-[#D4AF37] border-none font-mono text-[10px] uppercase">Live Data</Badge>
                    </div>

                    {/* Margin Opportunities from real arbitrage data */}
                    {margins.length > 0 ? margins.slice(0, 3).map((m: any, i: number) => (
                        <Card key={i} className="bg-[#0F172A] border-[#1E293B] border-l-4 border-l-[#D4AF37] overflow-hidden">
                            <CardContent className="p-5 flex flex-col md:flex-row gap-4 justify-between items-start md:items-center">
                                <div className="flex gap-4">
                                    <div className="p-3 bg-[#D4AF37]/10 rounded-lg h-fit">
                                        <Scale className="w-6 h-6 text-[#D4AF37]" />
                                    </div>
                                    <div>
                                        <div className="text-[10px] text-[#94A3B8] uppercase tracking-widest mb-1">Arbitrage Opportunity</div>
                                        <h4 className="text-white font-bold text-lg leading-tight">{m.product_key}: {m.buy_market} → {m.sell_market}</h4>
                                        <p className="text-sm text-slate-400 mt-1">
                                            Estimated margin: <strong className="text-[#D4AF37]">{m.estimated_margin_pct?.toFixed(1)}%</strong>
                                            {m.realized_margin_pct != null && <span> · Realized: {m.realized_margin_pct.toFixed(1)}%</span>}
                                            {" · Status: "}{m.status}
                                        </p>
                                    </div>
                                </div>
                                <Link href="/brain">
                                    <Button className="w-full md:w-auto bg-[#D4AF37]/10 text-[#D4AF37] border border-[#D4AF37]/30 hover:bg-[#D4AF37] hover:text-[#050A15] font-bold text-xs uppercase tracking-widest h-10">
                                        Analyze <ArrowRight className="w-4 h-4 ml-2" />
                                    </Button>
                                </Link>
                            </CardContent>
                        </Card>
                    )) : (
                        <Card className="bg-[#0F172A] border-[#1E293B] border-l-4 border-l-emerald-500 overflow-hidden">
                            <CardContent className="p-5 flex gap-4 items-center">
                                <div className="p-3 bg-emerald-500/10 rounded-lg h-fit">
                                    <TrendingUp className="w-6 h-6 text-emerald-400" />
                                </div>
                                <div>
                                    <h4 className="text-white font-bold text-lg leading-tight">No arbitrage opportunities yet</h4>
                                    <p className="text-sm text-slate-400 mt-1">Use the Brain engine to analyze trade routes and discover margin opportunities.</p>
                                </div>
                            </CardContent>
                        </Card>
                    )}

                    {/* Risk Alerts from real data */}
                    {riskItems.filter((r: any) => r.risk_level === "high").slice(0, 2).map((risk: any, i: number) => (
                        <Card key={`risk-${i}`} className="bg-[#0F172A] border-[#1E293B] border-l-4 border-l-red-500 overflow-hidden">
                            <CardContent className="p-5 flex flex-col md:flex-row gap-4 justify-between items-start md:items-center">
                                <div className="flex gap-4">
                                    <div className="p-3 bg-red-500/10 rounded-lg h-fit">
                                        <AlertTriangle className="w-6 h-6 text-red-500" />
                                    </div>
                                    <div>
                                        <div className="text-[10px] text-red-400 uppercase tracking-widest mb-1 flex items-center gap-1">
                                            <Landmark className="w-3 h-3 text-red-400"/> {risk.risk_type} Risk
                                        </div>
                                        <h4 className="text-white font-bold text-lg leading-tight">{risk.country} — {risk.risk_level.toUpperCase()}</h4>
                                        <p className="text-sm text-slate-400 mt-1">{risk.description} (Score: {risk.risk_score})</p>
                                    </div>
                                </div>
                                <Link href="/crm">
                                    <Button variant="outline" className="w-full md:w-auto border-red-900/50 text-red-400 hover:bg-red-900/30 font-bold text-xs uppercase tracking-widest h-10">
                                        Review <ArrowRight className="w-4 h-4 ml-2" />
                                    </Button>
                                </Link>
                            </CardContent>
                        </Card>
                    ))}
                </div>

                {/* RIGHT: Quick Execution Panel */}
                <div className="lg:col-span-4 space-y-6">
                    <Card className="bg-[#0F172A] border-[#1E293B] shadow-2xl relative overflow-hidden h-full">
                        <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-[#D4AF37] to-transparent opacity-50"></div>
                        <CardHeader className="pb-4 border-b border-[#1E293B]">
                            <CardTitle className="text-md font-medium text-white flex items-center gap-2">
                                <Target className="h-4 w-4 text-[#D4AF37]" /> Fast Execution
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="pt-6 space-y-4">
                            <Link href="/sourcing" className="block">
                                <div className="p-4 bg-[#050A15] border border-[#1E293B] rounded-lg cursor-pointer hover:border-[#D4AF37]/50 transition-colors group">
                                    <div className="flex items-center gap-3 mb-2">
                                        <div className="p-1.5 bg-blue-500/10 text-blue-400 rounded">
                                            <Globe className="w-4 h-4" />
                                        </div>
                                        <span className="font-bold text-sm text-white group-hover:text-[#D4AF37] transition-colors">Start New Sourcing Hub</span>
                                    </div>
                                    <p className="text-xs text-slate-500">Deploy AI agents to find verified manufacturers globally.</p>
                                </div>
                            </Link>
                            
                            <Link href="/whatsapp" className="block">
                                <div className="p-4 bg-[#050A15] border border-[#1E293B] rounded-lg cursor-pointer hover:border-[#D4AF37]/50 transition-colors group">
                                    <div className="flex items-center gap-3 mb-2">
                                        <div className="p-1.5 bg-emerald-500/10 text-emerald-400 rounded">
                                            <Send className="w-4 h-4" />
                                        </div>
                                        <span className="font-bold text-sm text-white group-hover:text-[#D4AF37] transition-colors">WhatsApp Broadcast</span>
                                    </div>
                                    <p className="text-xs text-slate-500">Send personalized pitch messages to CRM Leads via WAHA.</p>
                                </div>
                            </Link>

                            <Link href="/toolbox/fx" className="block">
                                <div className="p-4 bg-[#050A15] border border-[#1E293B] rounded-lg cursor-pointer hover:border-[#D4AF37]/50 transition-colors group">
                                    <div className="flex items-center gap-3 mb-2">
                                        <div className="p-1.5 bg-purple-500/10 text-purple-400 rounded">
                                            <Activity className="w-4 h-4" />
                                        </div>
                                        <span className="font-bold text-sm text-white group-hover:text-[#D4AF37] transition-colors">Review Financial Simulator</span>
                                    </div>
                                    <p className="text-xs text-slate-500">Test margin impact of FX changes or freight spikes.</p>
                                </div>
                            </Link>
                        </CardContent>
                    </Card>
                </div>

            </div>
            </>
            )}
        </div>
    );
}
