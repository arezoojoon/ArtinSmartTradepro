"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
    Briefcase, Target, PhoneCall, AlertCircle, TrendingUp,
    ShoppingCart, Factory, Clock, MessageCircle, Send, Plus
} from "lucide-react";
import Link from "next/link";

export default function CRMExecutionLayer() {
    const [activeRole, setActiveRole] = useState("manager");

    return (
        <div className="min-h-screen bg-[#0B1021] text-slate-300 p-4 md:p-8 pt-6 space-y-8">

            {/* Header */}
            <div className="flex flex-col md:flex-row md:justify-between md:items-end gap-4 border-b border-[#1E293B] pb-6">
                <div>
                    <div className="flex items-center gap-3 mb-2">
                        <div className="p-2 bg-[#D4AF37]/10 rounded-md border border-[#D4AF37]/30 shadow-[0_0_15px_rgba(212,175,55,0.15)]">
                            <Target className="h-6 w-6 text-[#D4AF37]" />
                        </div>
                        <h2 className="text-3xl font-bold tracking-tight text-white uppercase">Execution Hub</h2>
                    </div>
                    <p className="text-[#94A3B8] text-sm">Convert intelligence into action. Manage Pipelines, RFQs, and Follow-ups.</p>
                </div>
            </div>

            {/* Role Tabs */}
            <Tabs defaultValue="manager" onValueChange={setActiveRole} className="w-full">
                <TabsList className="grid w-full grid-cols-3 h-14 bg-[#131A2F] border border-[#1E293B] p-1 rounded-lg">
                    <TabsTrigger value="manager" className="rounded-md font-bold data-[state=active]:bg-[#D4AF37] data-[state=active]:text-[#0B1021] text-[#94A3B8]">
                        Trade Manager
                    </TabsTrigger>
                    <TabsTrigger value="sales" className="rounded-md font-bold data-[state=active]:bg-[#D4AF37] data-[state=active]:text-[#0B1021] text-[#94A3B8]">
                        Sales Agent
                    </TabsTrigger>
                    <TabsTrigger value="sourcing" className="rounded-md font-bold data-[state=active]:bg-[#D4AF37] data-[state=active]:text-[#0B1021] text-[#94A3B8]">
                        Sourcing Agent
                    </TabsTrigger>
                </TabsList>

                {/* 1. TRADE MANAGER VIEW */}
                <TabsContent value="manager" className="space-y-6 mt-6 animate-in fade-in duration-500">
                    <div className="grid gap-4 md:grid-cols-4">
                        <Card className="bg-[#131A2F] border-[#1E293B]">
                            <CardHeader className="flex flex-row items-center justify-between pb-2">
                                <CardTitle className="text-xs font-semibold text-[#94A3B8] uppercase tracking-widest">Sales Pipeline</CardTitle>
                                <TrendingUp className="h-4 w-4 text-[#D4AF37]" />
                            </CardHeader>
                            <CardContent>
                                <div className="text-2xl font-bold text-white">$2.4M</div>
                                <p className="text-xs text-emerald-400 font-medium mt-1">+14% MoM Growth</p>
                            </CardContent>
                        </Card>
                        <Card className="bg-[#131A2F] border-[#1E293B]">
                            <CardHeader className="flex flex-row items-center justify-between pb-2">
                                <CardTitle className="text-xs font-semibold text-[#94A3B8] uppercase tracking-widest">Active Deals</CardTitle>
                                <Briefcase className="h-4 w-4 text-[#D4AF37]" />
                            </CardHeader>
                            <CardContent>
                                <div className="text-2xl font-bold text-white">42</div>
                                <p className="text-xs text-[#94A3B8] mt-1">12 in Negotiation Stage</p>
                            </CardContent>
                        </Card>
                        <Card className="bg-[#131A2F] border-[#1E293B]">
                            <CardHeader className="flex flex-row items-center justify-between pb-2">
                                <CardTitle className="text-xs font-semibold text-[#94A3B8] uppercase tracking-widest">Open RFQs</CardTitle>
                                <ShoppingCart className="h-4 w-4 text-[#D4AF37]" />
                            </CardHeader>
                            <CardContent>
                                <div className="text-2xl font-bold text-white">8</div>
                                <p className="text-xs text-[#94A3B8] mt-1">3 Awaiting Responses</p>
                            </CardContent>
                        </Card>
                        <Card className="bg-[#450a0a]/30 border border-red-900/50">
                            <CardHeader className="flex flex-row items-center justify-between pb-2">
                                <CardTitle className="text-xs font-bold text-red-400 uppercase tracking-widest">SLA Breaches</CardTitle>
                                <AlertCircle className="h-4 w-4 text-red-500" />
                            </CardHeader>
                            <CardContent>
                                <div className="text-2xl font-bold text-red-400">3</div>
                                <p className="text-xs text-red-400/80 mt-1">Leads untouched &gt; 48h</p>
                            </CardContent>
                        </Card>
                    </div>

                    <div className="grid md:grid-cols-2 gap-6">
                        {/* Funnel */}
                        <Card className="bg-[#131A2F] border-[#1E293B]">
                            <CardHeader>
                                <CardTitle className="text-white text-lg font-medium border-b border-[#1E293B] pb-3">Sales Conversion Funnel</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-5 pt-4">
                                <div className="space-y-2">
                                    <div className="flex justify-between text-sm">
                                        <span className="text-[#94A3B8]">Target Leads (Hunter)</span>
                                        <span className="font-bold text-white">1,250</span>
                                    </div>
                                    <Progress value={100} className="h-1.5 bg-[#0B1021] [&>div]:bg-[#D4AF37]" />
                                </div>
                                <div className="space-y-2">
                                    <div className="flex justify-between text-sm">
                                        <span className="text-[#94A3B8]">Contacted (WA/Email)</span>
                                        <span className="font-bold text-white">480</span>
                                    </div>
                                    <Progress value={38} className="h-1.5 bg-[#0B1021] [&>div]:bg-blue-500" />
                                </div>
                                <div className="space-y-2">
                                    <div className="flex justify-between text-sm">
                                        <span className="text-[#94A3B8]">Quoted / Negotiating</span>
                                        <span className="font-bold text-white">112</span>
                                    </div>
                                    <Progress value={9} className="h-1.5 bg-[#0B1021] [&>div]:bg-purple-500" />
                                </div>
                                <div className="space-y-2">
                                    <div className="flex justify-between text-sm">
                                        <span className="text-[#D4AF37] font-semibold">Won Deals</span>
                                        <span className="font-bold text-emerald-400">24</span>
                                    </div>
                                    <Progress value={2} className="h-1.5 bg-[#0B1021] [&>div]:bg-emerald-500" />
                                </div>
                            </CardContent>
                        </Card>

                        {/* Actions */}
                        <Card className="bg-[#131A2F] border-[#1E293B]">
                            <CardHeader>
                                <CardTitle className="text-white text-lg font-medium border-b border-[#1E293B] pb-3">Manager Action Board</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-4 pt-4">
                                <div className="flex items-start gap-3 p-4 bg-[#450a0a]/20 rounded-lg border border-red-900/30">
                                    <AlertCircle className="h-5 w-5 text-red-500 mt-0.5" />
                                    <div>
                                        <p className="text-sm font-bold text-red-400">High-Value Lead Stalled</p>
                                        <p className="text-xs text-slate-400 mt-1">Carrefour UAE lead assigned to John has no activity for 3 days.</p>
                                        <Button size="sm" variant="outline" className="mt-3 text-xs h-8 border-red-900/50 text-red-400 hover:bg-red-900/30">Reassign Lead</Button>
                                    </div>
                                </div>
                                <div className="flex items-start gap-3 p-4 bg-[#D4AF37]/10 rounded-lg border border-[#D4AF37]/20">
                                    <Clock className="h-5 w-5 text-[#D4AF37] mt-0.5" />
                                    <div>
                                        <p className="text-sm font-bold text-[#D4AF37]">RFQ Validity Expiring</p>
                                        <p className="text-xs text-slate-400 mt-1">Supplier 'Zar Macaron' FOB price expires in 24 hours.</p>
                                        <Button size="sm" className="mt-3 text-xs h-8 bg-[#D4AF37] text-[#0B1021] hover:bg-white font-bold">Notify Sourcing Team</Button>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                </TabsContent>

                {/* 2. SALES AGENT VIEW */}
                <TabsContent value="sales" className="space-y-6 mt-6 animate-in fade-in duration-500">
                    <div className="flex flex-col sm:flex-row gap-4">
                        <Button className="flex-1 bg-[#D4AF37] text-[#0B1021] hover:bg-white h-14 text-md font-bold uppercase tracking-wider rounded-md">
                            <Target className="mr-2 h-5 w-5" /> Open Sales Kanban Board
                        </Button>
                        <Button variant="outline" className="flex-1 border-[#D4AF37]/30 bg-[#D4AF37]/10 text-[#D4AF37] hover:bg-[#D4AF37]/20 h-14 text-md font-bold uppercase tracking-wider rounded-md">
                            <Send className="mr-2 h-5 w-5" /> WhatsApp Mass Campaign
                        </Button>
                    </div>

                    <Card className="bg-[#131A2F] border-[#1E293B]">
                        <CardHeader className="border-b border-[#1E293B]">
                            <CardTitle className="text-white flex items-center gap-2 text-lg font-medium">
                                <Clock className="h-5 w-5 text-[#D4AF37]" /> Today's Action Items
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="pt-6">
                            <div className="space-y-3">
                                <div className="flex items-center justify-between p-4 bg-[#0B1021] rounded-lg border border-[#1E293B]">
                                    <div className="flex items-center gap-4">
                                        <div className="p-2.5 bg-blue-500/10 text-blue-400 rounded-md border border-blue-500/20">
                                            <PhoneCall className="h-5 w-5" />
                                        </div>
                                        <div>
                                            <p className="text-sm font-bold text-white">Call Spinneys Buyer</p>
                                            <p className="text-xs text-[#94A3B8] mt-0.5">Discuss CIF pricing for Q3 Pasta shipment</p>
                                        </div>
                                    </div>
                                    <Badge className="bg-orange-500/20 text-orange-400 border border-orange-500/30">Due 14:00</Badge>
                                </div>

                                <div className="flex items-center justify-between p-4 bg-[#0B1021] rounded-lg border border-[#1E293B]">
                                    <div className="flex items-center gap-4">
                                        <div className="p-2.5 bg-emerald-500/10 text-emerald-400 rounded-md border border-emerald-500/20">
                                            <MessageCircle className="h-5 w-5" />
                                        </div>
                                        <div>
                                            <p className="text-sm font-bold text-white">Send Proforma via WAHA</p>
                                            <p className="text-xs text-[#94A3B8] mt-0.5">Lulu Hypermarket - 2 Containers</p>
                                        </div>
                                    </div>
                                    <Badge className="bg-red-500/20 text-red-400 border border-red-500/30">High Priority</Badge>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>

                {/* 3. SOURCING AGENT VIEW */}
                <TabsContent value="sourcing" className="space-y-6 mt-6 animate-in fade-in duration-500">
                    <div className="flex flex-col sm:flex-row gap-4">
                        <Button className="flex-1 bg-[#D4AF37] text-[#0B1021] hover:bg-white h-14 text-md font-bold uppercase tracking-wider rounded-md">
                            <Plus className="mr-2 h-5 w-5" /> Create New RFQ
                        </Button>
                        <Button variant="outline" className="flex-1 border-[#D4AF37]/30 bg-[#D4AF37]/10 text-[#D4AF37] hover:bg-[#D4AF37]/20 h-14 text-md font-bold uppercase tracking-wider rounded-md">
                            <Factory className="mr-2 h-5 w-5" /> Supplier Database
                        </Button>
                    </div>

                    <Card className="bg-[#131A2F] border-[#1E293B]">
                        <CardHeader className="border-b border-[#1E293B]">
                            <CardTitle className="text-white flex items-center gap-2 text-lg font-medium">
                                <Factory className="h-5 w-5 text-[#D4AF37]" /> Active Supplier Negotiations
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="pt-6">
                            <div className="space-y-4">
                                <div className="border border-[#1E293B] rounded-lg p-5 bg-[#0B1021]">
                                    <div className="flex justify-between items-start mb-4">
                                        <div>
                                            <h4 className="font-bold text-white text-md">RFQ-2026-088: Copper Cathodes</h4>
                                            <p className="text-xs text-[#94A3B8] mt-1">Volume: 500 MT • Delivery: Jebel Ali, UAE</p>
                                        </div>
                                        <Badge className="bg-blue-500/10 text-blue-400 border border-blue-500/20">Receiving Quotes</Badge>
                                    </div>
                                    <div className="grid grid-cols-3 gap-3 text-sm">
                                        <div className="bg-[#131A2F] border border-[#1E293B] p-3 rounded-md text-center">
                                            <div className="text-[#94A3B8] text-[10px] uppercase tracking-widest mb-1">Contacted</div>
                                            <div className="font-bold text-white text-lg">12</div>
                                        </div>
                                        <div className="bg-[#131A2F] border border-[#D4AF37]/30 p-3 rounded-md text-center shadow-[inset_0_-2px_0_rgba(212,175,55,1)]">
                                            <div className="text-[#94A3B8] text-[10px] uppercase tracking-widest mb-1">Quotes Rcvd</div>
                                            <div className="font-bold text-[#D4AF37] text-lg">4</div>
                                        </div>
                                        <div className="bg-[#131A2F] border border-[#1E293B] p-3 rounded-md text-center">
                                            <div className="text-[#94A3B8] text-[10px] uppercase tracking-widest mb-1">Best FOB</div>
                                            <div className="font-bold text-white text-lg">$8,200/MT</div>
                                        </div>
                                    </div>
                                    <div className="mt-5 flex justify-end">
                                        <Button size="sm" className="bg-[#D4AF37]/10 text-[#D4AF37] border border-[#D4AF37]/20 hover:bg-[#D4AF37] hover:text-[#0B1021] font-bold text-xs uppercase tracking-wider">
                                            Compare Matrix &rarr;
                                        </Button>
                                    </div>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>
    );
}
