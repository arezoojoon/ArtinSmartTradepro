"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
    Briefcase, Target, PhoneCall, AlertCircle, TrendingUp,
    ShoppingCart, Factory, Clock, CheckCircle2, MessageCircle, Mail, ChevronRight, Zap
} from "lucide-react";
import Link from "next/link";

export default function CRMOverviewPage() {
    const [activeRole, setActiveRole] = useState("manager");

    return (
        <div className="space-y-8 max-w-[1400px] mx-auto p-4 md:p-8 pt-6 min-h-screen">
            {/* Header Section */}
            <div className="flex flex-col md:flex-row md:justify-between md:items-end gap-6 border-b border-white/10 pb-6">
                <div>
                    <div className="flex items-center gap-3 mb-2">
                        <div className="p-2 bg-[#f5a623]/10 rounded-lg border border-[#f5a623]/20 backdrop-blur-md">
                            <Briefcase className="h-6 w-6 text-[#f5a623]" />
                        </div>
                        <h2 className="text-3xl font-bold tracking-tight text-white">Execution Hub</h2>
                    </div>
                    <p className="text-slate-400 text-sm">Role-based CRM terminal for global trade execution.</p>
                </div>
            </div>

            {/* Premium Role Switcher */}
            <Tabs defaultValue="manager" onValueChange={setActiveRole} className="w-full">
                <div className="flex justify-center mb-8">
                    <TabsList className="grid grid-cols-3 h-14 bg-[#12253f]/80 backdrop-blur-xl border border-[#1e3a5f] hover:border-[#f5a623]/30">
                        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-[#f5a623]/5 to-transparent"></div>
                        <TabsTrigger value="manager" className="rounded-lg font-bold data-[state=active]:bg-[#f5a623] data-[state=active]:text-black data-[state=active]:shadow-[0_0_20px_rgba(245,166,35,0.3)] transition-all z-10 text-slate-400">
                            Trade Manager
                        </TabsTrigger>
                        <TabsTrigger value="sales" className="rounded-lg font-bold data-[state=active]:bg-[#f5a623] data-[state=active]:text-black data-[state=active]:shadow-[0_0_20px_rgba(245,166,35,0.3)] transition-all z-10 text-slate-400">
                            Sales Agent
                        </TabsTrigger>
                        <TabsTrigger value="sourcing" className="rounded-lg font-bold data-[state=active]:bg-[#f5a623] data-[state=active]:text-black data-[state=active]:shadow-[0_0_20px_rgba(245,166,35,0.3)] transition-all z-10 text-slate-400">
                            Sourcing Agent
                        </TabsTrigger>
                    </TabsList>
                </div>

                {/* ========================================== */}
                {/* 1. TRADE MANAGER VIEW */}
                {/* ========================================== */}
                <TabsContent value="manager" className="space-y-8 animate-in fade-in slide-in-from-bottom-8 duration-700">
                    <div className="grid gap-6 md:grid-cols-4">
                        <Card className="bg-[#12253f]/80 backdrop-blur-xl border border-[#1e3a5f] hover:border-[#f5a623]/30 transition-all">
                            <CardHeader className="flex flex-row items-center justify-between pb-2">
                                <CardTitle className="text-xs font-bold text-slate-400 uppercase tracking-wider">Total Pipeline</CardTitle>
                                <TrendingUp className="h-4 w-4 text-[#f5a623]" />
                            </CardHeader>
                            <CardContent>
                                <div className="text-2xl font-bold text-white">$2.4M</div>
                                <p className="text-[10px] text-emerald-400 font-bold mt-1 uppercase">+14.2% Mapped Yield</p>
                            </CardContent>
                        </Card>
                        <Card className="bg-[#12253f]/80 backdrop-blur-xl border border-[#1e3a5f] hover:border-[#f5a623]/30 transition-all">
                            <CardHeader className="flex flex-row items-center justify-between pb-2">
                                <CardTitle className="text-xs font-bold text-slate-400 uppercase tracking-wider">Active Deals</CardTitle>
                                <Briefcase className="h-4 w-4 text-blue-400" />
                            </CardHeader>
                            <CardContent>
                                <div className="text-2xl font-bold text-white">42</div>
                                <p className="text-[10px] text-slate-500 mt-1 uppercase">12 Pending Signature</p>
                            </CardContent>
                        </Card>
                        <Card className="bg-[#12253f]/80 backdrop-blur-xl border border-[#1e3a5f] hover:border-[#f5a623]/30 transition-all">
                            <CardHeader className="flex flex-row items-center justify-between pb-2">
                                <CardTitle className="text-xs font-bold text-slate-400 uppercase tracking-wider">Open RFQs</CardTitle>
                                <ShoppingCart className="h-4 w-4 text-emerald-400" />
                            </CardHeader>
                            <CardContent>
                                <div className="text-2xl font-bold text-white">8</div>
                                <p className="text-[10px] text-orange-400 mt-1 uppercase">3 Awaiting Supplier</p>
                            </CardContent>
                        </Card>
                        <Card className="bg-[#12253f]/80 backdrop-blur-xl border-red-500/20 bg-red-500/5 group hover:border-red-500/40 transition-all">
                            <CardHeader className="flex flex-row items-center justify-between pb-2">
                                <CardTitle className="text-xs font-bold text-red-400 uppercase tracking-wider">SLA Breaches</CardTitle>
                                <AlertCircle className="h-4 w-4 text-red-500" />
                            </CardHeader>
                            <CardContent>
                                <div className="text-2xl font-bold text-red-400">3</div>
                                <p className="text-[10px] text-red-500/70 mt-1 uppercase italic underline">Action Required Immediately</p>
                            </CardContent>
                        </Card>
                    </div>

                    <div className="grid md:grid-cols-2 gap-8">
                        {/* Funnel */}
                        <Card className="bg-[#12253f]/80 backdrop-blur-2xl border border-[#1e3a5f] shadow-2xlative overflow-hidden">
                            <div className="h-[2px] w-full bg-gradient-to-r from-transparent via-[#f5a623] to-transparent opacity-20"></div>
                            <CardHeader>
                                <CardTitle className="text-white text-lg flex items-center gap-2">
                                    <Target className="h-5 w-5 text-[#f5a623]" /> Conversion Intelligence
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-6">
                                <div className="space-y-2">
                                    <div className="flex justify-between text-[11px] uppercase font-bold tracking-widest text-slate-400">
                                        <span>Inbound Discovery</span>
                                        <span className="text-white">1,250</span>
                                    </div>
                                    <Progress value={100} className="h-2 bg-white/5 [&>div]:bg-slate-600 rounded-none" />
                                </div>
                                <div className="space-y-2">
                                    <div className="flex justify-between text-[11px] uppercase font-bold tracking-widest text-slate-400">
                                        <span>Engagement</span>
                                        <span className="text-white">480</span>
                                    </div>
                                    <Progress value={38} className="h-2 bg-white/5 [&>div]:bg-[#f5a623]/40 rounded-none" />
                                </div>
                                <div className="space-y-2">
                                    <div className="flex justify-between text-[11px] uppercase font-bold tracking-widest text-slate-400">
                                        <span>Negotiation</span>
                                        <span className="text-white">112</span>
                                    </div>
                                    <Progress value={15} className="h-2 bg-white/5 [&>div]:bg-[#f5a623]/70 rounded-none" />
                                </div>
                                <div className="space-y-2">
                                    <div className="flex justify-between text-[11px] uppercase font-bold tracking-widest text-[#f5a623]">
                                        <span>Won Deals</span>
                                        <span className="text-[#f5a623]">24</span>
                                    </div>
                                    <Progress value={5} className="h-2 bg-white/5 [&>div]:bg-[#f5a623] rounded-none shadow-[0_0_10px_rgba(212,175,55,0.4)]" />
                                </div>
                            </CardContent>
                        </Card>

                        {/* Action Terminal */}
                        <Card className="bg-[#050a15]/60 backdrop-blur-xl border border-white/10">
                            <CardHeader>
                                <CardTitle className="text-white text-lg flex items-center gap-2">
                                    <Zap className="h-5 w-5 text-[#f5a623]" /> Manager Action Terminal
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="flex items-start gap-4 p-4 bg-red-500/5 rounded-xl border border-red-500/20">
                                    <AlertCircle className="h-5 w-5 text-red-500 mt-1" />
                                    <div>
                                        <p className="text-sm font-bold text-red-400">High-Value Lead Stalled</p>
                                        <p className="text-[11px] text-slate-500 mt-1">Carrefour UAE lead (Tier 1) has no CRM entry for 72h.</p>
                                        <Button size="sm" className="mt-4 h-8 bg-red-500/20 text-red-400 border border-red-500/30 hover:bg-red-500/30 font-bold text-[10px] uppercase tracking-widest">Reassign Agent</Button>
                                    </div>
                                </div>
                                <div className="flex items-start gap-4 p-4 bg-white/5 rounded-xl border border-white/10 group hover:border-[#f5a623]/30 transition-all">
                                    <Clock className="h-5 w-5 text-[#f5a623] mt-1" />
                                    <div>
                                        <p className="text-sm font-bold text-white group-hover:text-[#f5a623]">Quote Expiration Alert</p>
                                        <p className="text-[11px] text-slate-500 mt-1">Supplier 'Zar Macaron' price validity expires <span className="text-[#f5a623]">today</span>.</p>
                                        <Button size="sm" className="mt-4 h-8 bg-black/40 text-slate-300 border border-white/10 hover:border-[#f5a623] font-bold text-[10px] uppercase tracking-widest">Ping Sourcing Team</Button>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                </TabsContent>

                {/* ========================================== */}
                {/* 2. SALES AGENT VIEW */}
                {/* ========================================== */}
                <TabsContent value="sales" className="space-y-8 animate-in fade-in slide-in-from-bottom-8 duration-700">
                    <div className="flex items-center gap-6">
                        <Link href="/crm/pipelines" className="flex-1">
                            <Button className="w-full bg-[#f5a623] text-black hover:bg-white h-14 font-extrabold text-base shadow-[0_0_20px_rgba(245,166,35,0.2)]">
                                <Target className="mr-2 h-5 w-5" /> Sales Kanban Board
                            </Button>
                        </Link>
                        <Link href="/crm/campaigns" className="flex-1">
                            <Button variant="outline" className="w-full border-[#1e3a5f] bg-[#12253f]/60 text-white hover:bg-[#f5a623] hover:text-black h-14 font-bold text-base transition-all">
                                <MessageCircle className="mr-2 h-5 w-5" /> WhatsApp Campaigns
                            </Button>
                        </Link>
                    </div>

                    <Card className="bg-[#050a15]/60 backdrop-blur-xl border border-white/10">
                        <CardHeader>
                            <CardTitle className="text-white text-lg flex items-center gap-2">
                                <Clock className="h-5 w-5 text-[#f5a623]" /> Active Daily Pursuit
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4">
                                <div className="flex items-center justify-between p-4 bg-white/5 rounded-xl border border-white/5 group hover:border-[#f5a623]/30 transition-all">
                                    <div className="flex items-center gap-4">
                                        <div className="p-3 bg-[#050a15]/60 border border-white/10 shadow-inner">
                                            <PhoneCall className="h-5 w-5" />
                                        </div>
                                        <div>
                                            <p className="text-sm font-bold text-white group-hover:text-[#f5a623] transition-colors">Spinneys - Procurement Director</p>
                                            <p className="text-[11px] text-slate-500 uppercase font-medium tracking-tight mt-1">Discuss pricing for Q3 Pasta shipment</p>
                                        </div>
                                    </div>
                                    <Badge className="bg-[#f5a623]/10 text-[#f5a623] border border-[#f5a623]/20 py-1.5 px-3 font-bold text-[10px] tracking-widest">14:00 GST</Badge>
                                </div>
                                <div className="flex items-center justify-between p-4 bg-white/5 rounded-xl border border-white/5 group hover:border-[#f5a623]/30 transition-all">
                                    <div className="flex items-center gap-4">
                                        <div className="p-3 bg-black/50 border border-white/10 text-emerald-400 rounded-xl shadow-inner">
                                            <Mail className="h-5 w-5" />
                                        </div>
                                        <div>
                                            <p className="text-sm font-bold text-white group-hover:text-[#f5a623] transition-colors">Lulu Hypermarket - Proforma</p>
                                            <p className="text-[11px] text-slate-500 uppercase font-medium tracking-tight mt-1">Export Documentation for 2 Containers</p>
                                        </div>
                                    </div>
                                    <Badge className="bg-emerald-500/10 text-emerald-400 border-emerald-500/20 py-1.5 px-3 font-bold text-[10px] tracking-widest">PRIORITY 1</Badge>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>

                {/* ========================================== */}
                {/* 3. SOURCING AGENT VIEW */}
                {/* ========================================== */}
                <TabsContent value="sourcing" className="space-y-8 animate-in fade-in slide-in-from-bottom-8 duration-700">
                    <div className="flex items-center gap-6">
                        <Link href="/sourcing/rfqs" className="flex-1">
                            <Button className="w-full bg-[#f5a623] text-black hover:bg-white h-14 font-extrabold text-base shadow-[0_0_20px_rgba(245,166,35,0.2)]">
                                <ShoppingCart className="mr-2 h-5 w-5" /> Negotiation Hub
                            </Button>
                        </Link>
                        <Link href="/hunter" className="flex-1">
                            <Button variant="outline" className="w-full border-[#1e3a5f] bg-[#12253f]/60 text-white hover:bg-[#f5a623] hover:text-black h-14 font-bold text-base transition-all">
                                <Factory className="mr-2 h-5 w-5" /> Deep Hunter Scan
                            </Button>
                        </Link>
                    </div>

                    <Card className="bg-[#050a15]/60 backdrop-blur-xl border border-white/10">
                        <CardHeader>
                            <CardTitle className="text-white text-lg flex items-center gap-2">
                                <Factory className="h-5 w-5 text-[#f5a623]" /> Global Supply Pipeline
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-6">
                                <div className="border border-white/10 rounded-2xl p-6 bg-white/5 hover:border-[#f5a623]/30 transition-all relative overflow-hidden group">
                                    <div className="absolute top-0 right-0 p-1">
                                        <div className="text-[8px] font-bold text-white/20 uppercase tracking-[0.2em] rotate-90 origin-right">Negotiation Stage</div>
                                    </div>
                                    <div className="flex justify-between items-start mb-6">
                                        <div>
                                            <h4 className="font-extrabold text-white text-lg group-hover:text-[#f5a623] transition-colors">RFQ-2026-088: Copper Cathodes</h4>
                                            <p className="text-[11px] text-slate-500 mt-1 uppercase font-semibold">500 MT • Origin: Zambia • Destination: Jebel Ali</p>
                                        </div>
                                        <Badge className="bg-blue-500/10 text-blue-400 border border-blue-500/20 px-3 py-1 font-bold text-[10px]">LIVE BIDS</Badge>
                                    </div>
                                    <div className="grid grid-cols-3 gap-4">
                                        <div className="bg-black/40 border border-white/5 p-4 rounded-xl text-center">
                                            <div className="text-slate-500 text-[10px] uppercase font-bold mb-1">Suppliers</div>
                                            <div className="font-bold text-white text-xl">12</div>
                                        </div>
                                        <div className="bg-black/40 border border-[#f5a623]/20 p-4 rounded-xl text-center shadow-[inset_0_0_15px_rgba(212,175,55,0.05)]">
                                            <div className="text-[#f5a623] text-[10px] uppercase font-bold mb-1">Quotes</div>
                                            <div className="font-bold text-[#f5a623] text-xl">4</div>
                                        </div>
                                        <div className="bg-black/40 border border-white/5 p-4 rounded-xl text-center">
                                            <div className="text-slate-500 text-[10px] uppercase font-bold mb-1">Best FOB</div>
                                            <div className="font-bold text-white text-xl">$8,200</div>
                                        </div>
                                    </div>
                                    <Button variant="ghost" className="w-full mt-6 text-[#f5a623] hover:bg-[#f5a623] hover:text-black font-bold uppercase tracking-widest text-[10px]">Analyze Quotes History &rarr;</Button>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>
    );
}
