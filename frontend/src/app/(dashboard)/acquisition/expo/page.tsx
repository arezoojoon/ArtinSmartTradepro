"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
    Globe, Users, QrCode, BookOpen, Handshake, Calendar,
    Loader2, Search, RefreshCw, ArrowRight, Phone, Mail,
    MapPin, Filter, Download, Plus, X,
} from "lucide-react";
import api from "@/lib/api";

interface ExpoLead {
    id: number;
    full_name: string;
    company?: string;
    email?: string;
    phone?: string;
    country?: string;
    interest_level?: string;
    source?: string;
    status?: string;
    created_at?: string;
}

const EMPTY_LEAD = { company_name: "", contact_name: "", email: "", phone: "", country: "", source: "expo" };

export default function ExpoLeadsPage() {
    const [leads, setLeads] = useState<ExpoLead[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState("");
    const [statusFilter, setStatusFilter] = useState("all");
    const [showAddLead, setShowAddLead] = useState(false);
    const [saving, setSaving] = useState(false);
    const [leadForm, setLeadForm] = useState(EMPTY_LEAD);

    const fetchLeads = useCallback(async () => {
        try {
            const res = await api.get("/leads?limit=200&source=expo");
            setLeads(res.data?.leads || res.data || []);
        } catch (e) {
            console.error("Expo leads fetch failed:", e);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { fetchLeads(); }, [fetchLeads]);

    const handleAddLead = async () => {
        if (!leadForm.company_name.trim() && !leadForm.contact_name.trim()) return;
        setSaving(true);
        try {
            await api.post("/leads", leadForm);
            setShowAddLead(false);
            setLeadForm(EMPTY_LEAD);
            setLoading(true);
            fetchLeads();
        } catch (e) { console.error("Create lead failed:", e); }
        finally { setSaving(false); }
    };

    const filtered = leads.filter(l => {
        const matchSearch = !searchQuery ||
            l.full_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
            l.company?.toLowerCase().includes(searchQuery.toLowerCase()) ||
            l.email?.toLowerCase().includes(searchQuery.toLowerCase());
        const matchStatus = statusFilter === "all" || l.status === statusFilter;
        return matchSearch && matchStatus;
    });

    const statusCounts = {
        total: leads.length,
        new: leads.filter(l => l.status === "new").length,
        contacted: leads.filter(l => l.status === "contacted").length,
        qualified: leads.filter(l => l.status === "qualified").length,
        converted: leads.filter(l => l.status === "converted" || l.status === "closed_won").length,
    };

    return (
        <div className="min-h-screen bg-[#050A15] text-slate-300 p-4 md:p-8 space-y-6">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-[#1E293B] pb-6">
                <div>
                    <div className="flex items-center gap-3 mb-2">
                        <div className="p-2 bg-amber-500/10 rounded-md border border-amber-500/30">
                            <Globe className="h-5 w-5 text-amber-400" />
                        </div>
                        <h1 className="text-2xl font-bold text-white uppercase tracking-tight">Expo Leads</h1>
                    </div>
                    <p className="text-sm text-slate-500">Exhibition visitor leads, negotiation requests &amp; booth interactions</p>
                </div>
                <div className="flex gap-3">
                    <Button variant="outline" size="sm" onClick={() => { setLoading(true); fetchLeads(); }} className="border-slate-700 text-slate-400">
                        <RefreshCw className="w-4 h-4 mr-2" /> Refresh
                    </Button>
                    <Button onClick={() => setShowAddLead(true)} className="bg-[#D4AF37] text-[#050A15] hover:bg-[#F3E5AB] font-bold">
                        <Plus className="w-4 h-4 mr-2" /> Add Lead
                    </Button>
                </div>
            </div>

            {/* KPI Strip */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                {[
                    { label: "Total", value: statusCounts.total, color: "text-white" },
                    { label: "New", value: statusCounts.new, color: "text-blue-400" },
                    { label: "Contacted", value: statusCounts.contacted, color: "text-amber-400" },
                    { label: "Qualified", value: statusCounts.qualified, color: "text-emerald-400" },
                    { label: "Converted", value: statusCounts.converted, color: "text-[#D4AF37]" },
                ].map(k => (
                    <Card key={k.label} className="bg-[#0F172A] border-[#1E293B]">
                        <CardContent className="p-3 text-center">
                            <div className={`text-2xl font-bold ${k.color}`}>{k.value}</div>
                            <p className="text-[10px] uppercase tracking-widest text-slate-500">{k.label}</p>
                        </CardContent>
                    </Card>
                ))}
            </div>

            {/* Filters */}
            <div className="flex flex-col md:flex-row gap-3">
                <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                    <input type="text" placeholder="Search leads..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full pl-10 pr-4 py-2.5 bg-[#0F172A] border border-[#1E293B] rounded-lg text-white placeholder:text-slate-600 focus:outline-none focus:border-[#D4AF37]/50" />
                </div>
                <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}
                    className="px-4 py-2.5 bg-[#0F172A] border border-[#1E293B] rounded-lg text-white focus:outline-none">
                    <option value="all">All Statuses</option>
                    <option value="new">New</option>
                    <option value="contacted">Contacted</option>
                    <option value="qualified">Qualified</option>
                    <option value="negotiation">Negotiation</option>
                    <option value="converted">Converted</option>
                </select>
            </div>

            {/* Lead List */}
            {loading ? (
                <div className="flex items-center justify-center py-20"><Loader2 className="h-8 w-8 animate-spin text-[#D4AF37]" /></div>
            ) : filtered.length === 0 ? (
                <Card className="bg-[#0F172A] border-[#1E293B]">
                    <CardContent className="py-20 flex flex-col items-center text-center">
                        <div className="w-20 h-20 rounded-full bg-amber-500/10 flex items-center justify-center mb-6">
                            <Globe className="w-10 h-10 text-amber-500" />
                        </div>
                        <h3 className="text-white font-bold text-2xl mb-3">No exhibition leads yet</h3>
                        <p className="text-slate-400 max-w-md mx-auto mb-8 leading-relaxed">
                            Leads will appear here as visitors interact with your booth via QR codes, bots, and catalog downloads.
                        </p>
                        <div className="flex gap-4">
                            <Button className="bg-[#D4AF37] text-[#050A15] hover:bg-[#F3E5AB] font-bold px-6 py-6" onClick={() => window.location.href = '/acquisition/qr-capture'}>
                                <QrCode className="w-5 h-5 mr-2" /> Generate Booth QR
                            </Button>
                            <Button variant="outline" className="border-slate-700 text-slate-300 hover:bg-[#1E293B] px-6 py-6" onClick={() => setShowAddLead(true)}>
                                <Plus className="w-5 h-5 mr-2" /> Add Lead Manually
                            </Button>
                        </div>
                    </CardContent>
                </Card>
            ) : (
                <div className="space-y-2">
                    {filtered.map((lead) => (
                        <Card key={lead.id} className="bg-[#0F172A] border-[#1E293B] hover:border-[#D4AF37]/30 transition-colors">
                            <CardContent className="p-4 flex flex-col md:flex-row justify-between items-start md:items-center gap-3">
                                <div className="flex items-start gap-3 min-w-0">
                                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#D4AF37] to-[#B8860B] flex items-center justify-center text-black font-bold text-sm shrink-0">
                                        {lead.full_name?.[0] || "?"}
                                    </div>
                                    <div className="min-w-0">
                                        <h4 className="text-white font-bold truncate">{lead.full_name}</h4>
                                        <div className="flex items-center gap-3 text-xs text-slate-500 mt-1 flex-wrap">
                                            {lead.company && <span>{lead.company}</span>}
                                            {lead.country && <span className="flex items-center gap-1"><MapPin className="w-3 h-3" />{lead.country}</span>}
                                            {lead.source && <Badge variant="outline" className="text-[10px] border-slate-700">{lead.source}</Badge>}
                                        </div>
                                    </div>
                                </div>
                                <div className="flex items-center gap-2 shrink-0">
                                    {lead.interest_level && (
                                        <Badge className={`border-none text-xs ${lead.interest_level === "hot" ? "bg-red-500/10 text-red-400" : lead.interest_level === "warm" ? "bg-amber-500/10 text-amber-400" : "bg-blue-500/10 text-blue-400"}`}>
                                            {lead.interest_level}
                                        </Badge>
                                    )}
                                    <div className="flex items-center gap-1 border-l border-[#1E293B] pl-2 ml-2">
                                        {lead.email && <a href={`mailto:${lead.email}`} className="p-2 bg-[#050A15] border border-[#1E293B] rounded-md text-slate-400 hover:text-white hover:border-slate-700 transition-colors"><Mail className="w-4 h-4" /></a>}
                                        {lead.phone && <a href={`tel:${lead.phone}`} className="p-2 bg-[#050A15] border border-[#1E293B] rounded-md text-slate-400 hover:text-white hover:border-slate-700 transition-colors"><Phone className="w-4 h-4" /></a>}
                                        <Button size="sm" variant="outline" className="bg-[#D4AF37]/10 border-[#D4AF37]/30 text-[#D4AF37] hover:bg-[#D4AF37] hover:text-[#050A15] ml-1"
                                            onClick={() => window.location.href = `/crm/contacts/import?from_lead_id=${lead.id}&source=expo`}>
                                            <ArrowRight className="w-4 h-4 mr-1" /> Convert to CRM
                                        </Button>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            )}

            {/* Add Lead Modal */}
            {showAddLead && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={() => setShowAddLead(false)}>
                    <div className="bg-[#0F172A] border border-[#1E293B] rounded-2xl p-6 w-full max-w-md space-y-4" onClick={e => e.stopPropagation()}>
                        <div className="flex justify-between items-center">
                            <h3 className="text-white font-bold text-lg">Add Expo Lead</h3>
                            <button onClick={() => setShowAddLead(false)} className="text-slate-500 hover:text-white"><X className="w-5 h-5" /></button>
                        </div>
                        <div className="space-y-3">
                            <input placeholder="Contact Name *" value={leadForm.contact_name} onChange={e => setLeadForm(p => ({ ...p, contact_name: e.target.value }))} className="w-full bg-[#050A15] border border-[#1E293B] rounded-lg px-4 py-2.5 text-white placeholder-slate-600 text-sm focus:border-[#D4AF37] outline-none" />
                            <input placeholder="Company Name" value={leadForm.company_name} onChange={e => setLeadForm(p => ({ ...p, company_name: e.target.value }))} className="w-full bg-[#050A15] border border-[#1E293B] rounded-lg px-4 py-2.5 text-white placeholder-slate-600 text-sm focus:border-[#D4AF37] outline-none" />
                            <input placeholder="Email" value={leadForm.email} onChange={e => setLeadForm(p => ({ ...p, email: e.target.value }))} className="w-full bg-[#050A15] border border-[#1E293B] rounded-lg px-4 py-2.5 text-white placeholder-slate-600 text-sm focus:border-[#D4AF37] outline-none" />
                            <input placeholder="Phone" value={leadForm.phone} onChange={e => setLeadForm(p => ({ ...p, phone: e.target.value }))} className="w-full bg-[#050A15] border border-[#1E293B] rounded-lg px-4 py-2.5 text-white placeholder-slate-600 text-sm focus:border-[#D4AF37] outline-none" />
                            <input placeholder="Country" value={leadForm.country} onChange={e => setLeadForm(p => ({ ...p, country: e.target.value }))} className="w-full bg-[#050A15] border border-[#1E293B] rounded-lg px-4 py-2.5 text-white placeholder-slate-600 text-sm focus:border-[#D4AF37] outline-none" />
                        </div>
                        <Button onClick={handleAddLead} disabled={saving || (!leadForm.contact_name.trim() && !leadForm.company_name.trim())} className="w-full bg-[#D4AF37] text-[#050A15] hover:bg-[#F3E5AB] font-bold disabled:opacity-40">
                            {saving ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Plus className="w-4 h-4 mr-2" />}
                            {saving ? "Creating..." : "Create Lead"}
                        </Button>
                    </div>
                </div>
            )}
        </div>
    );
}
