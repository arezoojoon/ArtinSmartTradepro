"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
    Package, Plus, Search, Filter, ArrowDownUp,
    Download, ExternalLink, ShieldCheck, MapPin,
    Building2, Star, Target, Factory, RefreshCw,
    Loader2, ArrowRight
} from "lucide-react";
import api from "@/lib/api";

interface Supplier {
    id: string;
    company_name: string;
    contact_name?: string;
    country?: string;
    product_category?: string;
    score?: number;
    status?: string;
    qualification?: string;
}

export default function SupplierLeadsPage() {
    const [suppliers, setSuppliers] = useState<Supplier[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState("");

    const fetchSuppliers = useCallback(async () => {
        try {
            const res = await api.get("/hunter/search?type=supplier&limit=50");
            setSuppliers(res.data?.results || res.data || []);
        } catch (e) {
            console.error("Supplier leads fetch failed:", e);
            try {
                const fallback = await api.get("/crm/contacts?tag=supplier&limit=50");
                setSuppliers(fallback.data?.suppliers || fallback.data || []);
            } catch { /* ignore */ }
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { fetchSuppliers(); }, [fetchSuppliers]);

    const filtered = suppliers.filter(s =>
        !searchQuery ||
        s.company_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        s.country?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        s.product_category?.toLowerCase().includes(searchQuery.toLowerCase())
    );

    return (
        <div className="min-h-screen bg-[#050A15] text-slate-300 p-4 md:p-8 space-y-6">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-[#1E293B] pb-6">
                <div>
                    <div className="flex items-center gap-3 mb-2">
                        <div className="p-2 bg-purple-500/10 rounded-md border border-purple-500/30">
                            <Package className="h-5 w-5 text-purple-400" />
                        </div>
                        <h1 className="text-2xl font-bold text-white uppercase tracking-tight">Supplier Leads</h1>
                    </div>
                    <p className="text-sm text-slate-500">RFQ matching, supplier scoring & qualification — powered by Hunter engine</p>
                </div>
                <div className="flex gap-3">
                    <Button variant="outline" size="sm" onClick={() => { setLoading(true); fetchSuppliers(); }} className="border-slate-700 text-slate-400">
                        <RefreshCw className="w-4 h-4 mr-2" /> Refresh
                    </Button>
                    <Button
                        onClick={() => document.querySelector('input')?.focus()}
                        className="bg-[#D4AF37] text-[#050A15] hover:bg-[#F3E5AB] font-bold"
                    >
                        <Plus className="w-4 h-4 mr-2" /> Launch Supplier Hunt
                    </Button>
                </div>
            </div>

            {/* Search */}
            <div className="relative max-w-lg">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                <input
                    type="text"
                    placeholder="Search by company, country, or category..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 bg-[#0F172A] border border-[#1E293B] rounded-lg text-white placeholder:text-slate-600 focus:outline-none focus:border-[#D4AF37]/50"
                />
            </div>

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
                            Discover and qualify new suppliers for your supply chain using the AI-powered Hunter engine.
                        </p>
                        <Button
                            onClick={() => document.querySelector('input')?.focus()}
                            className="bg-[#D4AF37] text-[#050A15] hover:bg-[#F3E5AB] font-bold px-6 py-6 border border-[#D4AF37]"
                        >
                            <Target className="w-5 h-5 mr-2" />
                            Run First Supplier Search
                        </Button>
                    </CardContent>
                </Card>
            ) : (
                <div className="space-y-3">
                    <p className="text-xs text-slate-500 uppercase tracking-widest">{filtered.length} suppliers</p>
                    {filtered.map((s) => (
                        <Card key={s.id} className="bg-[#0F172A] border-[#1E293B] hover:border-[#D4AF37]/30 transition-colors">
                            <CardContent className="p-4 flex flex-col md:flex-row justify-between items-start md:items-center gap-3">
                                <div className="flex items-start gap-3 min-w-0">
                                    <div className="w-10 h-10 rounded-lg bg-purple-500/10 flex items-center justify-center shrink-0">
                                        <Building2 className="w-5 h-5 text-purple-400" />
                                    </div>
                                    <div className="min-w-0">
                                        <h4 className="text-white font-bold truncate">{s.company_name || "Unknown Supplier"}</h4>
                                        <div className="flex items-center gap-3 text-xs text-slate-500 mt-1 flex-wrap">
                                            {s.country && <span className="flex items-center gap-1"><MapPin className="w-3 h-3" />{s.country}</span>}
                                            {s.product_category && <span className="flex items-center gap-1"><Package className="w-3 h-3" />{s.product_category}</span>}
                                        </div>
                                    </div>
                                </div>
                                <div className="flex items-center gap-3 shrink-0">
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
        </div>
    );
}
