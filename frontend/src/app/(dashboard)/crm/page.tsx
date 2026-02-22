"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
    Briefcase, Target, PhoneCall, AlertCircle, TrendingUp,
    ShoppingCart, Factory, Clock, CheckCircle2, MessageCircle, Mail
} from "lucide-react";
import Link from "next/link";

export default function CRMOverviewPage() {
    // In a real app, this would come from the Auth/Tenant Context
    const [activeRole, setActiveRole] = useState("manager");

    return (
        <div className="space-y-6 max-w-7xl mx-auto p-4 md:p-8 pt-6">
            <div className="flex flex-col md:flex-row md:justify-between md:items-center gap-4">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
                        CRM & Execution <Briefcase className="h-6 w-6 text-indigo-500" />
                    </h2>
                    <p className="text-slate-500 dark:text-slate-400 mt-1">Manage Pipelines, RFQs, and Campaigns</p>
                </div>
            </div>

            {/* Role Simulator Tabs */}
            <Tabs defaultValue="manager" onValueChange={setActiveRole} className="w-full">
                <TabsList className="grid w-full grid-cols-3 h-14 bg-slate-100 dark:bg-slate-800 p-1 rounded-xl">
                    <TabsTrigger value="manager" className="rounded-lg font-bold data-[state=active]:bg-white dark:data-[state=active]:bg-slate-900 data-[state=active]:text-indigo-600 dark:data-[state=active]:text-indigo-400">
                        Trade Manager
                    </TabsTrigger>
                    <TabsTrigger value="sales" className="rounded-lg font-bold data-[state=active]:bg-white dark:data-[state=active]:bg-slate-900 data-[state=active]:text-blue-600 dark:data-[state=active]:text-blue-400">
                        Sales Agent
                    </TabsTrigger>
                    <TabsTrigger value="sourcing" className="rounded-lg font-bold data-[state=active]:bg-white dark:data-[state=active]:bg-slate-900 data-[state=active]:text-emerald-600 dark:data-[state=active]:text-emerald-400">
                        Sourcing Agent
                    </TabsTrigger>
                </TabsList>

                {/* ========================================== */}
                {/* 1. TRADE MANAGER VIEW (Holistic Overview) */}
                {/* ========================================== */}
                <TabsContent value="manager" className="space-y-6 mt-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                    <div className="grid gap-4 md:grid-cols-4">
                        <Card className="bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 shadow-sm">
                            <CardHeader className="flex flex-row items-center justify-between pb-2">
                                <CardTitle className="text-sm font-medium text-slate-600 dark:text-slate-400">Total Sales Pipeline</CardTitle>
                                <TrendingUp className="h-4 w-4 text-indigo-500" />
                            </CardHeader>
                            <CardContent>
                                <div className="text-2xl font-bold text-slate-900 dark:text-white">$2.4M</div>
                                <p className="text-xs text-emerald-600 font-medium mt-1">+14% from last month</p>
                            </CardContent>
                        </Card>
                        <Card className="bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 shadow-sm">
                            <CardHeader className="flex flex-row items-center justify-between pb-2">
                                <CardTitle className="text-sm font-medium text-slate-600 dark:text-slate-400">Active Deals</CardTitle>
                                <Briefcase className="h-4 w-4 text-blue-500" />
                            </CardHeader>
                            <CardContent>
                                <div className="text-2xl font-bold text-slate-900 dark:text-white">42</div>
                                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">12 pending negotiation</p>
                            </CardContent>
                        </Card>
                        <Card className="bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 shadow-sm">
                            <CardHeader className="flex flex-row items-center justify-between pb-2">
                                <CardTitle className="text-sm font-medium text-slate-600 dark:text-slate-400">Open RFQs (Sourcing)</CardTitle>
                                <ShoppingCart className="h-4 w-4 text-emerald-500" />
                            </CardHeader>
                            <CardContent>
                                <div className="text-2xl font-bold text-slate-900 dark:text-white">8</div>
                                <p className="text-xs text-orange-500 mt-1">3 awaiting supplier response</p>
                            </CardContent>
                        </Card>
                        <Card className="bg-white dark:bg-slate-900 border-red-200 dark:border-red-900/50 shadow-sm bg-red-50/30 dark:bg-red-950/10">
                            <CardHeader className="flex flex-row items-center justify-between pb-2">
                                <CardTitle className="text-sm font-bold text-red-700 dark:text-red-400">SLA Breaches</CardTitle>
                                <AlertCircle className="h-4 w-4 text-red-600" />
                            </CardHeader>
                            <CardContent>
                                <div className="text-2xl font-bold text-red-700 dark:text-red-400">3</div>
                                <p className="text-xs text-red-600/80 dark:text-red-400/80 mt-1">Leads untouched > 48h</p>
                            </CardContent>
                        </Card>
                    </div>

                    <div className="grid md:grid-cols-2 gap-6">
                        <Card className="bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 shadow-sm">
                            <CardHeader>
                                <CardTitle className="text-slate-900 dark:text-white text-lg">Sales Conversion Funnel</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="space-y-2">
                                    <div className="flex justify-between text-sm">
                                        <span className="text-slate-600 dark:text-slate-400">New Leads (Hunter)</span>
                                        <span className="font-bold text-slate-900 dark:text-white">1,250</span>
                                    </div>
                                    <Progress value={100} className="h-2 bg-slate-100 dark:bg-slate-800 [&>div]:bg-slate-300 dark:[&>div]:bg-slate-600" />
                                </div>
                                <div className="space-y-2">
                                    <div className="flex justify-between text-sm">
                                        <span className="text-slate-600 dark:text-slate-400">Contacted (WhatsApp/Email)</span>
                                        <span className="font-bold text-slate-900 dark:text-white">480</span>
                                    </div>
                                    <Progress value={38} className="h-2 bg-slate-100 dark:bg-slate-800 [&>div]:bg-blue-500" />
                                </div>
                                <div className="space-y-2">
                                    <div className="flex justify-between text-sm">
                                        <span className="text-slate-600 dark:text-slate-400">Qualified & Quoted</span>
                                        <span className="font-bold text-slate-900 dark:text-white">112</span>
                                    </div>
                                    <Progress value={9} className="h-2 bg-slate-100 dark:bg-slate-800 [&>div]:bg-indigo-500" />
                                </div>
                                <div className="space-y-2">
                                    <div className="flex justify-between text-sm">
                                        <span className="text-slate-600 dark:text-slate-400">Won Deals</span>
                                        <span className="font-bold text-emerald-600">24</span>
                                    </div>
                                    <Progress value={2} className="h-2 bg-slate-100 dark:bg-slate-800 [&>div]:bg-emerald-500" />
                                </div>
                            </CardContent>
                        </Card>

                        <Card className="bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 shadow-sm">
                            <CardHeader>
                                <CardTitle className="text-slate-900 dark:text-white text-lg">Action Required (Manager)</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="flex items-start gap-3 p-3 bg-red-50 dark:bg-red-950/20 rounded-lg border border-red-100 dark:border-red-900/30">
                                    <AlertCircle className="h-5 w-5 text-red-500 mt-0.5" />
                                    <div>
                                        <p className="text-sm font-bold text-red-800 dark:text-red-300">High-Value Lead Ignored</p>
                                        <p className="text-xs text-red-600 dark:text-red-400 mt-1">Carrefour UAE lead assigned to John has no activity for 3 days.</p>
                                        <Button size="sm" variant="outline" className="mt-2 text-xs h-7 border-red-200 dark:border-red-800">Reassign Lead</Button>
                                    </div>
                                </div>
                                <div className="flex items-start gap-3 p-3 bg-yellow-50 dark:bg-yellow-950/20 rounded-lg border border-yellow-100 dark:border-yellow-900/30">
                                    <Clock className="h-5 w-5 text-yellow-500 mt-0.5" />
                                    <div>
                                        <p className="text-sm font-bold text-yellow-800 dark:text-yellow-300">RFQ Approaching Deadline</p>
                                        <p className="text-xs text-yellow-600 dark:text-yellow-400 mt-1">Supplier 'Zar Macaron' price validity expires in 24 hours.</p>
                                        <Button size="sm" variant="outline" className="mt-2 text-xs h-7 border-yellow-200 dark:border-yellow-800 text-slate-800 dark:text-slate-200">Notify Sourcing Agent</Button>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                </TabsContent>

                {/* ========================================== */}
                {/* 2. SALES AGENT VIEW */}
                {/* ========================================== */}
                <TabsContent value="sales" className="space-y-6 mt-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                    <div className="flex items-center gap-4">
                        <Link href="/crm/pipelines" className="flex-1">
                            <Button className="w-full bg-blue-600 hover:bg-blue-700 text-white h-12 text-md">
                                <Target className="mr-2 h-5 w-5" /> Go to Sales Kanban Board
                            </Button>
                        </Link>
                        <Link href="/crm/campaigns" className="flex-1">
                            <Button variant="outline" className="w-full border-blue-200 dark:border-blue-900 hover:bg-blue-50 dark:hover:bg-blue-900/20 text-blue-700 dark:text-blue-400 h-12 text-md">
                                <MessageCircle className="mr-2 h-5 w-5" /> WhatsApp Campaigns
                            </Button>
                        </Link>
                    </div>

                    <Card className="bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 shadow-sm">
                        <CardHeader>
                            <CardTitle className="text-slate-900 dark:text-white flex items-center gap-2">
                                <Clock className="h-5 w-5 text-orange-500" /> Today's Follow-ups
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-3">
                                {/* Task 1 */}
                                <div className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg border border-slate-100 dark:border-slate-700/50">
                                    <div className="flex items-center gap-3">
                                        <div className="p-2 bg-blue-100 dark:bg-blue-900/30 text-blue-600 rounded-full">
                                            <PhoneCall className="h-4 w-4" />
                                        </div>
                                        <div>
                                            <p className="text-sm font-bold text-slate-900 dark:text-white">Call Spinneys Buyer</p>
                                            <p className="text-xs text-slate-500 dark:text-slate-400">Discuss pricing for Q3 Pasta shipment</p>
                                        </div>
                                    </div>
                                    <Badge className="bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400">Due 14:00</Badge>
                                </div>
                                {/* Task 2 */}
                                <div className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg border border-slate-100 dark:border-slate-700/50">
                                    <div className="flex items-center gap-3">
                                        <div className="p-2 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 rounded-full">
                                            <MessageCircle className="h-4 w-4" />
                                        </div>
                                        <div>
                                            <p className="text-sm font-bold text-slate-900 dark:text-white">Send Proforma Invoice</p>
                                            <p className="text-xs text-slate-500 dark:text-slate-400">Lulu Hypermarket - 2 Containers</p>
                                        </div>
                                    </div>
                                    <Badge className="bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400">High Priority</Badge>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>

                {/* ========================================== */}
                {/* 3. SOURCING AGENT VIEW */}
                {/* ========================================== */}
                <TabsContent value="sourcing" className="space-y-6 mt-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                    <div className="flex items-center gap-4">
                        <Link href="/sourcing/rfqs" className="flex-1">
                            <Button className="w-full bg-emerald-600 hover:bg-emerald-700 text-white h-12 text-md">
                                <ShoppingCart className="mr-2 h-5 w-5" /> Manage RFQs
                            </Button>
                        </Link>
                        <Link href="/hunter" className="flex-1">
                            <Button variant="outline" className="w-full border-emerald-200 dark:border-emerald-900 hover:bg-emerald-50 dark:hover:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400 h-12 text-md">
                                <Factory className="mr-2 h-5 w-5" /> Find New Suppliers
                            </Button>
                        </Link>
                    </div>

                    <Card className="bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 shadow-sm">
                        <CardHeader>
                            <CardTitle className="text-slate-900 dark:text-white flex items-center gap-2">
                                <Factory className="h-5 w-5 text-emerald-500" /> Active Supplier Negotiations
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4">
                                {/* RFQ 1 */}
                                <div className="border border-slate-200 dark:border-slate-700 rounded-lg p-4 bg-white dark:bg-slate-800/20">
                                    <div className="flex justify-between items-start mb-3">
                                        <div>
                                            <h4 className="font-bold text-slate-900 dark:text-white text-md">RFQ-2026-088: Copper Cathodes</h4>
                                            <p className="text-xs text-slate-500 mt-1">Requested: 500 MT • Target: Dubai (Jebel Ali)</p>
                                        </div>
                                        <Badge className="bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400">Receiving Quotes</Badge>
                                    </div>
                                    <div className="grid grid-cols-3 gap-2 text-sm">
                                        <div className="bg-slate-50 dark:bg-slate-800 p-2 rounded text-center">
                                            <div className="text-slate-500 dark:text-slate-400 text-xs">Suppliers Contacted</div>
                                            <div className="font-bold text-slate-900 dark:text-white">12</div>
                                        </div>
                                        <div className="bg-slate-50 dark:bg-slate-800 p-2 rounded text-center border-b-2 border-emerald-500">
                                            <div className="text-slate-500 dark:text-slate-400 text-xs">Quotes Received</div>
                                            <div className="font-bold text-emerald-600 dark:text-emerald-400">4</div>
                                        </div>
                                        <div className="bg-slate-50 dark:bg-slate-800 p-2 rounded text-center">
                                            <div className="text-slate-500 dark:text-slate-400 text-xs">Best FOB Price</div>
                                            <div className="font-bold text-slate-900 dark:text-white">$8,200/MT</div>
                                        </div>
                                    </div>
                                    <div className="mt-4 flex justify-end">
                                        <Button size="sm" variant="ghost" className="text-emerald-600 dark:text-emerald-400 hover:bg-emerald-50 dark:hover:bg-emerald-900/20">Compare Quotes &rarr;</Button>
                                    </div>
                                </div>

                                {/* RFQ 2 */}
                                <div className="border border-slate-200 dark:border-slate-700 rounded-lg p-4 bg-white dark:bg-slate-800/20">
                                    <div className="flex justify-between items-start mb-3">
                                        <div>
                                            <h4 className="font-bold text-slate-900 dark:text-white text-md">RFQ-2026-089: Robusta Coffee Beans</h4>
                                            <p className="text-xs text-slate-500 mt-1">Requested: 20ft Container • Target: Germany</p>
                                        </div>
                                        <Badge className="bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400">Negotiating</Badge>
                                    </div>
                                    <div className="mt-2 p-2 bg-orange-50 dark:bg-orange-950/20 border border-orange-100 dark:border-orange-900/30 rounded text-xs text-orange-800 dark:text-orange-300 flex items-center gap-2">
                                        <AlertCircle className="w-4 h-4" />
                                        Supplier "Vietnam Beans Co." flagged for recent shipping delays (Risk Engine Alert).
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
