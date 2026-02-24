"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
    Activity, AlertTriangle, BrainCircuit, CloudLightning, 
    Globe, Landmark, Radar, Scale, Send, ShoppingCart, 
    Target, TrendingUp, ArrowRight, Zap
} from "lucide-react";
import Link from "next/link";

export default function GlobalCommandCenter() {
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
                        System Status: Optimal. AI Engines monitoring 4 active global markets.
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

            {/* 2. Executive KPIs */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Card className="bg-[#0F172A] border-[#1E293B] hover:border-[#D4AF37]/30 transition-colors">
                    <CardContent className="p-5">
                        <div className="text-[10px] text-[#94A3B8] uppercase tracking-widest mb-1 flex items-center justify-between">
                            Active Pipeline <TrendingUp className="w-3 h-3 text-[#D4AF37]"/>
                        </div>
                        <div className="text-3xl font-bold text-white">$4.2M</div>
                        <div className="text-xs text-emerald-400 mt-2 font-medium">+12% vs Last Month</div>
                    </CardContent>
                </Card>
                <Card className="bg-[#0F172A] border-[#1E293B] hover:border-[#D4AF37]/30 transition-colors">
                    <CardContent className="p-5">
                        <div className="text-[10px] text-[#94A3B8] uppercase tracking-widest mb-1 flex items-center justify-between">
                            Pending RFQs <ShoppingCart className="w-3 h-3 text-blue-400"/>
                        </div>
                        <div className="text-3xl font-bold text-white">8</div>
                        <div className="text-xs text-[#94A3B8] mt-2 font-medium">3 Awaiting Supplier Response</div>
                    </CardContent>
                </Card>
                <Card className="bg-[#0F172A] border-[#1E293B] shadow-[inset_0_-2px_0_rgba(212,175,55,1)]">
                    <CardContent className="p-5">
                        <div className="text-[10px] text-[#94A3B8] uppercase tracking-widest mb-1 flex items-center justify-between">
                            AI Arbitrage Opps <Scale className="w-3 h-3 text-[#D4AF37]"/>
                        </div>
                        <div className="text-3xl font-bold text-[#D4AF37]">14</div>
                        <div className="text-xs text-[#D4AF37]/80 mt-2 font-medium">High Margin Spread Detected</div>
                    </CardContent>
                </Card>
                <Card className="bg-[#450a0a]/20 border-red-900/30">
                    <CardContent className="p-5">
                        <div className="text-[10px] text-red-400 uppercase tracking-widest mb-1 flex items-center justify-between">
                            Critical Risks <AlertTriangle className="w-3 h-3 text-red-500"/>
                        </div>
                        <div className="text-3xl font-bold text-red-500">2</div>
                        <div className="text-xs text-red-400/80 mt-2 font-medium">Logistics & Sanctions Alerts</div>
                    </CardContent>
                </Card>
            </div>

            {/* 3. Main Dashboard Body */}
            <div className="grid lg:grid-cols-12 gap-8">
                
                {/* LEFT: Strategic Intelligence Feed (The "Brain" Output) */}
                <div className="lg:col-span-8 space-y-4">
                    <div className="flex items-center justify-between mb-2">
                        <h3 className="text-lg font-bold text-white uppercase tracking-widest flex items-center gap-2">
                            <BrainCircuit className="h-5 w-5 text-[#D4AF37]" /> Live Intelligence Feed
                        </h3>
                        <Badge className="bg-[#D4AF37]/10 text-[#D4AF37] border-none font-mono text-[10px] uppercase">Auto-Refreshing</Badge>
                    </div>

                    {/* Alert 1: Demand Engine (Stockout) */}
                    <Card className="bg-[#0F172A] border-[#1E293B] border-l-4 border-l-emerald-500 overflow-hidden">
                        <CardContent className="p-5 flex flex-col md:flex-row gap-4 justify-between items-start md:items-center">
                            <div className="flex gap-4">
                                <div className="p-3 bg-emerald-500/10 rounded-lg h-fit">
                                    <TrendingUp className="w-6 h-6 text-emerald-400" />
                                </div>
                                <div>
                                    <div className="text-[10px] text-[#94A3B8] uppercase tracking-widest mb-1 flex items-center gap-1">
                                        <Zap className="w-3 h-3 text-emerald-400"/> Demand Engine Predicts Stockout
                                    </div>
                                    <h4 className="text-white font-bold text-lg leading-tight">Pre-Ramadan FMCG Demand Spike (GCC)</h4>
                                    <p className="text-sm text-slate-400 mt-1">Historical patterns indicate buyers in UAE & KSA will begin urgent restocking of dry foods in 14 days.</p>
                                </div>
                            </div>
                            <Link href="/crm/campaigns">
                                <Button className="w-full md:w-auto bg-[#D4AF37]/10 text-[#D4AF37] border border-[#D4AF37]/30 hover:bg-[#D4AF37] hover:text-[#050A15] font-bold text-xs uppercase tracking-widest h-10">
                                    Launch WAHA Campaign <Send className="w-4 h-4 ml-2" />
                                </Button>
                            </Link>
                        </CardContent>
                    </Card>

                    {/* Alert 2: Arbitrage Engine (High Margin) */}
                    <Card className="bg-[#0F172A] border-[#1E293B] border-l-4 border-l-[#D4AF37] overflow-hidden">
                        <CardContent className="p-5 flex flex-col md:flex-row gap-4 justify-between items-start md:items-center">
                            <div className="flex gap-4">
                                <div className="p-3 bg-[#D4AF37]/10 rounded-lg h-fit">
                                    <Scale className="w-6 h-6 text-[#D4AF37]" />
                                </div>
                                <div>
                                    <div className="text-[10px] text-[#94A3B8] uppercase tracking-widest mb-1">Arbitrage Opportunity Detected</div>
                                    <h4 className="text-white font-bold text-lg leading-tight">Copper Cathodes: TR → AE Spread</h4>
                                    <p className="text-sm text-slate-400 mt-1">FOB prices dropped in Mersin. Estimated Risk-Adjusted Margin is now <strong className="text-[#D4AF37]">22.4%</strong> (after freight & tariffs).</p>
                                </div>
                            </div>
                            <Link href="/sourcing/rfqs">
                                <Button className="w-full md:w-auto bg-[#D4AF37]/10 text-[#D4AF37] border border-[#D4AF37]/30 hover:bg-[#D4AF37] hover:text-[#050A15] font-bold text-xs uppercase tracking-widest h-10">
                                    Draft Supplier RFQ <ArrowRight className="w-4 h-4 ml-2" />
                                </Button>
                            </Link>
                        </CardContent>
                    </Card>

                    {/* Alert 3: Cultural/Risk Engine */}
                    <Card className="bg-[#0F172A] border-[#1E293B] border-l-4 border-l-red-500 overflow-hidden">
                        <CardContent className="p-5 flex flex-col md:flex-row gap-4 justify-between items-start md:items-center">
                            <div className="flex gap-4">
                                <div className="p-3 bg-red-500/10 rounded-lg h-fit">
                                    <AlertTriangle className="w-6 h-6 text-red-500" />
                                </div>
                                <div>
                                    <div className="text-[10px] text-red-400 uppercase tracking-widest mb-1 flex items-center gap-1">
                                        <Landmark className="w-3 h-3 text-red-400"/> Risk & Cultural Engine Warning
                                    </div>
                                    <h4 className="text-white font-bold text-lg leading-tight">Liquidity Risk in Target Market (EG)</h4>
                                    <p className="text-sm text-slate-400 mt-1">Severe USD shortage flagged. Cultural playbook advises strict adherence to TT Advance. Do not offer OA terms.</p>
                                </div>
                            </div>
                            <Link href="/crm">
                                <Button variant="outline" className="w-full md:w-auto border-red-900/50 text-red-400 hover:bg-red-900/30 font-bold text-xs uppercase tracking-widest h-10">
                                    Update CRM Deal <ArrowRight className="w-4 h-4 ml-2" />
                                </Button>
                            </Link>
                        </CardContent>
                    </Card>
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
                            
                            <Link href="/crm/campaigns" className="block">
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
        </div>
    );
}
