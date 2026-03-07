"use client";

import { useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle, Loader2, MapPin, Shield, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import api from "@/lib/api";

interface RiskItem {
    country: string;
    risk_level: string;
    risk_type: string;
    risk_score: number;
    description: string;
}

export default function RiskEnginePage() {
    const [risks, setRisks] = useState<RiskItem[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchRisks = async () => {
        try {
            const res = await api.get("/dashboard/main");
            setRisks(res.data?.risk_heatmap || []);
        } catch { /* ignore */ }
        finally { setLoading(false); }
    };

    useEffect(() => { fetchRisks(); }, []);

    const high = risks.filter(r => r.risk_level === "high");
    const medium = risks.filter(r => r.risk_level === "medium");
    const low = risks.filter(r => r.risk_level === "low");

    return (
        <div className="min-h-screen bg-[#050A15] text-slate-300 p-4 md:p-8 space-y-6">
            <div className="flex justify-between items-center border-b border-[#1E293B] pb-6">
                <div>
                    <h1 className="text-2xl font-bold text-white uppercase flex items-center gap-3">
                        <AlertTriangle className="h-5 w-5 text-red-400" /> Risk Engine
                    </h1>
                    <p className="text-sm text-slate-500 mt-1">Country risk analysis & trade compliance</p>
                </div>
                <Button variant="outline" size="sm" onClick={() => { setLoading(true); fetchRisks(); }} className="border-slate-700 text-slate-400">
                    <RefreshCw className="w-4 h-4 mr-2" /> Refresh
                </Button>
            </div>

            {loading ? (
                <div className="flex justify-center py-20"><Loader2 className="h-8 w-8 animate-spin text-[#D4AF37]" /></div>
            ) : risks.length === 0 ? (
                <Card className="bg-[#0F172A] border-[#1E293B]">
                    <CardContent className="py-16 text-center">
                        <Shield className="w-12 h-12 text-emerald-500 mx-auto mb-4" />
                        <h3 className="text-white font-bold text-lg">All Clear</h3>
                        <p className="text-slate-500 text-sm">No risk alerts detected</p>
                    </CardContent>
                </Card>
            ) : (
                <div className="space-y-6">
                    {/* Summary */}
                    <div className="grid grid-cols-3 gap-4">
                        <Card className="bg-red-500/5 border-red-500/20">
                            <CardContent className="p-4 text-center">
                                <p className="text-3xl font-bold text-red-400">{high.length}</p>
                                <p className="text-xs uppercase text-red-400/60">High Risk</p>
                            </CardContent>
                        </Card>
                        <Card className="bg-amber-500/5 border-amber-500/20">
                            <CardContent className="p-4 text-center">
                                <p className="text-3xl font-bold text-amber-400">{medium.length}</p>
                                <p className="text-xs uppercase text-amber-400/60">Medium</p>
                            </CardContent>
                        </Card>
                        <Card className="bg-emerald-500/5 border-emerald-500/20">
                            <CardContent className="p-4 text-center">
                                <p className="text-3xl font-bold text-emerald-400">{low.length}</p>
                                <p className="text-xs uppercase text-emerald-400/60">Low Risk</p>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Risk Items */}
                    <div className="space-y-2">
                        {risks.map((r, i) => (
                            <Card key={i} className={`bg-[#0F172A] border-[#1E293B] border-l-4 ${r.risk_level === "high" ? "border-l-red-500" :
                                    r.risk_level === "medium" ? "border-l-amber-500" : "border-l-emerald-500"
                                }`}>
                                <CardContent className="p-4 flex items-center gap-4">
                                    <MapPin className={`w-5 h-5 shrink-0 ${r.risk_level === "high" ? "text-red-400" : r.risk_level === "medium" ? "text-amber-400" : "text-emerald-400"
                                        }`} />
                                    <div className="flex-1 min-w-0">
                                        <h4 className="text-white font-bold">{r.country}</h4>
                                        <p className="text-xs text-slate-500">{r.description}</p>
                                    </div>
                                    <Badge className={`border-none text-xs ${r.risk_level === "high" ? "bg-red-500/10 text-red-400" :
                                            r.risk_level === "medium" ? "bg-amber-500/10 text-amber-400" : "bg-emerald-500/10 text-emerald-400"
                                        }`}>
                                        {r.risk_type} · {r.risk_score}
                                    </Badge>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
