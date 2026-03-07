"use client";

import { useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
    Target, Users, Package, Globe, QrCode, BookOpen, Send,
    BarChart3, TrendingUp, Loader2, Search, UserCheck,
} from "lucide-react";
import Link from "next/link";
import api from "@/lib/api";
// expoApi removed — now served by main backend

export default function AcquisitionOverview() {
    const [loading, setLoading] = useState(true);
    const [stats, setStats] = useState<any>({});
    const [expoStats, setExpoStats] = useState<any>({});

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [mainRes, expoRes] = await Promise.allSettled([
                    api.get("/dashboard/main"),
                    api.get("/analytics/stats").catch(() => ({ data: null })),
                ]);
                if (mainRes.status === "fulfilled") setStats(mainRes.value.data?.kpi_summary || {});
                if (expoRes.status === "fulfilled" && expoRes.value.data) setExpoStats(expoRes.value.data);
            } catch (e) {
                console.error("Acquisition overview fetch failed:", e);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    const kpis = [
        { label: "Total Leads", value: stats.active_leads ?? 0, icon: Users, color: "blue" },
        { label: "Buyer Leads", value: stats.buyer_leads ?? 0, icon: Search, color: "emerald" },
        { label: "Supplier Leads", value: stats.supplier_leads ?? 0, icon: Package, color: "purple" },
        { label: "Expo Leads", value: expoStats.total_leads ?? 0, icon: Globe, color: "amber" },
        { label: "Qualified", value: stats.qualified_leads ?? 0, icon: UserCheck, color: "green" },
        { label: "Broadcasts", value: stats.broadcasts_sent ?? 0, icon: Send, color: "cyan" },
        { label: "QR Scans", value: expoStats.qr_scans ?? 0, icon: QrCode, color: "orange" },
        { label: "Catalog Opens", value: expoStats.catalog_opens ?? 0, icon: BookOpen, color: "pink" },
    ];

    const sections = [
        { label: "Buyer Leads", href: "/acquisition/buyer-leads", icon: Search, desc: "AI-powered buyer lead generation" },
        { label: "Supplier Leads", href: "/acquisition/supplier-leads", icon: Package, desc: "RFQ matching & supplier discovery" },
        { label: "Expo", href: "/acquisition/expo", icon: Globe, desc: "Exhibition leads & visitor management" },
        { label: "QR Capture", href: "/acquisition/qr-capture", icon: QrCode, desc: "QR code generation & scan tracking" },
        { label: "Catalogs", href: "/acquisition/catalogs", icon: BookOpen, desc: "Product catalog management" },
        { label: "Broadcasts", href: "/acquisition/broadcasts", icon: Send, desc: "Mass messaging campaigns" },
        { label: "Representatives", href: "/acquisition/representatives", icon: UserCheck, desc: "Booth representative management" },
        { label: "Lead Analytics", href: "/acquisition/lead-analytics", icon: BarChart3, desc: "Analytics & performance insights" },
    ];

    return (
        <div className="min-h-screen bg-[#050A15] text-slate-300 p-4 md:p-8 space-y-8">
            {/* Header */}
            <div className="border-b border-[#1E293B] pb-6">
                <div className="flex items-center gap-3 mb-2">
                    <div className="p-2 bg-[#D4AF37]/10 rounded-md border border-[#D4AF37]/30">
                        <Target className="h-6 w-6 text-[#D4AF37]" />
                    </div>
                    <h1 className="text-3xl font-bold tracking-tight text-white uppercase">Acquisition</h1>
                </div>
                <p className="text-[#94A3B8] text-sm">
                    Unified lead generation — Buyers, Suppliers, Expo & Campaigns
                </p>
            </div>

            {loading ? (
                <div className="flex items-center justify-center py-20">
                    <Loader2 className="h-8 w-8 animate-spin text-[#D4AF37]" />
                </div>
            ) : (
                <>
                    {/* KPI Grid */}
                    <div className="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-8 gap-4">
                        {kpis.map((k) => (
                            <KpiCard key={k.label} {...k} />
                        ))}
                    </div>

                    {/* Quick Access Grid */}
                    <div>
                        <h2 className="text-lg font-bold text-white uppercase tracking-widest mb-4">Modules</h2>
                        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
                            {sections.map((s) => (
                                <Link key={s.href} href={s.href}>
                                    <Card className="bg-[#0F172A] border-[#1E293B] hover:border-[#D4AF37]/40 transition-all cursor-pointer group h-full">
                                        <CardContent className="p-5 flex items-start gap-4">
                                            <div className="p-2.5 bg-[#D4AF37]/10 rounded-lg">
                                                <s.icon className="w-5 h-5 text-[#D4AF37]" />
                                            </div>
                                            <div>
                                                <h3 className="text-white font-bold group-hover:text-[#D4AF37] transition-colors">{s.label}</h3>
                                                <p className="text-xs text-slate-500 mt-1">{s.desc}</p>
                                            </div>
                                        </CardContent>
                                    </Card>
                                </Link>
                            ))}
                        </div>
                    </div>
                </>
            )}
        </div>
    );
}

function KpiCard({ label, value, icon: Icon, color }: { label: string; value: number; icon: any; color: string }) {
    const cm: Record<string, string> = {
        blue: "border-blue-500/20 text-blue-400", emerald: "border-emerald-500/20 text-emerald-400",
        purple: "border-purple-500/20 text-purple-400", amber: "border-amber-500/20 text-amber-400",
        green: "border-emerald-500/20 text-emerald-400", cyan: "border-cyan-500/20 text-cyan-400",
        orange: "border-orange-500/20 text-orange-400", pink: "border-pink-500/20 text-pink-400",
    };
    return (
        <Card className={`bg-[#0F172A] border ${cm[color] || cm.blue}`}>
            <CardContent className="p-4">
                <Icon className="w-4 h-4 opacity-60 mb-1" />
                <div className="text-2xl font-bold text-white">{value}</div>
                <p className="text-[10px] uppercase tracking-widest opacity-60">{label}</p>
            </CardContent>
        </Card>
    );
}
