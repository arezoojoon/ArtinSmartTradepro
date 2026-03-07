"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
    BookOpen, Plus, Search, Loader2, RefreshCw,
    Package, Eye, Download, Image, ExternalLink,
} from "lucide-react";
import expoApi from "@/lib/expoApi";

interface Catalog {
    id: number;
    title: string;
    description?: string;
    cover_image?: string;
    products_count?: number;
    downloads?: number;
    status?: string;
    created_at?: string;
}

export default function CatalogsPage() {
    const [catalogs, setCatalogs] = useState<Catalog[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState("");

    const fetchCatalogs = useCallback(async () => {
        try {
            const res = await expoApi.get("/api/catalogs");
            setCatalogs(res.data?.catalogs || res.data || []);
        } catch (e) {
            console.error("Catalogs fetch failed:", e);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { fetchCatalogs(); }, [fetchCatalogs]);

    const filtered = catalogs.filter(c =>
        !searchQuery || c.title?.toLowerCase().includes(searchQuery.toLowerCase())
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
                    <Button onClick={() => alert('Opening Catalog Builder...')} className="bg-[#D4AF37] text-[#050A15] hover:bg-[#F3E5AB] font-bold">
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
                        <Button onClick={() => alert('Opening Catalog Builder...')} className="bg-[#D4AF37] text-[#050A15] hover:bg-[#F3E5AB] font-bold">
                            <Plus className="w-4 h-4 mr-2" /> Create Catalog
                        </Button>
                    </CardContent>
                </Card>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                    {filtered.map((catalog) => (
                        <Card key={catalog.id} className="bg-[#0F172A] border-[#1E293B] hover:border-[#D4AF37]/30 transition-colors overflow-hidden group">
                            <div className="h-40 bg-gradient-to-br from-[#1E293B] to-[#0F172A] flex items-center justify-center">
                                {catalog.cover_image ? (
                                    <img src={catalog.cover_image} alt={catalog.title} className="w-full h-full object-cover" />
                                ) : (
                                    <Image className="w-12 h-12 text-slate-700" />
                                )}
                            </div>
                            <CardContent className="p-4">
                                <h3 className="text-white font-bold truncate group-hover:text-[#D4AF37] transition-colors">{catalog.title}</h3>
                                {catalog.description && <p className="text-xs text-slate-500 mt-1 line-clamp-2">{catalog.description}</p>}
                                <div className="flex items-center gap-3 mt-3 text-xs text-slate-500">
                                    {catalog.products_count != null && (
                                        <span className="flex items-center gap-1"><Package className="w-3 h-3" /> {catalog.products_count} products</span>
                                    )}
                                    {catalog.downloads != null && (
                                        <span className="flex items-center gap-1"><Download className="w-3 h-3" /> {catalog.downloads} downloads</span>
                                    )}
                                </div>
                                <div className="flex gap-2 mt-4">
                                    <Button size="sm" variant="outline" onClick={() => alert(`Opening ${catalog.title}...`)} className="border-[#D4AF37]/30 text-[#D4AF37] hover:bg-[#D4AF37]/10 text-xs flex-1">
                                        <Eye className="w-3 h-3 mr-1" /> View
                                    </Button>
                                    <Button size="sm" variant="outline" onClick={() => alert(`Share link for ${catalog.title} copied to clipboard!`)} className="border-slate-700 text-slate-400 text-xs flex-1">
                                        <ExternalLink className="w-3 h-3 mr-1" /> Share
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
