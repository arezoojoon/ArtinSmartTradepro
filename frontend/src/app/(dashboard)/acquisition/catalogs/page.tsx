"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
    BookOpen, Plus, Search, Loader2, RefreshCw,
    Package, Eye, Download, Image, ExternalLink, X, Trash2,
} from "lucide-react";
import api from "@/lib/api";

interface Catalog {
    id: string;
    title_en?: string;
    title_fa?: string;
    url?: string;
    pdf_url?: string;
    keywords?: string;
    clicks?: number;
    enabled?: boolean;
    language?: string;
    created_at?: string;
}

const EMPTY_FORM = { title_en: "", title_fa: "", url: "", pdf_url: "", keywords: "", language: "en" };

export default function CatalogsPage() {
    const [catalogs, setCatalogs] = useState<Catalog[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState("");
    const [showModal, setShowModal] = useState(false);
    const [saving, setSaving] = useState(false);
    const [form, setForm] = useState(EMPTY_FORM);

    const fetchCatalogs = useCallback(async () => {
        try {
            const res = await api.get("/catalogs");
            setCatalogs(res.data?.catalogs || res.data || []);
        } catch (e) {
            console.error("Catalogs fetch failed:", e);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { fetchCatalogs(); }, [fetchCatalogs]);

    const handleCreate = async () => {
        if (!form.title_en.trim() && !form.title_fa.trim()) return;
        setSaving(true);
        try {
            await api.post("/catalogs", form);
            setShowModal(false);
            setForm(EMPTY_FORM);
            setLoading(true);
            fetchCatalogs();
        } catch (e) { console.error("Create failed:", e); }
        finally { setSaving(false); }
    };

    const handleDelete = async (id: string) => {
        if (!confirm("Delete this catalog?")) return;
        try {
            await api.delete(`/catalogs/${id}`);
            setCatalogs(prev => prev.filter(c => c.id !== id));
        } catch (e) { console.error("Delete failed:", e); }
    };

    const handleShare = (catalog: Catalog) => {
        const url = catalog.url || catalog.pdf_url || window.location.href;
        navigator.clipboard.writeText(url).then(() => {
            // Brief visual feedback
            const btn = document.activeElement as HTMLElement;
            if (btn) btn.textContent = "Copied!";
            setTimeout(() => { if (btn) btn.textContent = "Share"; }, 1500);
        });
    };

    const handleView = (catalog: Catalog) => {
        const url = catalog.url || catalog.pdf_url;
        if (url) {
            window.open(url, "_blank");
        }
    };

    const title = (c: Catalog) => c.title_en || c.title_fa || "Untitled";

    const filtered = catalogs.filter(c =>
        !searchQuery || title(c).toLowerCase().includes(searchQuery.toLowerCase())
    );

    return (
        <div className="min-h-screen bg-[#050A15] text-slate-300 p-4 md:p-8 space-y-6">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-[#1E293B] pb-6">
                <div>
                    <div className="flex items-center gap-3 mb-2">
                        <div className="p-2 bg-[#D4AF37]/10 rounded-md border border-[#D4AF37]/30">
                            <BookOpen className="h-5 w-5 text-[#D4AF37]" />
                        </div>
                        <h1 className="text-2xl font-bold text-white uppercase tracking-tight">Catalogs</h1>
                    </div>
                    <p className="text-sm text-slate-500">Manage product catalogs for exhibitions and digital showcases</p>
                </div>
                <div className="flex gap-3">
                    <Button variant="outline" size="sm" onClick={() => { setLoading(true); fetchCatalogs(); }} className="border-slate-700 text-slate-400">
                        <RefreshCw className="w-4 h-4 mr-2" /> Refresh
                    </Button>
                    <Button onClick={() => setShowModal(true)} className="bg-[#D4AF37] text-[#050A15] hover:bg-[#F3E5AB] font-bold">
                        <Plus className="w-4 h-4 mr-2" /> New Catalog
                    </Button>
                </div>
            </div>

            {/* Search */}
            <div className="relative max-w-lg">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                <input type="text" placeholder="Search catalogs..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 bg-[#0F172A] border border-[#1E293B] rounded-lg text-white placeholder:text-slate-600 focus:outline-none focus:border-[#D4AF37]/50" />
            </div>

            {loading ? (
                <div className="flex items-center justify-center py-20"><Loader2 className="h-8 w-8 animate-spin text-[#D4AF37]" /></div>
            ) : filtered.length === 0 ? (
                <Card className="bg-[#0F172A] border-[#1E293B]">
                    <CardContent className="py-16 text-center">
                        <BookOpen className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                        <h3 className="text-white font-bold text-lg mb-2">No catalogs yet</h3>
                        <p className="text-slate-500 text-sm mb-6">Create your first product catalog for the exhibition</p>
                        <Button onClick={() => setShowModal(true)} className="bg-[#D4AF37] text-[#050A15] hover:bg-[#F3E5AB] font-bold">
                            <Plus className="w-4 h-4 mr-2" /> Create Catalog
                        </Button>
                    </CardContent>
                </Card>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                    {filtered.map((catalog) => (
                        <Card key={catalog.id} className="bg-[#0F172A] border-[#1E293B] hover:border-[#D4AF37]/30 transition-colors overflow-hidden group">
                            <div className="h-32 bg-gradient-to-br from-[#1E293B] to-[#0F172A] flex items-center justify-center relative">
                                <Image className="w-10 h-10 text-slate-700" />
                                {catalog.language && (
                                    <Badge className="absolute top-2 right-2 bg-[#D4AF37]/20 text-[#D4AF37] border-none text-[10px]">{catalog.language.toUpperCase()}</Badge>
                                )}
                                <Button variant="ghost" size="icon" onClick={() => handleDelete(catalog.id)} className="absolute top-2 left-2 opacity-0 group-hover:opacity-100 text-red-400 hover:text-red-300 hover:bg-red-900/20">
                                    <Trash2 className="w-4 h-4" />
                                </Button>
                            </div>
                            <CardContent className="p-4">
                                <h3 className="text-white font-bold truncate group-hover:text-[#D4AF37] transition-colors">{title(catalog)}</h3>
                                {catalog.keywords && <p className="text-xs text-slate-500 mt-1 line-clamp-2">{catalog.keywords}</p>}
                                <div className="flex items-center gap-3 mt-3 text-xs text-slate-500">
                                    {catalog.clicks != null && (
                                        <span className="flex items-center gap-1"><Eye className="w-3 h-3" /> {catalog.clicks} clicks</span>
                                    )}
                                    <Badge className={catalog.enabled ? "bg-emerald-500/10 text-emerald-400 border-none text-[10px]" : "bg-red-500/10 text-red-400 border-none text-[10px]"}>
                                        {catalog.enabled ? "Active" : "Disabled"}
                                    </Badge>
                                </div>
                                <div className="flex gap-2 mt-4">
                                    <Button size="sm" variant="outline" onClick={() => handleView(catalog)} className="border-[#D4AF37]/30 text-[#D4AF37] hover:bg-[#D4AF37]/10 text-xs flex-1">
                                        <Eye className="w-3 h-3 mr-1" /> View
                                    </Button>
                                    <Button size="sm" variant="outline" onClick={() => handleShare(catalog)} className="border-slate-700 text-slate-400 text-xs flex-1">
                                        <ExternalLink className="w-3 h-3 mr-1" /> Share
                                    </Button>
                                </div>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            )}

            {/* Create Catalog Modal */}
            {showModal && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={() => setShowModal(false)}>
                    <div className="bg-[#0F172A] border border-[#1E293B] rounded-2xl p-6 w-full max-w-md space-y-4" onClick={e => e.stopPropagation()}>
                        <div className="flex justify-between items-center">
                            <h3 className="text-white font-bold text-lg">New Catalog</h3>
                            <button onClick={() => setShowModal(false)} className="text-slate-500 hover:text-white"><X className="w-5 h-5" /></button>
                        </div>
                        <div className="space-y-3">
                            <input placeholder="Title (English) *" value={form.title_en} onChange={e => setForm(p => ({ ...p, title_en: e.target.value }))} className="w-full bg-[#050A15] border border-[#1E293B] rounded-lg px-4 py-2.5 text-white placeholder-slate-600 text-sm focus:border-[#D4AF37] outline-none" />
                            <input placeholder="Title (فارسی)" value={form.title_fa} onChange={e => setForm(p => ({ ...p, title_fa: e.target.value }))} className="w-full bg-[#050A15] border border-[#1E293B] rounded-lg px-4 py-2.5 text-white placeholder-slate-600 text-sm focus:border-[#D4AF37] outline-none" dir="rtl" />
                            <input placeholder="URL (website link)" value={form.url} onChange={e => setForm(p => ({ ...p, url: e.target.value }))} className="w-full bg-[#050A15] border border-[#1E293B] rounded-lg px-4 py-2.5 text-white placeholder-slate-600 text-sm focus:border-[#D4AF37] outline-none" />
                            <input placeholder="PDF URL" value={form.pdf_url} onChange={e => setForm(p => ({ ...p, pdf_url: e.target.value }))} className="w-full bg-[#050A15] border border-[#1E293B] rounded-lg px-4 py-2.5 text-white placeholder-slate-600 text-sm focus:border-[#D4AF37] outline-none" />
                            <input placeholder="Keywords (comma separated)" value={form.keywords} onChange={e => setForm(p => ({ ...p, keywords: e.target.value }))} className="w-full bg-[#050A15] border border-[#1E293B] rounded-lg px-4 py-2.5 text-white placeholder-slate-600 text-sm focus:border-[#D4AF37] outline-none" />
                            <select value={form.language} onChange={e => setForm(p => ({ ...p, language: e.target.value }))} className="w-full bg-[#050A15] border border-[#1E293B] rounded-lg px-4 py-2.5 text-white text-sm focus:border-[#D4AF37] outline-none">
                                <option value="en">English</option>
                                <option value="fa">فارسی</option>
                                <option value="ar">عربی</option>
                                <option value="ru">Russian</option>
                            </select>
                        </div>
                        <Button onClick={handleCreate} disabled={saving || (!form.title_en.trim() && !form.title_fa.trim())} className="w-full bg-[#D4AF37] text-[#050A15] hover:bg-[#F3E5AB] font-bold disabled:opacity-40">
                            {saving ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Plus className="w-4 h-4 mr-2" />}
                            {saving ? "Creating..." : "Create Catalog"}
                        </Button>
                    </div>
                </div>
            )}
        </div>
    );
}
