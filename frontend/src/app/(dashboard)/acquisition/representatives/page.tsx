"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
    UserCheck, Plus, Search, Loader2, RefreshCw,
    Mail, Phone, MapPin, Star, X, Trash2,
} from "lucide-react";
import api from "@/lib/api";

interface Representative {
    id: string;
    contact_person: string;
    email?: string;
    phone?: string;
    country?: string;
    city?: string;
    address?: string;
    rep_type?: string;
    office_name?: string;
    is_active?: boolean;
}

const EMPTY_FORM = { contact_person: "", email: "", phone: "", country: "", city: "", address: "", rep_type: "personal", office_name: "" };

export default function RepresentativesPage() {
    const [reps, setReps] = useState<Representative[]>([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [saving, setSaving] = useState(false);
    const [form, setForm] = useState(EMPTY_FORM);

    const fetchReps = useCallback(async () => {
        try {
            const res = await api.get("/representatives");
            setReps(res.data?.representatives || res.data || []);
        } catch { /* ignore */ }
        finally { setLoading(false); }
    }, []);

    useEffect(() => { fetchReps(); }, [fetchReps]);

    const handleCreate = async () => {
        if (!form.contact_person.trim()) return;
        setSaving(true);
        try {
            await api.post("/representatives", form);
            setShowModal(false);
            setForm(EMPTY_FORM);
            setLoading(true);
            fetchReps();
        } catch (e) {
            console.error("Failed to create rep:", e);
        } finally { setSaving(false); }
    };

    const handleDelete = async (id: string) => {
        if (!confirm("Delete this representative?")) return;
        try {
            await api.delete(`/representatives/${id}`);
            setReps(prev => prev.filter(r => r.id !== id));
        } catch (e) { console.error("Delete failed:", e); }
    };

    return (
        <div className="min-h-screen bg-[#050A15] text-slate-300 p-4 md:p-8 space-y-6">
            <div className="flex justify-between items-center border-b border-[#1E293B] pb-6">
                <div>
                    <h1 className="text-2xl font-bold text-white uppercase flex items-center gap-3">
                        <UserCheck className="h-5 w-5 text-[#D4AF37]" /> Representatives
                    </h1>
                    <p className="text-sm text-slate-500 mt-1">Manage booth reps &amp; track performance</p>
                </div>
                <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm" onClick={() => { setLoading(true); fetchReps(); }} className="border-slate-700 text-slate-400">
                        <RefreshCw className="w-4 h-4 mr-2" /> Refresh
                    </Button>
                    <Button onClick={() => setShowModal(true)} className="bg-[#D4AF37] text-[#050A15] hover:bg-[#F3E5AB] font-bold">
                        <Plus className="w-4 h-4 mr-2" /> Add Rep
                    </Button>
                </div>
            </div>

            {loading ? (
                <div className="flex justify-center py-20"><Loader2 className="h-8 w-8 animate-spin text-[#D4AF37]" /></div>
            ) : reps.length === 0 ? (
                <Card className="bg-[#0F172A] border-[#1E293B]">
                    <CardContent className="py-16 text-center">
                        <UserCheck className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                        <h3 className="text-white font-bold text-lg mb-2">No representatives yet</h3>
                        <p className="text-slate-500 text-sm mb-4">Add booth reps to track lead capture</p>
                        <Button onClick={() => setShowModal(true)} className="bg-[#D4AF37] text-[#050A15] hover:bg-[#F3E5AB] font-bold">
                            <Plus className="w-4 h-4 mr-2" /> Add Your First Rep
                        </Button>
                    </CardContent>
                </Card>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                    {reps.map((r) => (
                        <Card key={r.id} className="bg-[#0F172A] border-[#1E293B] hover:border-[#D4AF37]/30 group">
                            <CardContent className="p-5">
                                <div className="flex items-center justify-between mb-3">
                                    <div className="flex items-center gap-3">
                                        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#D4AF37] to-[#B8860B] flex items-center justify-center text-black font-bold">
                                            {r.contact_person?.[0] || "?"}
                                        </div>
                                        <div>
                                            <h4 className="text-white font-bold">{r.contact_person}</h4>
                                            {r.rep_type && <p className="text-xs text-[#D4AF37]">{r.rep_type}{r.office_name ? ` — ${r.office_name}` : ""}</p>}
                                        </div>
                                    </div>
                                    <Button variant="ghost" size="icon" onClick={() => handleDelete(r.id)} className="opacity-0 group-hover:opacity-100 text-red-400 hover:text-red-300 hover:bg-red-900/20">
                                        <Trash2 className="w-4 h-4" />
                                    </Button>
                                </div>
                                <div className="space-y-1.5 text-xs text-slate-500">
                                    {r.email && <p className="flex items-center gap-2"><Mail className="w-3 h-3" />{r.email}</p>}
                                    {r.phone && <p className="flex items-center gap-2"><Phone className="w-3 h-3" />{r.phone}</p>}
                                    {r.country && <p className="flex items-center gap-2"><MapPin className="w-3 h-3" />{r.country}{r.city ? `, ${r.city}` : ""}</p>}
                                </div>
                                {r.is_active != null && (
                                    <div className="mt-3 pt-3 border-t border-[#1E293B] flex justify-between items-center">
                                        <span className="text-xs text-slate-500">Status</span>
                                        <Badge className={r.is_active ? "bg-emerald-500/10 text-emerald-400 border-none" : "bg-red-500/10 text-red-400 border-none"}>
                                            {r.is_active ? "Active" : "Inactive"}
                                        </Badge>
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    ))}
                </div>
            )}

            {/* Add Representative Modal */}
            {showModal && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={() => setShowModal(false)}>
                    <div className="bg-[#0F172A] border border-[#1E293B] rounded-2xl p-6 w-full max-w-md space-y-4" onClick={e => e.stopPropagation()}>
                        <div className="flex justify-between items-center">
                            <h3 className="text-white font-bold text-lg">Add Representative</h3>
                            <button onClick={() => setShowModal(false)} className="text-slate-500 hover:text-white"><X className="w-5 h-5" /></button>
                        </div>
                        <div className="space-y-3">
                            <input placeholder="Contact Person *" value={form.contact_person} onChange={e => setForm(p => ({ ...p, contact_person: e.target.value }))} className="w-full bg-[#050A15] border border-[#1E293B] rounded-lg px-4 py-2.5 text-white placeholder-slate-600 text-sm focus:border-[#D4AF37] outline-none" />
                            <input placeholder="Email" value={form.email} onChange={e => setForm(p => ({ ...p, email: e.target.value }))} className="w-full bg-[#050A15] border border-[#1E293B] rounded-lg px-4 py-2.5 text-white placeholder-slate-600 text-sm focus:border-[#D4AF37] outline-none" />
                            <input placeholder="Phone" value={form.phone} onChange={e => setForm(p => ({ ...p, phone: e.target.value }))} className="w-full bg-[#050A15] border border-[#1E293B] rounded-lg px-4 py-2.5 text-white placeholder-slate-600 text-sm focus:border-[#D4AF37] outline-none" />
                            <div className="grid grid-cols-2 gap-3">
                                <input placeholder="Country" value={form.country} onChange={e => setForm(p => ({ ...p, country: e.target.value }))} className="w-full bg-[#050A15] border border-[#1E293B] rounded-lg px-4 py-2.5 text-white placeholder-slate-600 text-sm focus:border-[#D4AF37] outline-none" />
                                <input placeholder="City" value={form.city} onChange={e => setForm(p => ({ ...p, city: e.target.value }))} className="w-full bg-[#050A15] border border-[#1E293B] rounded-lg px-4 py-2.5 text-white placeholder-slate-600 text-sm focus:border-[#D4AF37] outline-none" />
                            </div>
                            <input placeholder="Address" value={form.address} onChange={e => setForm(p => ({ ...p, address: e.target.value }))} className="w-full bg-[#050A15] border border-[#1E293B] rounded-lg px-4 py-2.5 text-white placeholder-slate-600 text-sm focus:border-[#D4AF37] outline-none" />
                            <select value={form.rep_type} onChange={e => setForm(p => ({ ...p, rep_type: e.target.value }))} className="w-full bg-[#050A15] border border-[#1E293B] rounded-lg px-4 py-2.5 text-white text-sm focus:border-[#D4AF37] outline-none">
                                <option value="personal">Personal Rep</option>
                                <option value="office">Office / Branch</option>
                            </select>
                            {form.rep_type === "office" && (
                                <input placeholder="Office / Branch Name" value={form.office_name} onChange={e => setForm(p => ({ ...p, office_name: e.target.value }))} className="w-full bg-[#050A15] border border-[#1E293B] rounded-lg px-4 py-2.5 text-white placeholder-slate-600 text-sm focus:border-[#D4AF37] outline-none" />
                            )}
                        </div>
                        <Button onClick={handleCreate} disabled={saving || !form.contact_person.trim()} className="w-full bg-[#D4AF37] text-[#050A15] hover:bg-[#F3E5AB] font-bold disabled:opacity-40">
                            {saving ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Plus className="w-4 h-4 mr-2" />}
                            {saving ? "Creating..." : "Create Representative"}
                        </Button>
                    </div>
                </div>
            )}
        </div>
    );
}
