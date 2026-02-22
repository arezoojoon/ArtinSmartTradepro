import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertTriangle, TrendingUp, DollarSign, Users, Activity, Target, Zap, ShieldCheck, ChevronRight } from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';

export default function DashboardPage() {
    return (
        <div className="flex-1 space-y-8 p-4 md:p-8 pt-6 min-h-screen">
            {/* Header Section */}
            <div className="flex flex-col md:flex-row md:justify-between md:items-end gap-6 border-b border-white/10 pb-6">
                <div>
                    <div className="flex items-center gap-3 mb-2">
                        <div className="p-2 bg-[#D4AF37]/10 rounded-lg border border-[#D4AF37]/20 backdrop-blur-md">
                            <Zap className="h-6 w-6 text-[#D4AF37]" />
                        </div>
                        <h2 className="text-3xl font-bold tracking-tight text-white">Control Tower</h2>
                    </div>
                    <p className="text-slate-400 text-sm">Real-time operational intelligence and global trade oversight.</p>
                </div>

                <div className="flex items-center gap-3 bg-black/40 backdrop-blur-md px-4 py-2 rounded-lg border border-white/5">
                    <div className="h-2 w-2 rounded-full bg-[#D4AF37] animate-pulse"></div>
                    <span className="text-xs font-medium text-slate-300 uppercase tracking-widest text-[#D4AF37]">Market Mode: Active</span>
                </div>
            </div>

            {/* Critical Metrics Grid */}
            <div className="grid gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-5">

                {/* 1. Opportunities */}
                <Card className="bg-black/40 backdrop-blur-xl border border-white/10 hover:border-[#D4AF37]/30 transition-all group overflow-hidden relative">
                    <div className="absolute top-0 left-0 w-1 h-full bg-[#D4AF37] opacity-50"></div>
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                        <CardTitle className="text-xs font-bold text-slate-400 uppercase tracking-wider">Opportunities</CardTitle>
                        <TrendingUp className="h-4 w-4 text-[#D4AF37]" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white group-hover:text-[#D4AF37] transition-colors">3 High Margin</div>
                        <p className="text-[10px] text-slate-500 mt-1 uppercase">UAE to EU • 18% Est. Margin</p>
                        <Link href="/brain" className="text-xs text-[#D4AF37] hover:text-white transition-colors mt-4 flex items-center gap-1 font-bold">
                            Review in Brain <ChevronRight className="h-3 w-3" />
                        </Link>
                    </CardContent>
                </Card>

                {/* 2. Risk Alerts */}
                <Card className="bg-black/40 backdrop-blur-xl border border-white/10 hover:border-red-500/30 transition-all group overflow-hidden relative">
                    <div className="absolute top-0 left-0 w-1 h-full bg-red-500 opacity-50"></div>
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                        <CardTitle className="text-xs font-bold text-slate-400 uppercase tracking-wider">Risk Alerts</CardTitle>
                        <AlertTriangle className="h-4 w-4 text-red-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white group-hover:text-red-400 transition-colors">2 Critical</div>
                        <p className="text-[10px] text-slate-500 mt-1 uppercase">Port Delays & Customs Flags</p>
                        <Link href="/settings/notifications" className="text-xs text-red-400 hover:text-white transition-colors mt-4 flex items-center gap-1 font-bold">
                            Take Action <ChevronRight className="h-3 w-3" />
                        </Link>
                    </CardContent>
                </Card>

                {/* 3. Cash Flow */}
                <Card className="bg-black/40 backdrop-blur-xl border border-white/10 hover:border-emerald-500/30 transition-all group overflow-hidden relative">
                    <div className="absolute top-0 left-0 w-1 h-full bg-emerald-500 opacity-50"></div>
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                        <CardTitle className="text-xs font-bold text-slate-400 uppercase tracking-wider">Cash Flow</CardTitle>
                        <DollarSign className="h-4 w-4 text-emerald-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white group-hover:text-emerald-400 transition-colors">$124,500</div>
                        <p className="text-[10px] text-slate-500 mt-1 uppercase">In 7 Days (DSO: 42d)</p>
                        <Link href="/wallet" className="text-xs text-emerald-400 hover:text-white transition-colors mt-4 flex items-center gap-1 font-bold">
                            View Wallet <ChevronRight className="h-3 w-3" />
                        </Link>
                    </CardContent>
                </Card>

                {/* 4. New Leads */}
                <Card className="bg-black/40 backdrop-blur-xl border border-white/10 hover:border-purple-500/30 transition-all group overflow-hidden relative">
                    <div className="absolute top-0 left-0 w-1 h-full bg-purple-500 opacity-50"></div>
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                        <CardTitle className="text-xs font-bold text-slate-400 uppercase tracking-wider">New Leads</CardTitle>
                        <Users className="h-4 w-4 text-purple-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white group-hover:text-purple-400 transition-colors">12 Qualified</div>
                        <p className="text-[10px] text-slate-500 mt-1 uppercase">Hunter Score &gt; 80</p>
                        <Link href="/crm" className="text-xs text-purple-400 hover:text-white transition-colors mt-4 flex items-center gap-1 font-bold">
                            Open CRM <ChevronRight className="h-3 w-3" />
                        </Link>
                    </CardContent>
                </Card>

                {/* 5. Market Shocks */}
                <Card className="bg-black/40 backdrop-blur-xl border border-white/10 hover:border-orange-500/30 transition-all group overflow-hidden relative">
                    <div className="absolute top-0 left-0 w-1 h-full bg-orange-500 opacity-50"></div>
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                        <CardTitle className="text-xs font-bold text-slate-400 uppercase tracking-wider">Market Shocks</CardTitle>
                        <Activity className="h-4 w-4 text-orange-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white group-hover:text-orange-400 transition-colors">+2.4% FX</div>
                        <p className="text-[10px] text-slate-500 mt-1 uppercase">AED/USD Volatility</p>
                        <Link href="/toolbox/fx" className="text-xs text-orange-400 hover:text-white transition-colors mt-4 flex items-center gap-1 font-bold">
                            Analyze <ChevronRight className="h-3 w-3" />
                        </Link>
                    </CardContent>
                </Card>
            </div>

            {/* Detailed Insights Section */}
            <div className="grid gap-6 lg:grid-cols-7 mt-8">

                {/* Pipeline Summary (Bloomberg Style) */}
                <Card className="col-span-full lg:col-span-4 bg-black/40 backdrop-blur-2xl border border-white/10 shadow-2xl overflow-hidden relative">
                    <div className="h-[2px] w-full bg-gradient-to-r from-transparent via-[#D4AF37] to-transparent opacity-30"></div>
                    <CardHeader>
                        <CardTitle className="text-white text-lg flex items-center gap-2">
                            <Target className="h-5 w-5 text-[#D4AF37]" /> Pipeline Intelligence Summary
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-8">
                            <div className="flex items-center justify-between">
                                <span className="text-sm font-semibold text-slate-400 uppercase tracking-widest">Global Conversion Rate</span>
                                <span className="text-xl font-bold text-[#D4AF37]">24.8%</span>
                            </div>

                            <div className="space-y-2">
                                <div className="w-full bg-white/5 rounded-full h-8 relative overflow-hidden flex border border-white/5">
                                    <div className="bg-white/20 h-full flex items-center justify-center text-[10px] text-white font-bold border-r border-white/10" style={{ width: '40%' }}>Leads</div>
                                    <div className="bg-[#D4AF37]/40 h-full flex items-center justify-center text-[10px] text-white font-bold border-r border-white/10" style={{ width: '30%' }}>Quoted</div>
                                    <div className="bg-[#D4AF37] h-full flex items-center justify-center text-[10px] text-black font-bold" style={{ width: '30%' }}>Won</div>
                                </div>
                                <div className="flex justify-between px-1 text-[10px] text-slate-500 uppercase font-bold tracking-tighter">
                                    <span>Inbound Discovery</span>
                                    <span>Negotiation</span>
                                    <span>Deployment</span>
                                </div>
                            </div>

                            <div className="grid grid-cols-3 gap-4 text-center">
                                <div className="p-4 bg-white/5 rounded-xl border border-white/5 group hover:border-[#D4AF37]/20 transition-all">
                                    <p className="text-[10px] text-slate-500 uppercase font-bold mb-1">Total Pipeline</p>
                                    <p className="text-xl font-bold text-white group-hover:text-[#D4AF37] transición-colors">$850,000</p>
                                </div>
                                <div className="p-4 bg-white/5 rounded-xl border border-white/5 group hover:border-[#D4AF37]/20 transition-all">
                                    <p className="text-[10px] text-slate-500 uppercase font-bold mb-1">Gross Margin</p>
                                    <p className="text-xl font-bold text-white group-hover:text-[#D4AF37] transición-colors">18.5%</p>
                                </div>
                                <div className="p-4 bg-white/5 rounded-xl border border-white/5 group hover:border-[#D4AF37]/20 transition-all">
                                    <p className="text-[10px] text-slate-500 uppercase font-bold mb-1">Active Deals</p>
                                    <p className="text-xl font-bold text-white group-hover:text-[#D4AF37] transición-colors">24</p>
                                </div>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Risk Heatmap (Terminal Style) */}
                <Card className="col-span-full lg:col-span-3 bg-black/40 backdrop-blur-2xl border border-white/10 shadow-2xl relative">
                    <CardHeader>
                        <CardTitle className="text-white text-lg flex items-center gap-2">
                            <ShieldCheck className="h-5 w-5 text-red-500" /> AI Risk Terminal
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="flex items-center justify-between p-4 bg-red-500/5 rounded-xl border border-red-500/20 group hover:border-red-500/40 transition-all">
                            <div className="flex gap-3 items-start">
                                <div className="w-2 h-2 rounded-full bg-red-500 mt-1.5 animate-pulse"></div>
                                <div>
                                    <span className="block text-sm font-bold text-red-400">Customs Alert (Turkey)</span>
                                    <span className="block text-[11px] text-slate-500 mt-0.5">HS Code mismatch detected in recent exports.</span>
                                </div>
                            </div>
                            <Badge className="bg-red-500/20 text-red-400 border-red-500/30 text-[10px]">CRITICAL</Badge>
                        </div>

                        <div className="flex items-center justify-between p-4 bg-orange-500/5 rounded-xl border border-orange-500/20 group hover:border-orange-500/40 transition-all">
                            <div className="flex gap-3 items-start">
                                <div className="w-2 h-2 rounded-full bg-orange-500 mt-1.5"></div>
                                <div>
                                    <span className="block text-sm font-bold text-orange-400">Supplier Delay (CN)</span>
                                    <span className="block text-[11px] text-slate-500 mt-0.5">Reliability score dropped by 4%.</span>
                                </div>
                            </div>
                            <Badge className="bg-orange-500/20 text-orange-400 border-orange-500/30 text-[10px]">MEDIUM</Badge>
                        </div>

                        <div className="flex items-center justify-between p-4 bg-emerald-500/5 rounded-xl border border-emerald-500/20 group hover:border-emerald-500/40 transition-all">
                            <div className="flex gap-3 items-start">
                                <div className="w-2 h-2 rounded-full bg-emerald-500 mt-1.5"></div>
                                <div>
                                    <span className="block text-sm font-bold text-emerald-400">Buyer Behavior (AE)</span>
                                    <span className="block text-[11px] text-slate-500 mt-0.5">Payment on-time rate &gt; 95%.</span>
                                </div>
                            </div>
                            <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30 text-[10px]">STABLE</Badge>
                        </div>

                        <div className="pt-4 flex justify-between items-center text-[10px] text-slate-600 font-bold uppercase tracking-widest px-1">
                            <span>Last Scan: 12s ago</span>
                            <span className="flex items-center gap-1 italic">Intelligence Level: 89% <ShieldCheck className="w-3 h-3" /></span>
                        </div>
                    </CardContent>
                </Card>

            </div>
        </div>
    );
}
