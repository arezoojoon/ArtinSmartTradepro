"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
    Search, Plus, Filter, Download, Users, Globe,
    TrendingUp, Loader2, ArrowRight, Mail, Phone,
    MapPin, Building2, Target, RefreshCw, ExternalLink,
} from "lucide-react";
import api from "@/lib/api";

interface Lead {
    id: string;
    company_name: string;
    contact_name?: string;
    email?: string;
    phone?: string;
    country?: string;
    source?: string;
    status?: string;
    score?: number;
    created_at?: string;
}

export default function BuyerLeadsPage() {
    const [leads, setLeads] = useState<Lead[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState("");
    const [statusFilter, setStatusFilter] = useState("all");

    const fetchLeads = useCallback(async () => {
        try {
            const res = await api.get("/hunter/search?type=buyer&limit=50");
            setLeads(res.data?.results || res.data || []);
        } catch (e) {
            console.error("Buyer leads fetch failed:", e);
            // Fallback: try CRM contacts with buyer tag
            try {
                const fallback = await api.get("/crm/contacts?tag=buyer&limit=50");
                setLeads(fallback.data?.contacts || fallback.data || []);
            } catch { /* ignore */ }
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { fetchLeads(); }, [fetchLeads]);

    const filtered = leads.filter(l => {
        const matchSearch = !searchQuery ||
            l.company_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
            l.contact_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
            l.email?.toLowerCase().includes(searchQuery.toLowerCase());
        const matchStatus = statusFilter === "all" || l.status === statusFilter;
        return matchSearch && matchStatus;
    });

    return (
        <div className="min-h-screen bg-[#050A15] text-slate-300 p-4 md:p-8 space-y-6">
            {/* Header */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-[#1E293B] pb-6">
                <div>
                    <div className="flex items-center gap-3 mb-2">
                        <div className="p-2 bg-blue-500/10 rounded-md border border-blue-500/30">
                            <Search className="h-5 w-5 text-blue-400" />
                        </div>
                        <h1 className="text-2xl font-bold text-white uppercase tracking-tight">Buyer Leads</h1>
                    </div>
                    <p className="text-sm text-slate-500">AI-powered buyer discovery & lead generation — powered by Hunter engine</p>
                </div>
                <div className="flex gap-3">
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => { setLoading(true); fetchLeads(); }}
                        className="border-slate-700 text-slate-400"
                    >
                        <RefreshCw className="w-4 h-4 mr-2" /> Refresh
                    </Button>
                    <Button
                        onClick={() => document.querySelector('input')?.focus()}
                        className="bg-[#D4AF37] text-[#050A15] hover:bg-[#F3E5AB] font-bold"
                    >
                        <Plus className="w-4 h-4 mr-2" /> Launch Buyer Hunt
                    </Button>
                </div>
            </div>

            {/* Filters */}
            <div className="flex flex-col md:flex-row gap-3">
                <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                    <input
                        type="text"
                        placeholder="Search by company, contact, or email..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full pl-10 pr-4 py-2.5 bg-[#0F172A] border border-[#1E293B] rounded-lg text-white placeholder:text-slate-600 focus:outline-none focus:border-[#D4AF37]/50"
                    />
                </div>
                <select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                    className="px-4 py-2.5 bg-[#0F172A] border border-[#1E293B] rounded-lg text-white focus:outline-none"
                >
                    <option value="all">All Statuses</option>
                    <option value="new">New</option>
                    <option value="contacted">Contacted</option>
                    <option value="qualified">Qualified</option>
                    <option value="converted">Converted</option>
                </select>
            </div>

            {/* Results */}
            {loading ? (
                <div className="flex items-center justify-center py-20">
                    <Loader2 className="h-8 w-8 animate-spin text-[#D4AF37]" />
                </div>
            ) : filtered.length === 0 ? (
                <Card className="bg-[#0F172A] border-[#1E293B]">
                    <CardContent className="py-20 flex flex-col items-center text-center">
                        <div className="w-20 h-20 rounded-full bg-blue-500/10 flex items-center justify-center mb-6">
                            <Users className="w-10 h-10 text-blue-500" />
                        </div>
                        <h3 className="text-white font-bold text-2xl mb-3">No buyer leads yet</h3>
                        <p className="text-slate-400 max-w-md mx-auto mb-8 leading-relaxed">
                            Start discovering potential buyers for your products using the AI-powered Hunter engine.
                        </p>
                        <Button
                            onClick={() => document.querySelector('input')?.focus()}
                            className="bg-[#D4AF37] text-[#050A15] hover:bg-[#F3E5AB] font-bold px-6 py-6 border border-[#D4AF37]"
                        >
                            <Target className="w-5 h-5 mr-2" />
                            Run First Buyer Search
                        </Button>
                    </CardContent>
                </Card>
            ) : (
                <div className="space-y-3">
                    <p className="text-xs text-slate-500 uppercase tracking-widest">{filtered.length} results</p>
                    {filtered.map((lead) => (
                        <Card key={lead.id} className="bg-[#0F172A] border-[#1E293B] hover:border-[#D4AF37]/30 transition-colors">
                            <CardContent className="p-4 flex flex-col md:flex-row justify-between items-start md:items-center gap-3">
                                <div className="flex items-start gap-3 min-w-0">
                                    <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center shrink-0">
                                        <Building2 className="w-5 h-5 text-blue-400" />
                                    </div>
                                    <div className="min-w-0">
                                        <h4 className="text-white font-bold truncate">{lead.company_name || "Unknown Company"}</h4>
                                        <div className="flex items-center gap-3 text-xs text-slate-500 mt-1 flex-wrap">
                                            {lead.contact_name && <span className="flex items-center gap-1"><Users className="w-3 h-3" /> {lead.contact_name}</span>}
                                            {lead.country && <span className="flex items-center gap-1"><MapPin className="w-3 h-3" /> {lead.country}</span>}
                                            {lead.email && <span className="flex items-center gap-1"><Mail className="w-3 h-3" /> {lead.email}</span>}
                                        </div>
                                    </div>
                                </div>
                                <div className="flex items-center gap-3 shrink-0">
                                    {lead.score != null && (
                                        <Badge className={`${lead.score >= 70 ? "bg-emerald-500/10 text-emerald-400" : lead.score >= 40 ? "bg-amber-500/10 text-amber-400" : "bg-slate-500/10 text-slate-400"} border-none text-xs`}>
                                            Score: {lead.score}
                                        </Badge>
                                    )}
                                    {lead.status && (
                                        <Badge variant="outline" className="text-xs border-slate-700 text-slate-400">
                                            {lead.status}
                                        </Badge>
                                    )}
                                    <Button size="sm" variant="outline" onClick={() => window.location.href = `/crm/contacts?search=${encodeURIComponent(lead.company_name || '')}`} className="border-[#D4AF37]/30 text-[#D4AF37] hover:bg-[#D4AF37]/10 text-xs">
                                        View <ArrowRight className="w-3 h-3 ml-1" />
                                    </Button>
                                </div>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            )}
        </div>
    );
}
