"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
    Package, Plus, Search, ArrowRight, ExternalLink,
    MapPin, Building2, Star, Target, Factory, RefreshCw,
    Loader2, X, Check, AlertCircle, Mail, Phone,
    Globe, Users, DollarSign, Store,
    Linkedin, MessageCircle, Map, Globe2, Facebook,
    Send, Hash,
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
interface Supplier {
    id: string;
    company_name: string;
    contact_name?: string;
    email?: string;
    phone?: string;
    country?: string;
    product_category?: string;
    score?: number;
    status?: string;
    qualification?: string;
    source?: string;
    brand_name?: string;
    product_name?: string;
    price?: string;
    website?: string;
}

/* ───────── Component ───────── */
export default function SupplierLeadsPage() {
    const [suppliers, setSuppliers] = useState<Supplier[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState("");
    const [showModal, setShowModal] = useState(false);

    // Hunt form state
    const [selectedSources, setSelectedSources] = useState<string[]>([]);
    const [keyword, setKeyword] = useState("");
    const [location, setLocation] = useState("");
    const [hsCode, setHsCode] = useState("");
    const [credentials, setCredentials] = useState<Record<string, Record<string, string>>>({});
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [huntError, setHuntError] = useState("");

    const fetchSuppliers = useCallback(async () => {
        try {
            const res = await api.get("/hunter/search?type=supplier&limit=100");
            setSuppliers(res.data?.results || res.data || []);
        } catch (e) {
            console.error("Supplier leads fetch failed:", e);
            try {
                const fallback = await api.get("/crm/contacts?tag=supplier&limit=100");
                setSuppliers(fallback.data?.suppliers || fallback.data || []);
            } catch { /* ignore */ }
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { fetchSuppliers(); }, [fetchSuppliers]);

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
                hunt_type: "supplier",
            });
            // Add scraped results to suppliers immediately
            const newSuppliers = (res.data?.results || []).map((r: any, i: number) => ({
                id: `scraped-${Date.now()}-${i}`,
                ...r,
                status: "new",
            }));
            setSuppliers(prev => [...newSuppliers, ...prev]);
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

    const filtered = suppliers.filter(s =>
        !searchQuery ||
        s.company_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        s.country?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        s.product_category?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        s.brand_name?.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const authSources = selectedSources.filter(id => SOURCES.find(s => s.id === id)?.auth);

    return (
        <div className="min-h-screen bg-[#050A15] text-slate-300 p-4 md:p-8 space-y-6">
            {/* Header */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-[#1E293B] pb-6">
                <div>
                    <div className="flex items-center gap-3 mb-2">
                        <div className="p-2 bg-purple-500/10 rounded-md border border-purple-500/30">
                            <Package className="h-5 w-5 text-purple-400" />
                        </div>
                        <h1 className="text-2xl font-bold text-white uppercase tracking-tight">Supplier Leads</h1>
                    </div>
                    <p className="text-sm text-slate-500">Multi-source supplier discovery & qualification engine</p>
                </div>
                <div className="flex gap-3">
                    <Button variant="outline" size="sm" onClick={() => { setLoading(true); fetchSuppliers(); }} className="border-slate-700 text-slate-400">
                        <RefreshCw className="w-4 h-4 mr-2" /> Refresh
                    </Button>
                    <Button onClick={() => setShowModal(true)} className="bg-[#D4AF37] text-[#050A15] hover:bg-[#F3E5AB] font-bold">
                        <Plus className="w-4 h-4 mr-2" /> New Supplier Hunt
                    </Button>
                </div>
            </div>

            {/* Stats Bar */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {[
                    { label: "Total Suppliers", value: suppliers.length, icon: Factory, color: "text-purple-400" },
                    { label: "With Email", value: suppliers.filter(s => s.email).length, icon: Mail, color: "text-emerald-400" },
                    { label: "With Phone", value: suppliers.filter(s => s.phone).length, icon: Phone, color: "text-amber-400" },
                    { label: "Sources Used", value: [...new Set(suppliers.map(s => s.source).filter(Boolean))].length, icon: Globe, color: "text-blue-400" },
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

            {/* Search */}
            <div className="relative max-w-lg">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                <input
                    type="text"
                    placeholder="Search by company, country, category, or brand..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 bg-[#0F172A] border border-[#1E293B] rounded-lg text-white placeholder:text-slate-600 focus:outline-none focus:border-[#D4AF37]/50"
                />
            </div>

            {/* Results */}
            {loading ? (
                <div className="flex items-center justify-center py-20"><Loader2 className="h-8 w-8 animate-spin text-[#D4AF37]" /></div>
            ) : filtered.length === 0 ? (
                <Card className="bg-[#0F172A] border-[#1E293B]">
                    <CardContent className="py-20 flex flex-col items-center text-center">
                        <div className="w-20 h-20 rounded-full bg-emerald-500/10 flex items-center justify-center mb-6">
                            <Factory className="w-10 h-10 text-emerald-500" />
                        </div>
                        <h3 className="text-white font-bold text-2xl mb-3">No supplier leads yet</h3>
                        <p className="text-slate-400 max-w-md mx-auto mb-8 leading-relaxed">
                            Discover suppliers by scraping Google Maps, LinkedIn, Telegram groups, TradeMap, and more.
                        </p>
                        <Button onClick={() => setShowModal(true)} className="bg-[#D4AF37] text-[#050A15] hover:bg-[#F3E5AB] font-bold px-6 py-6 border border-[#D4AF37]">
                            <Target className="w-5 h-5 mr-2" /> Launch First Supplier Hunt
                        </Button>
                    </CardContent>
                </Card>
            ) : (
                <div className="space-y-3">
                    <p className="text-xs text-slate-500 uppercase tracking-widest">{filtered.length} suppliers</p>
                    {filtered.map((s) => (
                        <Card key={s.id} className="bg-[#0F172A] border-[#1E293B] hover:border-[#D4AF37]/30 transition-colors">
                            <CardContent className="p-4 flex flex-col md:flex-row justify-between items-start md:items-center gap-3">
                                <div className="flex items-start gap-3 min-w-0 flex-1">
                                    <div className="w-10 h-10 rounded-lg bg-purple-500/10 flex items-center justify-center shrink-0">
                                        <Building2 className="w-5 h-5 text-purple-400" />
                                    </div>
                                    <div className="min-w-0 flex-1">
                                        <h4 className="text-white font-bold truncate">{s.company_name || "Unknown Supplier"}</h4>
                                        <div className="flex items-center gap-3 text-xs text-slate-500 mt-1 flex-wrap">
                                            {s.contact_name && <span className="flex items-center gap-1"><Users className="w-3 h-3" />{s.contact_name}</span>}
                                            {s.country && <span className="flex items-center gap-1"><MapPin className="w-3 h-3" />{s.country}</span>}
                                            {s.email && <span className="flex items-center gap-1"><Mail className="w-3 h-3" />{s.email}</span>}
                                            {s.phone && <span className="flex items-center gap-1"><Phone className="w-3 h-3" />{s.phone}</span>}
                                            {s.product_category && <span className="flex items-center gap-1"><Package className="w-3 h-3" />{s.product_category}</span>}
                                            {s.brand_name && <span className="flex items-center gap-1"><Store className="w-3 h-3" />{s.brand_name}</span>}
                                            {s.price && <span className="flex items-center gap-1"><DollarSign className="w-3 h-3" />{s.price}</span>}
                                        </div>
                                    </div>
                                </div>
                                <div className="flex items-center gap-2 shrink-0 flex-wrap">
                                    {s.source && <Badge variant="outline" className="text-xs border-slate-700 text-slate-400">{s.source}</Badge>}
                                    {s.score != null && (
                                        <Badge className={`${s.score >= 70 ? "bg-emerald-500/10 text-emerald-400" : "bg-amber-500/10 text-amber-400"} border-none text-xs`}>
                                            <Star className="w-3 h-3 mr-1" /> {s.score}
                                        </Badge>
                                    )}
                                    <Button size="sm" variant="outline" onClick={() => window.location.href = `/crm/contacts?search=${encodeURIComponent(s.company_name || '')}`} className="border-[#D4AF37]/30 text-[#D4AF37] hover:bg-[#D4AF37]/10 text-xs">
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
                                    New Supplier Hunt
                                </h2>
                                <p className="text-sm text-slate-500 mt-1">Find new suppliers across multiple sources</p>
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
                                        <label className="text-xs text-slate-500 mb-1 block">Product / Material *</label>
                                        <input type="text" placeholder="e.g. olive oil, steel pipes" value={keyword} onChange={(e) => setKeyword(e.target.value)}
                                            className="w-full px-4 py-2.5 bg-[#050A15] border border-[#1E293B] rounded-lg text-white placeholder:text-slate-600 focus:outline-none focus:border-[#D4AF37]/50" />
                                    </div>
                                    <div>
                                        <label className="text-xs text-slate-500 mb-1 block">Country / Region</label>
                                        <input type="text" placeholder="e.g. Turkey, China" value={location} onChange={(e) => setLocation(e.target.value)}
                                            className="w-full px-4 py-2.5 bg-[#050A15] border border-[#1E293B] rounded-lg text-white placeholder:text-slate-600 focus:outline-none focus:border-[#D4AF37]/50" />
                                    </div>
                                </div>
                                <div>
                                    <label className="text-xs text-slate-500 mb-1 block">HS Code (optional, for TradeMap)</label>
                                    <input type="text" placeholder="e.g. 1509 (Olive Oil)" value={hsCode} onChange={(e) => setHsCode(e.target.value)}
                                        className="w-full px-4 py-2.5 bg-[#050A15] border border-[#1E293B] rounded-lg text-white placeholder:text-slate-600 focus:outline-none focus:border-[#D4AF37]/50" />
                                </div>
                            </div>

                            {/* Source Selector */}
                            <div className="space-y-3">
                                <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">Select Sources</h3>
                                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                                    {SOURCES.map((src) => {
                                        const isSelected = selectedSources.includes(src.id);
                                        return (
                                            <button key={src.id} onClick={() => toggleSource(src.id)}
                                                className={`relative flex items-center gap-3 p-3 rounded-xl border-2 transition-all duration-200 text-left ${
                                                    isSelected ? `${src.bg} ${src.border}` : "bg-[#050A15] border-[#1E293B] hover:border-slate-600"
                                                }`}>
                                                <div className={`w-8 h-8 rounded-lg ${src.bg} flex items-center justify-center shrink-0`}>
                                                    <src.icon className={`w-4 h-4 ${src.color}`} />
                                                </div>
                                                <div className="min-w-0">
                                                    <p className="text-sm font-medium text-white truncate">{src.label}</p>
                                                    {src.auth && <p className="text-[10px] text-slate-500">Login required</p>}
                                                </div>
                                                {isSelected && <div className="absolute top-2 right-2"><Check className="w-4 h-4 text-[#D4AF37]" /></div>}
                                            </button>
                                        );
                                    })}
                                </div>
                            </div>

                            {/* Credentials */}
                            {authSources.length > 0 && (
                                <div className="space-y-4">
                                    <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-2">
                                        <AlertCircle className="w-4 h-4 text-amber-400" /> Credentials
                                    </h3>
                                    <p className="text-xs text-slate-500">Enter your credentials for each source. Encrypted and used only for this hunt.</p>
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
                                                            <input type={field === "password" ? "password" : "text"}
                                                                placeholder={FIELD_LABELS[field]}
                                                                value={credentials[sourceId]?.[field] || ""}
                                                                onChange={(e) => updateCredential(sourceId, field, e.target.value)}
                                                                className="w-full px-3 py-2 bg-[#050A15]/80 border border-[#1E293B] rounded-lg text-white text-sm placeholder:text-slate-600 focus:outline-none focus:border-[#D4AF37]/50" />
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            )}

                            {huntError && (
                                <div className="flex items-center gap-2 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-sm text-red-400">
                                    <AlertCircle className="w-4 h-4 shrink-0" /> {huntError}
                                </div>
                            )}
                        </div>

                        {/* Modal Footer */}
                        <div className="flex items-center justify-between p-6 border-t border-[#1E293B]">
                            <p className="text-xs text-slate-500">{selectedSources.length} source{selectedSources.length !== 1 ? "s" : ""} selected</p>
                            <div className="flex gap-3">
                                <Button variant="outline" onClick={() => setShowModal(false)} className="border-slate-700 text-slate-400">Cancel</Button>
                                <Button onClick={launchHunt} disabled={isSubmitting || !keyword.trim() || selectedSources.length === 0}
                                    className="bg-[#D4AF37] text-[#050A15] hover:bg-[#F3E5AB] font-bold disabled:opacity-50">
                                    {isSubmitting ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Starting...</> : <><Target className="w-4 h-4 mr-2" /> Launch Hunt</>}
                                </Button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
