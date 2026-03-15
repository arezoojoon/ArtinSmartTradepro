"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
    Search, Plus, Filter, Download, Users, Globe,
    TrendingUp, Loader2, ArrowRight, Mail, Phone,
    MapPin, Building2, Target, RefreshCw, ExternalLink,
    X, Check, ChevronDown, Clock, AlertCircle,
    Linkedin, MessageCircle, Map, Globe2, Facebook,
    Send, Hash, Briefcase, Store, DollarSign,
} from "lucide-react";
import api from "@/lib/api";

/* ───────── Source Config ───────── */
const SOURCES = [
    { id: "google_maps", label: "Google Maps", icon: Map, color: "text-green-400", bg: "bg-green-500/10", border: "border-green-500/30", auth: false },
    { id: "linkedin", label: "LinkedIn", icon: Linkedin, color: "text-blue-400", bg: "bg-blue-500/10", border: "border-blue-500/30", auth: true, fields: ["username", "password"] },
    { id: "telegram", label: "Telegram Groups", icon: Send, color: "text-sky-400", bg: "bg-sky-500/10", border: "border-sky-500/30", auth: true, fields: ["api_id", "api_hash", "phone"] },
    { id: "discord", label: "Discord", icon: Hash, color: "text-indigo-400", bg: "bg-indigo-500/10", border: "border-indigo-500/30", auth: true, fields: ["bot_token"] },
    { id: "trademap", label: "TradeMap", icon: Globe2, color: "text-amber-400", bg: "bg-amber-500/10", border: "border-amber-500/30", auth: true, fields: ["username", "password"] },
    { id: "facebook", label: "Facebook Groups", icon: Facebook, color: "text-blue-500", bg: "bg-blue-600/10", border: "border-blue-600/30", auth: true, fields: ["username", "password"] },
    { id: "web", label: "Web / Google", icon: Globe, color: "text-purple-400", bg: "bg-purple-500/10", border: "border-purple-500/30", auth: false },
];

const FIELD_LABELS: Record<string, string> = {
    username: "Username / Email",
    password: "Password",
    api_id: "API ID",
    api_hash: "API Hash",
    phone: "Phone Number",
    bot_token: "Bot Token",
};

/* ───────── Interfaces ───────── */
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
    brand_name?: string;
    product_name?: string;
    price?: string;
    website?: string;
    created_at?: string;
}

interface HuntJob {
    job_id: string;
    status: string;
    keyword: string;
    sources: string[];
    created_at?: string;
    result_count?: number;
}

/* ───────── Component ───────── */
export default function BuyerLeadsPage() {
    const [leads, setLeads] = useState<Lead[]>([]);
    const [jobs, setJobs] = useState<HuntJob[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState("");
    const [statusFilter, setStatusFilter] = useState("all");
    const [showModal, setShowModal] = useState(false);

    // Hunt form state
    const [selectedSources, setSelectedSources] = useState<string[]>([]);
    const [keyword, setKeyword] = useState("");
    const [location, setLocation] = useState("");
    const [hsCode, setHsCode] = useState("");
    const [credentials, setCredentials] = useState<Record<string, Record<string, string>>>({});
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [huntError, setHuntError] = useState("");

    const fetchLeads = useCallback(async () => {
        try {
            const res = await api.get("/hunter/search?type=buyer&limit=100");
            setLeads(res.data?.results || res.data || []);
        } catch (e) {
            console.error("Buyer leads fetch failed:", e);
            try {
                const fallback = await api.get("/crm/contacts?tag=buyer&limit=100");
                setLeads(fallback.data?.contacts || fallback.data || []);
            } catch { /* ignore */ }
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { fetchLeads(); }, [fetchLeads]);

    const toggleSource = (id: string) => {
        setSelectedSources(prev =>
            prev.includes(id) ? prev.filter(s => s !== id) : [...prev, id]
        );
    };

    const updateCredential = (sourceId: string, field: string, value: string) => {
        setCredentials(prev => ({
            ...prev,
            [sourceId]: { ...(prev[sourceId] || {}), [field]: value },
        }));
    };

    const launchHunt = async () => {
        if (!keyword.trim() || selectedSources.length === 0) {
            setHuntError("Please enter a keyword and select at least one source.");
            return;
        }
        setHuntError("");
        setIsSubmitting(true);
        try {
            const res = await api.post("/hunter/scrape-now", {
                keyword: keyword.trim(),
                location: location.trim() || undefined,
                sources: selectedSources,
                hs_code: hsCode.trim() || undefined,
                credentials: Object.keys(credentials).length > 0 ? credentials : undefined,
                hunt_type: "buyer",
            });
            // Add scraped results to leads immediately
            const newLeads = (res.data?.results || []).map((r: any, i: number) => ({
                id: `scraped-${Date.now()}-${i}`,
                ...r,
                status: "new",
            }));
            setLeads(prev => [...newLeads, ...prev]);
            setShowModal(false);
            setKeyword("");
            setLocation("");
            setSelectedSources([]);
            setCredentials({});
            setHsCode("");
        } catch (e: any) {
            setHuntError(e?.response?.data?.detail || "Failed to start hunt. Try again.");
        } finally {
            setIsSubmitting(false);
        }
    };

    const filtered = leads.filter(l => {
        const matchSearch = !searchQuery ||
            l.company_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
            l.contact_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
            l.email?.toLowerCase().includes(searchQuery.toLowerCase()) ||
            l.brand_name?.toLowerCase().includes(searchQuery.toLowerCase());
        const matchStatus = statusFilter === "all" || l.status === statusFilter;
        return matchSearch && matchStatus;
    });

    const authSources = selectedSources.filter(id => {
        const src = SOURCES.find(s => s.id === id);
        return src?.auth;
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
                    <p className="text-sm text-slate-500">AI-powered buyer discovery & multi-source lead generation</p>
                </div>
                <div className="flex gap-3">
                    <Button variant="outline" size="sm" onClick={() => { setLoading(true); fetchLeads(); }} className="border-slate-700 text-slate-400">
                        <RefreshCw className="w-4 h-4 mr-2" /> Refresh
                    </Button>
                    <Button onClick={() => setShowModal(true)} className="bg-[#D4AF37] text-[#050A15] hover:bg-[#F3E5AB] font-bold">
                        <Plus className="w-4 h-4 mr-2" /> New Buyer Hunt
                    </Button>
                </div>
            </div>

            {/* Stats Bar */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {[
                    { label: "Total Leads", value: leads.length, icon: Users, color: "text-blue-400" },
                    { label: "With Email", value: leads.filter(l => l.email).length, icon: Mail, color: "text-emerald-400" },
                    { label: "With Phone", value: leads.filter(l => l.phone).length, icon: Phone, color: "text-amber-400" },
                    { label: "Sources Used", value: [...new Set(leads.map(l => l.source).filter(Boolean))].length, icon: Globe, color: "text-purple-400" },
                ].map((stat, i) => (
                    <div key={i} className="bg-[#0F172A] border border-[#1E293B] rounded-lg p-4">
                        <div className="flex items-center gap-2 mb-1">
                            <stat.icon className={`w-4 h-4 ${stat.color}`} />
                            <span className="text-xs text-slate-500 uppercase tracking-wider">{stat.label}</span>
                        </div>
                        <p className="text-2xl font-bold text-white">{stat.value}</p>
                    </div>
                ))}
            </div>

            {/* Filters */}
            <div className="flex flex-col md:flex-row gap-3">
                <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                    <input
                        type="text"
                        placeholder="Search by company, contact, email, or brand..."
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
                            Start discovering potential buyers by scraping Google Maps, LinkedIn, Telegram, and more.
                        </p>
                        <Button onClick={() => setShowModal(true)} className="bg-[#D4AF37] text-[#050A15] hover:bg-[#F3E5AB] font-bold px-6 py-6 border border-[#D4AF37]">
                            <Target className="w-5 h-5 mr-2" /> Launch First Buyer Hunt
                        </Button>
                    </CardContent>
                </Card>
            ) : (
                <div className="space-y-3">
                    <p className="text-xs text-slate-500 uppercase tracking-widest">{filtered.length} results</p>
                    {filtered.map((lead) => (
                        <Card key={lead.id} className="bg-[#0F172A] border-[#1E293B] hover:border-[#D4AF37]/30 transition-colors">
                            <CardContent className="p-4 flex flex-col md:flex-row justify-between items-start md:items-center gap-3">
                                <div className="flex items-start gap-3 min-w-0 flex-1">
                                    <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center shrink-0">
                                        <Building2 className="w-5 h-5 text-blue-400" />
                                    </div>
                                    <div className="min-w-0 flex-1">
                                        <h4 className="text-white font-bold truncate">{lead.company_name || "Unknown Company"}</h4>
                                        <div className="flex items-center gap-3 text-xs text-slate-500 mt-1 flex-wrap">
                                            {lead.contact_name && <span className="flex items-center gap-1"><Users className="w-3 h-3" /> {lead.contact_name}</span>}
                                            {lead.country && <span className="flex items-center gap-1"><MapPin className="w-3 h-3" /> {lead.country}</span>}
                                            {lead.email && <span className="flex items-center gap-1"><Mail className="w-3 h-3" /> {lead.email}</span>}
                                            {lead.phone && <span className="flex items-center gap-1"><Phone className="w-3 h-3" /> {lead.phone}</span>}
                                            {lead.brand_name && <span className="flex items-center gap-1"><Store className="w-3 h-3" /> {lead.brand_name}</span>}
                                            {lead.price && <span className="flex items-center gap-1"><DollarSign className="w-3 h-3" /> {lead.price}</span>}
                                        </div>
                                    </div>
                                </div>
                                <div className="flex items-center gap-2 shrink-0 flex-wrap">
                                    {lead.source && (
                                        <Badge variant="outline" className="text-xs border-slate-700 text-slate-400">
                                            {lead.source}
                                        </Badge>
                                    )}
                                    {lead.score != null && (
                                        <Badge className={`${lead.score >= 70 ? "bg-emerald-500/10 text-emerald-400" : lead.score >= 40 ? "bg-amber-500/10 text-amber-400" : "bg-slate-500/10 text-slate-400"} border-none text-xs`}>
                                            Score: {lead.score}
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

            {/* ═══════════ New Hunt Modal ═══════════ */}
            {showModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
                    <div className="bg-[#0F172A] border border-[#1E293B] rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto shadow-2xl">
                        {/* Modal Header */}
                        <div className="flex items-center justify-between p-6 border-b border-[#1E293B]">
                            <div>
                                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                                    <Target className="w-5 h-5 text-[#D4AF37]" />
                                    New Buyer Hunt
                                </h2>
                                <p className="text-sm text-slate-500 mt-1">Select sources and enter your search criteria</p>
                            </div>
                            <button onClick={() => setShowModal(false)} className="p-2 hover:bg-slate-800 rounded-lg transition-colors">
                                <X className="w-5 h-5 text-slate-400" />
                            </button>
                        </div>

                        {/* Modal Body */}
                        <div className="p-6 space-y-6">
                            {/* Search Criteria */}
                            <div className="space-y-4">
                                <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">Search Criteria</h3>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div>
                                        <label className="text-xs text-slate-500 mb-1 block">Keyword / Product *</label>
                                        <input
                                            type="text"
                                            placeholder="e.g. olive oil, steel pipes"
                                            value={keyword}
                                            onChange={(e) => setKeyword(e.target.value)}
                                            className="w-full px-4 py-2.5 bg-[#050A15] border border-[#1E293B] rounded-lg text-white placeholder:text-slate-600 focus:outline-none focus:border-[#D4AF37]/50"
                                        />
                                    </div>
                                    <div>
                                        <label className="text-xs text-slate-500 mb-1 block">Location / Country</label>
                                        <input
                                            type="text"
                                            placeholder="e.g. UAE, Dubai, Germany"
                                            value={location}
                                            onChange={(e) => setLocation(e.target.value)}
                                            className="w-full px-4 py-2.5 bg-[#050A15] border border-[#1E293B] rounded-lg text-white placeholder:text-slate-600 focus:outline-none focus:border-[#D4AF37]/50"
                                        />
                                    </div>
                                </div>
                                <div>
                                    <label className="text-xs text-slate-500 mb-1 block">HS Code (optional, for TradeMap)</label>
                                    <input
                                        type="text"
                                        placeholder="e.g. 1509 (Olive Oil)"
                                        value={hsCode}
                                        onChange={(e) => setHsCode(e.target.value)}
                                        className="w-full px-4 py-2.5 bg-[#050A15] border border-[#1E293B] rounded-lg text-white placeholder:text-slate-600 focus:outline-none focus:border-[#D4AF37]/50"
                                    />
                                </div>
                            </div>

                            {/* Source Selector */}
                            <div className="space-y-3">
                                <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">Select Sources</h3>
                                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                                    {SOURCES.map((src) => {
                                        const isSelected = selectedSources.includes(src.id);
                                        return (
                                            <button
                                                key={src.id}
                                                onClick={() => toggleSource(src.id)}
                                                className={`relative flex items-center gap-3 p-3 rounded-xl border-2 transition-all duration-200 text-left ${
                                                    isSelected
                                                        ? `${src.bg} ${src.border} ring-1 ring-${src.color.replace("text-", "")}/20`
                                                        : "bg-[#050A15] border-[#1E293B] hover:border-slate-600"
                                                }`}
                                            >
                                                <div className={`w-8 h-8 rounded-lg ${src.bg} flex items-center justify-center shrink-0`}>
                                                    <src.icon className={`w-4 h-4 ${src.color}`} />
                                                </div>
                                                <div className="min-w-0">
                                                    <p className="text-sm font-medium text-white truncate">{src.label}</p>
                                                    {src.auth && <p className="text-[10px] text-slate-500">Login required</p>}
                                                </div>
                                                {isSelected && (
                                                    <div className="absolute top-2 right-2">
                                                        <Check className="w-4 h-4 text-[#D4AF37]" />
                                                    </div>
                                                )}
                                            </button>
                                        );
                                    })}
                                </div>
                            </div>

                            {/* Credentials Section (dynamic) */}
                            {authSources.length > 0 && (
                                <div className="space-y-4">
                                    <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-2">
                                        <AlertCircle className="w-4 h-4 text-amber-400" />
                                        Credentials
                                    </h3>
                                    <p className="text-xs text-slate-500">Enter your credentials for each source. These are encrypted and only used for this hunt.</p>
                                    {authSources.map((sourceId) => {
                                        const src = SOURCES.find(s => s.id === sourceId)!;
                                        return (
                                            <div key={sourceId} className={`p-4 rounded-xl ${src.bg} border ${src.border}`}>
                                                <div className="flex items-center gap-2 mb-3">
                                                    <src.icon className={`w-4 h-4 ${src.color}`} />
                                                    <span className="text-sm font-medium text-white">{src.label}</span>
                                                </div>
                                                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                                    {src.fields?.map((field) => (
                                                        <div key={field}>
                                                            <label className="text-xs text-slate-400 mb-1 block">{FIELD_LABELS[field] || field}</label>
                                                            <input
                                                                type={field === "password" ? "password" : "text"}
                                                                placeholder={FIELD_LABELS[field]}
                                                                value={credentials[sourceId]?.[field] || ""}
                                                                onChange={(e) => updateCredential(sourceId, field, e.target.value)}
                                                                className="w-full px-3 py-2 bg-[#050A15]/80 border border-[#1E293B] rounded-lg text-white text-sm placeholder:text-slate-600 focus:outline-none focus:border-[#D4AF37]/50"
                                                            />
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            )}

                            {/* Error */}
                            {huntError && (
                                <div className="flex items-center gap-2 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-sm text-red-400">
                                    <AlertCircle className="w-4 h-4 shrink-0" />
                                    {huntError}
                                </div>
                            )}
                        </div>

                        {/* Modal Footer */}
                        <div className="flex items-center justify-between p-6 border-t border-[#1E293B]">
                            <p className="text-xs text-slate-500">
                                {selectedSources.length} source{selectedSources.length !== 1 ? "s" : ""} selected
                            </p>
                            <div className="flex gap-3">
                                <Button variant="outline" onClick={() => setShowModal(false)} className="border-slate-700 text-slate-400">
                                    Cancel
                                </Button>
                                <Button
                                    onClick={launchHunt}
                                    disabled={isSubmitting || !keyword.trim() || selectedSources.length === 0}
                                    className="bg-[#D4AF37] text-[#050A15] hover:bg-[#F3E5AB] font-bold disabled:opacity-50"
                                >
                                    {isSubmitting ? (
                                        <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Starting...</>
                                    ) : (
                                        <><Target className="w-4 h-4 mr-2" /> Launch Hunt</>
                                    )}
                                </Button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
