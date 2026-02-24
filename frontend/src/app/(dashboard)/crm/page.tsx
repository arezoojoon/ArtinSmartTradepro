"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
    Users, Building2, Target, MessageCircle, CheckCircle2,
    Clock, AlertCircle, TrendingUp, ArrowRight, Plus, Search,
    Phone, Mail, Globe
} from "lucide-react";
import api from "@/lib/api";

interface PipelineStats {
    new: number;
    contacted: number;
    qualified: number;
    negotiation: number;
    won: number;
    lost: number;
}

interface RecentLead {
    id: string;
    company_name: string;
    contact_name: string;
    country: string;
    status: string;
    source: string;
    intent_score: number;
    created_at: string;
}

const STATUS_COLORS: Record<string, string> = {
    new: "bg-blue-500/10 text-blue-400 border-blue-500/30",
    contacted: "bg-amber-500/10 text-amber-400 border-amber-500/30",
    qualified: "bg-purple-500/10 text-purple-400 border-purple-500/30",
    interested: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
    negotiation: "bg-[#D4AF37]/10 text-[#D4AF37] border-[#D4AF37]/30",
    won: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
    closed: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
    lost: "bg-red-500/10 text-red-400 border-red-500/30",
};

export default function CRMOverviewPage() {
    const [stats, setStats] = useState<PipelineStats>({ new: 0, contacted: 0, qualified: 0, negotiation: 0, won: 0, lost: 0 });
    const [leads, setLeads] = useState<RecentLead[]>([]);
    const [companies, setCompanies] = useState<number>(0);
    const [contacts, setContacts] = useState<number>(0);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const [leadsRes, companiesRes, contactsRes] = await Promise.allSettled([
                api.get("/crm/companies?limit=200"),
                api.get("/crm/companies?limit=1"),
                api.get("/crm/contacts?limit=1"),
            ]);

            if (leadsRes.status === "fulfilled") {
                const items = leadsRes.value?.data?.items || leadsRes.value?.data || [];
                const arr = Array.isArray(items) ? items : [];
                setLeads(arr.slice(0, 10));
                const s: PipelineStats = { new: 0, contacted: 0, qualified: 0, negotiation: 0, won: 0, lost: 0 };
                arr.forEach((l: any) => {
                    const st = (l.status || "new").toLowerCase();
                    if (st in s) (s as any)[st]++;
                });
                setStats(s);
            }
            if (companiesRes.status === "fulfilled") {
                const d = companiesRes.value?.data;
                setCompanies(d?.total ?? (Array.isArray(d) ? d.length : 0));
            }
            if (contactsRes.status === "fulfilled") {
                const d = contactsRes.value?.data;
                setContacts(d?.total ?? (Array.isArray(d) ? d.length : 0));
            }
        } catch (e) {
            console.error("CRM load error:", e);
        } finally {
            setLoading(false);
        }
    };

    const totalPipeline = stats.new + stats.contacted + stats.qualified + stats.negotiation;

    const pipelineStages = [
        { label: "New", count: stats.new, color: "bg-blue-500" },
        { label: "Contacted", count: stats.contacted, color: "bg-amber-500" },
        { label: "Qualified", count: stats.qualified, color: "bg-purple-500" },
        { label: "Negotiation", count: stats.negotiation, color: "bg-[#D4AF37]" },
        { label: "Won", count: stats.won, color: "bg-emerald-500" },
    ];

    return (
        <div className="space-y-8">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:justify-between md:items-end gap-4 border-b border-[#1E293B] pb-6">
                <div>
                    <div className="flex items-center gap-3 mb-2">
                        <div className="p-2 bg-[#D4AF37]/10 rounded-md border border-[#D4AF37]/30">
                            <Target className="h-6 w-6 text-[#D4AF37]" />
                        </div>
                        <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-white uppercase">CRM</h1>
                    </div>
                    <p className="text-[#94A3B8] text-sm">Pipeline overview, companies, contacts & deals</p>
                </div>
                <div className="flex gap-2">
                    <Link href="/crm/companies">
                        <Button variant="outline" className="border-[#1E293B] text-slate-300 hover:bg-[#1E293B] text-xs uppercase tracking-wider">
                            <Building2 className="w-4 h-4 mr-1.5" /> Companies
                        </Button>
                    </Link>
                    <Link href="/crm/contacts">
                        <Button variant="outline" className="border-[#1E293B] text-slate-300 hover:bg-[#1E293B] text-xs uppercase tracking-wider">
                            <Users className="w-4 h-4 mr-1.5" /> Contacts
                        </Button>
                    </Link>
                </div>
            </div>

            {/* KPI Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Card className="bg-[#0F172A] border-[#1E293B]">
                    <CardContent className="p-5">
                        <div className="text-[10px] text-[#94A3B8] uppercase tracking-widest mb-1 flex items-center justify-between">
                            Active Pipeline <TrendingUp className="w-3 h-3 text-[#D4AF37]" />
                        </div>
                        <div className="text-3xl font-bold text-white">{loading ? "—" : totalPipeline}</div>
                        <div className="text-xs text-[#94A3B8] mt-1">Open opportunities</div>
                    </CardContent>
                </Card>
                <Card className="bg-[#0F172A] border-[#1E293B]">
                    <CardContent className="p-5">
                        <div className="text-[10px] text-[#94A3B8] uppercase tracking-widest mb-1 flex items-center justify-between">
                            Companies <Building2 className="w-3 h-3 text-blue-400" />
                        </div>
                        <div className="text-3xl font-bold text-white">{loading ? "—" : companies}</div>
                        <div className="text-xs text-[#94A3B8] mt-1">In your CRM</div>
                    </CardContent>
                </Card>
                <Card className="bg-[#0F172A] border-[#1E293B]">
                    <CardContent className="p-5">
                        <div className="text-[10px] text-[#94A3B8] uppercase tracking-widest mb-1 flex items-center justify-between">
                            Contacts <Users className="w-3 h-3 text-emerald-400" />
                        </div>
                        <div className="text-3xl font-bold text-white">{loading ? "—" : contacts}</div>
                        <div className="text-xs text-[#94A3B8] mt-1">Decision-makers</div>
                    </CardContent>
                </Card>
                <Card className="bg-[#0F172A] border-[#1E293B] shadow-[inset_0_-2px_0_rgba(16,185,129,1)]">
                    <CardContent className="p-5">
                        <div className="text-[10px] text-emerald-400 uppercase tracking-widest mb-1 flex items-center justify-between">
                            Won <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                        </div>
                        <div className="text-3xl font-bold text-emerald-400">{loading ? "—" : stats.won}</div>
                        <div className="text-xs text-[#94A3B8] mt-1">Closed deals</div>
                    </CardContent>
                </Card>
            </div>

            {/* Pipeline Bar */}
            <Card className="bg-[#0F172A] border-[#1E293B]">
                <CardHeader className="pb-3 border-b border-[#1E293B]">
                    <CardTitle className="text-sm font-medium text-white">Pipeline Stages</CardTitle>
                </CardHeader>
                <CardContent className="pt-4">
                    <div className="flex gap-3">
                        {pipelineStages.map(stage => (
                            <div key={stage.label} className="flex-1 text-center">
                                <div className={`h-2 rounded-full ${stage.color} mb-2`} style={{ opacity: stage.count > 0 ? 1 : 0.2 }} />
                                <p className="text-lg font-bold text-white">{stage.count}</p>
                                <p className="text-[10px] text-[#94A3B8] uppercase tracking-widest">{stage.label}</p>
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>

            {/* Recent Leads / Quick Links */}
            <div className="grid lg:grid-cols-12 gap-6">
                <div className="lg:col-span-8">
                    <Card className="bg-[#0F172A] border-[#1E293B]">
                        <CardHeader className="pb-3 border-b border-[#1E293B] flex flex-row items-center justify-between">
                            <CardTitle className="text-sm font-medium text-white">Recent Companies</CardTitle>
                            <Link href="/crm/companies" className="text-xs text-[#D4AF37] hover:text-[#F3E5AB] flex items-center gap-1">
                                View all <ArrowRight className="w-3 h-3" />
                            </Link>
                        </CardHeader>
                        <CardContent className="pt-0">
                            {loading ? (
                                <div className="py-10 text-center text-slate-600 text-sm">Loading...</div>
                            ) : leads.length === 0 ? (
                                <div className="py-10 text-center text-slate-600 text-sm">
                                    <p>No companies yet.</p>
                                    <Link href="/crm/companies">
                                        <Button className="mt-3 bg-[#D4AF37] text-[#050A15] hover:bg-[#F3E5AB] text-xs">
                                            <Plus className="w-3 h-3 mr-1" /> Add First Company
                                        </Button>
                                    </Link>
                                </div>
                            ) : (
                                <div className="divide-y divide-[#1E293B]">
                                    {leads.map((lead) => (
                                        <div key={lead.id} className="py-3 flex items-center justify-between hover:bg-[#0F172A]/50 px-2 -mx-2 rounded transition-colors">
                                            <div className="flex items-center gap-3 min-w-0">
                                                <div className="w-9 h-9 rounded-lg bg-[#1E293B] flex items-center justify-center flex-shrink-0">
                                                    <Building2 className="w-4 h-4 text-[#D4AF37]" />
                                                </div>
                                                <div className="min-w-0">
                                                    <p className="text-sm font-medium text-white truncate">{lead.company_name || lead.contact_name}</p>
                                                    <p className="text-xs text-[#94A3B8] flex items-center gap-1">
                                                        {lead.country && <><Globe className="w-3 h-3" /> {lead.country}</>}
                                                        {lead.source && <span className="ml-2 text-slate-600">via {lead.source}</span>}
                                                    </p>
                                                </div>
                                            </div>
                                            <Badge className={`text-[10px] border ${STATUS_COLORS[lead.status] || STATUS_COLORS.new} flex-shrink-0`}>
                                                {lead.status || "new"}
                                            </Badge>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </div>

                {/* Quick Actions */}
                <div className="lg:col-span-4 space-y-4">
                    <Card className="bg-[#0F172A] border-[#1E293B]">
                        <CardHeader className="pb-3 border-b border-[#1E293B]">
                            <CardTitle className="text-sm font-medium text-white">Quick Actions</CardTitle>
                        </CardHeader>
                        <CardContent className="pt-4 space-y-3">
                            <Link href="/crm/companies" className="block">
                                <div className="p-3 bg-[#050A15] border border-[#1E293B] rounded-lg hover:border-[#D4AF37]/50 transition-colors group cursor-pointer">
                                    <div className="flex items-center gap-2">
                                        <Building2 className="w-4 h-4 text-blue-400" />
                                        <span className="text-sm text-white group-hover:text-[#D4AF37] transition-colors">Manage Companies</span>
                                    </div>
                                </div>
                            </Link>
                            <Link href="/crm/contacts" className="block">
                                <div className="p-3 bg-[#050A15] border border-[#1E293B] rounded-lg hover:border-[#D4AF37]/50 transition-colors group cursor-pointer">
                                    <div className="flex items-center gap-2">
                                        <Users className="w-4 h-4 text-emerald-400" />
                                        <span className="text-sm text-white group-hover:text-[#D4AF37] transition-colors">Manage Contacts</span>
                                    </div>
                                </div>
                            </Link>
                            <Link href="/crm/pipelines" className="block">
                                <div className="p-3 bg-[#050A15] border border-[#1E293B] rounded-lg hover:border-[#D4AF37]/50 transition-colors group cursor-pointer">
                                    <div className="flex items-center gap-2">
                                        <Target className="w-4 h-4 text-purple-400" />
                                        <span className="text-sm text-white group-hover:text-[#D4AF37] transition-colors">Deal Pipelines</span>
                                    </div>
                                </div>
                            </Link>
                            <Link href="/crm/campaigns" className="block">
                                <div className="p-3 bg-[#050A15] border border-[#1E293B] rounded-lg hover:border-[#D4AF37]/50 transition-colors group cursor-pointer">
                                    <div className="flex items-center gap-2">
                                        <MessageCircle className="w-4 h-4 text-[#D4AF37]" />
                                        <span className="text-sm text-white group-hover:text-[#D4AF37] transition-colors">Campaigns</span>
                                    </div>
                                </div>
                            </Link>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
}
