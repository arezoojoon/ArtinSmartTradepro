"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Users, Plus, Search, X, Loader2, Globe, TrendingUp, TrendingDown, BarChart3, Target, Eye } from "lucide-react";
import api from "@/lib/api";

interface Competitor {
    id: string;
    name: string;
    website?: string;
    country: string;
    market_share?: number;
    pricing_level: string;
    strength: string;
    weakness: string;
    threat_level: string;
    notes?: string;
}

export default function CompetitorsPage() {
    const [competitors, setCompetitors] = useState<Competitor[]>([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState("");
    const [showModal, setShowModal] = useState(false);
    const [form, setForm] = useState({ name: "", website: "", country: "", pricing_level: "Medium", strength: "", weakness: "", threat_level: "Medium", notes: "" });
    const [saving, setSaving] = useState(false);

    const fetchCompetitors = async () => {
        try {
            const res = await api.get("/hunter/competitors");
            setCompetitors(Array.isArray(res.data) ? res.data : []);
        } catch { setCompetitors([]); }
        finally { setLoading(false); }
    };

    useEffect(() => { fetchCompetitors(); }, []);

    const handleCreate = async () => {
        if (!form.name) return;
        setSaving(true);
        try {
            await api.post("/hunter/competitors", {
                name: form.name, website: form.website || undefined,
                country: form.country, pricing_level: form.pricing_level,
                strength: form.strength, weakness: form.weakness,
                threat_level: form.threat_level, notes: form.notes || undefined,
            });
            setShowModal(false);
            setForm({ name: "", website: "", country: "", pricing_level: "Medium", strength: "", weakness: "", threat_level: "Medium", notes: "" });
            fetchCompetitors();
        } catch (e) { console.error("Failed to add competitor", e); }
        finally { setSaving(false); }
    };

    const threatColor = (level: string) => {
        switch (level?.toLowerCase()) {
            case "high": return "bg-rose-500/20 text-rose-400";
            case "low": return "bg-emerald-500/20 text-emerald-400";
            default: return "bg-amber-500/20 text-amber-400";
        }
    };

    const filtered = competitors.filter(c => c.name?.toLowerCase().includes(search.toLowerCase()) || c.country?.toLowerCase().includes(search.toLowerCase()));

    return (
        <div className="space-y-6 p-4 md:p-8 max-w-[1400px] mx-auto">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold flex items-center gap-2 text-white">
                        <Users className="h-6 w-6 text-orange-400" /> Competitor Analysis
                    </h1>
                    <p className="text-white/50 text-sm">Track competitors, pricing, and market positioning</p>
                </div>
                <Button onClick={() => setShowModal(true)} className="bg-[#f5a623] text-black hover:bg-[#e09000]">
                    <Plus className="h-4 w-4 mr-2" /> Add Competitor
                </Button>
            </div>

            {/* Stats */}
            <div className="grid gap-4 sm:grid-cols-3">
                <Card className="bg-[#0e1e33] border-[#1e3a5f]"><CardContent className="p-4 flex items-center justify-between">
                    <div><p className="text-white/50 text-xs uppercase">Tracked</p><p className="text-xl font-bold text-white mt-1">{competitors.length}</p></div>
                    <Eye className="h-7 w-7 text-blue-400/40" />
                </CardContent></Card>
                <Card className="bg-[#0e1e33] border-[#1e3a5f]"><CardContent className="p-4 flex items-center justify-between">
                    <div><p className="text-white/50 text-xs uppercase">High Threat</p><p className="text-xl font-bold text-rose-400 mt-1">{competitors.filter(c => c.threat_level?.toLowerCase() === "high").length}</p></div>
                    <Target className="h-7 w-7 text-rose-400/40" />
                </CardContent></Card>
                <Card className="bg-[#0e1e33] border-[#1e3a5f]"><CardContent className="p-4 flex items-center justify-between">
                    <div><p className="text-white/50 text-xs uppercase">Markets</p><p className="text-xl font-bold text-[#f5a623] mt-1">{new Set(competitors.map(c => c.country)).size}</p></div>
                    <Globe className="h-7 w-7 text-[#f5a623]/40" />
                </CardContent></Card>
            </div>

            {/* Search */}
            <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-white/30" />
                <Input placeholder="Search competitors..." value={search} onChange={e => setSearch(e.target.value)} className="pl-10 bg-[#0e1e33] border-[#1e3a5f] text-white" />
            </div>

            {/* Competitor Cards */}
            {loading ? (
                <div className="flex justify-center py-16"><Loader2 className="h-6 w-6 animate-spin text-white/40" /></div>
            ) : filtered.length === 0 ? (
                <Card className="bg-[#0e1e33] border-[#1e3a5f]"><CardContent className="py-16 text-center">
                    <Users className="h-12 w-12 mx-auto mb-3 text-white/10" />
                    <p className="text-white/40 text-sm">{competitors.length === 0 ? "No competitors tracked yet" : "No results"}</p>
                    {competitors.length === 0 && <Button onClick={() => setShowModal(true)} variant="link" className="text-[#f5a623] mt-2">Add your first competitor</Button>}
                </CardContent></Card>
            ) : (
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                    {filtered.map(comp => (
                        <Card key={comp.id} className="bg-[#0e1e33] border-[#1e3a5f] hover:border-orange-400/30 transition-colors">
                            <CardContent className="p-5 space-y-3">
                                <div className="flex items-start justify-between">
                                    <div>
                                        <h3 className="text-white font-semibold">{comp.name}</h3>
                                        <p className="text-white/40 text-xs flex items-center gap-1 mt-0.5"><Globe className="h-3 w-3" />{comp.country}</p>
                                    </div>
                                    <Badge className={`text-[10px] ${threatColor(comp.threat_level)}`}>{comp.threat_level} Threat</Badge>
                                </div>
                                {comp.website && <a href={comp.website} target="_blank" rel="noopener noreferrer" className="text-blue-400 text-xs hover:underline">{comp.website}</a>}
                                <div className="grid grid-cols-2 gap-3">
                                    <div className="p-2 bg-white/5 rounded-lg">
                                        <p className="text-white/40 text-[10px] uppercase">Pricing</p>
                                        <p className="text-white text-sm font-medium">{comp.pricing_level}</p>
                                    </div>
                                    <div className="p-2 bg-white/5 rounded-lg">
                                        <p className="text-white/40 text-[10px] uppercase">Market Share</p>
                                        <p className="text-white text-sm font-medium">{comp.market_share ? `${comp.market_share}%` : "N/A"}</p>
                                    </div>
                                </div>
                                <div className="space-y-1.5">
                                    {comp.strength && <div className="flex items-start gap-2"><TrendingUp className="h-3.5 w-3.5 text-emerald-400 mt-0.5 shrink-0" /><p className="text-white/60 text-xs">{comp.strength}</p></div>}
                                    {comp.weakness && <div className="flex items-start gap-2"><TrendingDown className="h-3.5 w-3.5 text-rose-400 mt-0.5 shrink-0" /><p className="text-white/60 text-xs">{comp.weakness}</p></div>}
                                </div>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            )}

            {/* Modal */}
            {showModal && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50" onClick={() => setShowModal(false)}>
                    <div className="bg-[#0e1e33] border border-[#1e3a5f] rounded-xl p-6 w-full max-w-md space-y-4" onClick={e => e.stopPropagation()}>
                        <div className="flex items-center justify-between">
                            <h3 className="text-white font-bold text-lg">Add Competitor</h3>
                            <button onClick={() => setShowModal(false)}><X className="h-5 w-5 text-white/40" /></button>
                        </div>
                        <div className="space-y-3">
                            <Input placeholder="Company Name *" value={form.name} onChange={e => setForm(p => ({ ...p, name: e.target.value }))} className="bg-white/5 border-white/10 text-white" />
                            <Input placeholder="Website" value={form.website} onChange={e => setForm(p => ({ ...p, website: e.target.value }))} className="bg-white/5 border-white/10 text-white" />
                            <Input placeholder="Country/Market" value={form.country} onChange={e => setForm(p => ({ ...p, country: e.target.value }))} className="bg-white/5 border-white/10 text-white" />
                            <div className="grid grid-cols-2 gap-3">
                                <div>
                                    <label className="text-white/50 text-xs">Pricing Level</label>
                                    <select value={form.pricing_level} onChange={e => setForm(p => ({ ...p, pricing_level: e.target.value }))} className="w-full p-2 bg-white/5 border border-white/10 text-white rounded-md text-sm">
                                        <option value="Low">Low</option><option value="Medium">Medium</option><option value="High">High</option><option value="Premium">Premium</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="text-white/50 text-xs">Threat Level</label>
                                    <select value={form.threat_level} onChange={e => setForm(p => ({ ...p, threat_level: e.target.value }))} className="w-full p-2 bg-white/5 border border-white/10 text-white rounded-md text-sm">
                                        <option value="Low">Low</option><option value="Medium">Medium</option><option value="High">High</option>
                                    </select>
                                </div>
                            </div>
                            <Input placeholder="Key Strength" value={form.strength} onChange={e => setForm(p => ({ ...p, strength: e.target.value }))} className="bg-white/5 border-white/10 text-white" />
                            <Input placeholder="Key Weakness" value={form.weakness} onChange={e => setForm(p => ({ ...p, weakness: e.target.value }))} className="bg-white/5 border-white/10 text-white" />
                            <Input placeholder="Notes" value={form.notes} onChange={e => setForm(p => ({ ...p, notes: e.target.value }))} className="bg-white/5 border-white/10 text-white" />
                        </div>
                        <Button onClick={handleCreate} disabled={saving || !form.name} className="w-full bg-[#f5a623] text-black hover:bg-[#e09000]">
                            {saving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Plus className="h-4 w-4 mr-2" />} Add Competitor
                        </Button>
                    </div>
                </div>
            )}
        </div>
    );
}
