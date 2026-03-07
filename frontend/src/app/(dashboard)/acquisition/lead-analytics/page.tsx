"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
    BarChart3, Users, Download, TrendingUp,
    Globe, Clock, Loader2, RefreshCw, Target,
} from "lucide-react";
import api from "@/lib/api";

export default function LeadAnalyticsPage() {
    const [stats, setStats] = useState<any>(null);
    const [boothMetrics, setBoothMetrics] = useState<any>({});
    const [loading, setLoading] = useState(true);

    const fetchData = useCallback(async () => {
        try {
            const [statsRes, metricsRes] = await Promise.allSettled([
                api.get("/analytics/stats"),
                api.get("/analytics/stats"), // booth-metrics merged into analytics
            ]);
            if (statsRes.status === "fulfilled") setStats(statsRes.value.data);
            if (metricsRes.status === "fulfilled") setBoothMetrics(metricsRes.value.data || {});
        } catch { /* ignore */ }
        finally { setLoading(false); }
    }, []);

    useEffect(() => { fetchData(); }, [fetchData]);

    const summaryCards = [
        { label: "Total Visitors", value: boothMetrics.total_visitors || stats?.total_leads || 0, icon: Users, color: "gold" },
        { label: "Catalog Downloads", value: boothMetrics.catalog_downloads || 0, icon: Download, color: "blue" },
        { label: "Negotiations", value: boothMetrics.negotiations || 0, icon: TrendingUp, color: "green" },
        { label: "Avg Lead Score", value: boothMetrics.avg_lead_score || 0, icon: Target, color: "purple" },
    ];

    return (
        <div className="min-h-screen bg-[#050A15] text-slate-300 p-4 md:p-8 space-y-6">
            <div className="flex justify-between items-center border-b border-[#1E293B] pb-6">
                <div>
                    <h1 className="text-2xl font-bold text-white uppercase flex items-center gap-3">
                        <BarChart3 className="h-5 w-5 text-[#D4AF37]" /> Lead Analytics
                    </h1>
                    <p className="text-sm text-slate-500 mt-1">AI-Powered acquisition performance insights</p>
                </div>
                <Button variant="outline" size="sm" onClick={() => { setLoading(true); fetchData(); }} className="border-slate-700 text-slate-400">
                    <RefreshCw className="w-4 h-4 mr-2" /> Refresh
                </Button>
            </div>

            {loading ? (
                <div className="flex justify-center py-20"><Loader2 className="h-8 w-8 animate-spin text-[#D4AF37]" /></div>
            ) : (
                <>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {summaryCards.map((s) => (
                            <Card key={s.label} className="bg-[#0F172A] border-[#1E293B]">
                                <CardContent className="p-5 flex items-center justify-between">
                                    <div>
                                        <p className="text-[10px] uppercase tracking-widest text-slate-500">{s.label}</p>
                                        <p className="text-3xl font-bold text-white mt-1">{s.value}</p>
                                    </div>
                                    <s.icon className="w-6 h-6 text-[#D4AF37] opacity-50" />
                                </CardContent>
                            </Card>
                        ))}
                    </div>

                    {/* Operational Metrics */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <Card className="bg-[#0F172A] border-[#1E293B]">
                            <CardContent className="p-6">
                                <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                                    <Globe className="w-5 h-5 text-emerald-400" /> Top Countries
                                </h3>
                                {(boothMetrics.reseller_countries || []).length > 0 ? (
                                    <div className="space-y-3">
                                        {boothMetrics.reseller_countries.slice(0, 5).map((c: any, i: number) => (
                                            <div key={i} className="flex items-center justify-between">
                                                <span className="text-sm text-slate-400">{c.country}</span>
                                                <span className="text-white font-bold">{c.count}</span>
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <p className="text-slate-600 text-sm">No country data yet</p>
                                )}
                            </CardContent>
                        </Card>

                        <Card className="bg-[#0F172A] border-[#1E293B]">
                            <CardContent className="p-6">
                                <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                                    <TrendingUp className="w-5 h-5 text-orange-400" /> Top Products
                                </h3>
                                {(boothMetrics.top_products || []).length > 0 ? (
                                    <div className="space-y-3">
                                        {boothMetrics.top_products.slice(0, 5).map((p: any, i: number) => (
                                            <div key={i} className="flex items-center justify-between">
                                                <span className="text-sm text-slate-400">{p.name}</span>
                                                <span className="text-white font-bold">{p.count} views</span>
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <p className="text-slate-600 text-sm">No product data yet</p>
                                )}
                            </CardContent>
                        </Card>
                    </div>

                    {/* Conversion Metrics */}
                    <Card className="bg-[#0F172A] border-[#1E293B]">
                        <CardContent className="p-6">
                            <h3 className="text-lg font-bold text-white mb-4">Conversion Funnel</h3>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                {[
                                    { label: "Download Rate", value: `${boothMetrics.catalog_download_rate || 0}%` },
                                    { label: "Negotiation Rate", value: `${boothMetrics.negotiation_rate || 0}%` },
                                    { label: "Franchise Requests", value: boothMetrics.franchise_requests || 0 },
                                    { label: "Avg Score", value: boothMetrics.avg_lead_score || 0 },
                                ].map((m) => (
                                    <div key={m.label} className="text-center p-4 bg-[#050A15] rounded-lg border border-[#1E293B]">
                                        <p className="text-2xl font-bold text-[#D4AF37]">{m.value}</p>
                                        <p className="text-[10px] uppercase tracking-widest text-slate-500 mt-1">{m.label}</p>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>
                </>
            )}
        </div>
    );
}
