"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
    UserCheck, Plus, Search, Loader2, RefreshCw,
    Mail, Phone, MapPin, Star,
} from "lucide-react";
import expoApi from "@/lib/expoApi";

interface Representative {
    id: number;
    full_name: string;
    role?: string;
    email?: string;
    phone?: string;
    country?: string;
    booth_location?: string;
    leads_captured?: number;
}

export default function RepresentativesPage() {
    const [reps, setReps] = useState<Representative[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchReps = useCallback(async () => {
        try {
            const res = await expoApi.get("/api/representatives");
            setReps(res.data?.representatives || res.data || []);
        } catch { /* ignore */ }
        finally { setLoading(false); }
    }, []);

    useEffect(() => { fetchReps(); }, [fetchReps]);

    return (
        <div className="min-h-screen bg-[#050A15] text-slate-300 p-4 md:p-8 space-y-6">
            <div className="flex justify-between items-center border-b border-[#1E293B] pb-6">
                <div>
                    <h1 className="text-2xl font-bold text-white uppercase flex items-center gap-3">
                        <UserCheck className="h-5 w-5 text-[#D4AF37]" /> Representatives
                    </h1>
                    <p className="text-sm text-slate-500 mt-1">Manage booth reps & track performance</p>
                </div>
                <Button onClick={() => alert('Opening Add Rep form...')} className="bg-[#D4AF37] text-[#050A15] hover:bg-[#F3E5AB] font-bold">
                    <Plus className="w-4 h-4 mr-2" /> Add Rep
                </Button>
            </div>

            {loading ? (
                <div className="flex justify-center py-20"><Loader2 className="h-8 w-8 animate-spin text-[#D4AF37]" /></div>
            ) : reps.length === 0 ? (
                <Card className="bg-[#0F172A] border-[#1E293B]">
                    <CardContent className="py-16 text-center">
                        <UserCheck className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                        <h3 className="text-white font-bold text-lg mb-2">No representatives yet</h3>
                        <p className="text-slate-500 text-sm">Add booth reps to track lead capture</p>
                    </CardContent>
                </Card>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                    {reps.map((r) => (
                        <Card key={r.id} className="bg-[#0F172A] border-[#1E293B] hover:border-[#D4AF37]/30">
                            <CardContent className="p-5">
                                <div className="flex items-center gap-3 mb-3">
                                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#D4AF37] to-[#B8860B] flex items-center justify-center text-black font-bold">
                                        {r.full_name?.[0] || "?"}
                                    </div>
                                    <div>
                                        <h4 className="text-white font-bold">{r.full_name}</h4>
                                        {r.role && <p className="text-xs text-[#D4AF37]">{r.role}</p>}
                                    </div>
                                </div>
                                <div className="space-y-1.5 text-xs text-slate-500">
                                    {r.email && <p className="flex items-center gap-2"><Mail className="w-3 h-3" />{r.email}</p>}
                                    {r.phone && <p className="flex items-center gap-2"><Phone className="w-3 h-3" />{r.phone}</p>}
                                    {r.country && <p className="flex items-center gap-2"><MapPin className="w-3 h-3" />{r.country}</p>}
                                </div>
                                {r.leads_captured != null && (
                                    <div className="mt-3 pt-3 border-t border-[#1E293B] flex justify-between items-center">
                                        <span className="text-xs text-slate-500">Leads</span>
                                        <Badge className="bg-emerald-500/10 text-emerald-400 border-none">{r.leads_captured}</Badge>
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    ))}
                </div>
            )}
        </div>
    );
}
