"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
    Activity, AlertTriangle, BrainCircuit, Bell,
    Globe, Landmark, Radar, Scale, Send, ShoppingCart,
    Target, TrendingUp, ArrowRight, Zap, Loader2,
    Ship, ShieldCheck, Check, CheckCircle2, Clock,
    Eye, MessageSquare, Package, RefreshCw, X,
    Sparkles, Camera, Mic, FileText, CircleDot,
    Users, Handshake, Brain, Crosshair, Search,
} from "lucide-react";
import Link from "next/link";
import api from "@/lib/api";

function formatCurrency(val: number): string {
    if (val >= 1_000_000) return `$${(val / 1_000_000).toFixed(1)}M`;
    if (val >= 1_000) return `$${(val / 1_000).toFixed(0)}K`;
    return `$${val.toFixed(0)}`;
}

interface Alert {
    id: string;
    type: string;
    severity: string;
    title_fa: string;
    title_en: string;
    description_en: string;
    ai_confidence?: number;
    action_label_en?: string;
}

export default function CommandCenterPage() {
    const [dashData, setDashData] = useState<any>(null);
    const [alerts, setAlerts] = useState<Alert[]>([]);
    const [kpi, setKpi] = useState<any>(null);
    const [approvals, setApprovals] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchData = useCallback(async () => {
        try {
            const [dashRes, alertsRes, kpiRes, approvalsRes] = await Promise.allSettled([
                api.get("/dashboard/main"),
                api.get("/control-tower/alerts"),
                api.get("/control-tower/kpi"),
                api.get("/control-tower/approvals?status=pending"),
            ]);
            if (dashRes.status === "fulfilled") setDashData(dashRes.value.data);
            if (alertsRes.status === "fulfilled") setAlerts(alertsRes.value.data || []);
            if (kpiRes.status === "fulfilled") setKpi(kpiRes.value.data);
            if (approvalsRes.status === "fulfilled") setApprovals(approvalsRes.value.data || []);
        } catch (e) {
            console.error("Command Center fetch failed:", e);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 30000);
        return () => clearInterval(interval);
    }, [fetchData]);

    const kpiSummary = dashData?.kpi_summary || {};
    const pipelineValue = kpiSummary.total_pipeline_value || 0;
    const riskCount = kpiSummary.high_risk_countries || 0;
    const margins = dashData?.margin_overview || [];
    const riskItems = dashData?.risk_heatmap || [];

    return (
        <div className="min-h-screen bg-[#050A15] text-slate-300 p-4 md:p-8 pt-6 selection:bg-[#D4AF37] selection:text-black space-y-8">

            {/* ── Header ── */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-6 border-b border-[#1E293B] pb-6">
                <div>
                    <div className="flex items-center gap-3 mb-2">
                        <div className="p-2 bg-[#D4AF37]/10 rounded-md border border-[#D4AF37]/30 shadow-[0_0_15px_rgba(212,175,55,0.15)]">
                            <Zap className="h-6 w-6 text-[#D4AF37]" />
                        </div>
                        <h1 className="text-3xl font-bold tracking-tight text-white uppercase">Command Center</h1>
                    </div>
                    <p className="text-[#94A3B8] text-sm flex items-center gap-2">
                        <Activity className="w-4 h-4 text-emerald-400" />
                        {loading ? "Loading live data..." : "Live operational overview — CRM, Acquisition & Logistics merged."}
                    </p>
                </div>

                <div className="flex items-center gap-3 flex-wrap">
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => { setLoading(true); fetchData(); }}
                        className="border-slate-700 text-slate-400 hover:text-white hover:border-[#D4AF37]/50"
                    >
                        <RefreshCw className="w-4 h-4 mr-2" /> Refresh
                    </Button>
                </div>
            </div>

            {loading ? (
                <div className="flex items-center justify-center py-20">
                    <Loader2 className="h-8 w-8 animate-spin text-[#D4AF37]" />
                    <span className="ml-3 text-slate-400">Loading command center...</span>
                </div>
            ) : (
                <>
                    {/* ── Row 1: KPI Strip ── */}
                    <div className="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-8 gap-4">
                        <KpiMiniCard label="Active Deals" value={kpi?.active_deals ?? kpiSummary.active_deals ?? 0} icon={Handshake} color="emerald" />
                        <KpiMiniCard label="New Leads" value={kpiSummary.active_leads ?? 0} icon={Users} color="blue" />
                        <KpiMiniCard label="Open Approvals" value={kpi?.pending_approvals ?? 0} icon={ShieldCheck} color={kpi?.pending_approvals > 0 ? "amber" : "green"} />
                        <KpiMiniCard label="Shipment Risks" value={riskCount} icon={AlertTriangle} color={riskCount > 0 ? "red" : "green"} />
                        <KpiMiniCard label="Pipeline" value={formatCurrency(pipelineValue)} icon={TrendingUp} color="gold" />
                        <KpiMiniCard label="Contacts" value={kpi?.total_contacts ?? 0} icon={Users} color="purple" />
                        <KpiMiniCard label="Margin Opps" value={margins.length} icon={Scale} color="gold" />
                        <KpiMiniCard label="Conversion %" value={kpiSummary.conversion_rate ? `${kpiSummary.conversion_rate}%` : "—"} icon={Target} color="emerald" />
                    </div>

                    {/* ── Row 2: Panels ── */}
                    <div className="grid lg:grid-cols-12 gap-6">

                        {/* Left 8 cols: Alerts + Approvals + Intelligence */}
                        <div className="lg:col-span-8 space-y-6">

                            {/* Alerts & Exceptions */}
                            <div>
                                <h3 className="text-lg font-bold text-white uppercase tracking-widest flex items-center gap-2 mb-3">
                                    <Bell className="h-5 w-5 text-[#D4AF37]" /> Live Alerts
                                    <Badge className="bg-[#D4AF37]/10 text-[#D4AF37] border-none font-mono text-[10px] uppercase ml-auto">{alerts.length}</Badge>
                                </h3>
                                {alerts.length === 0 ? (
                                    <Card className="bg-[#0F172A] border-[#1E293B]">
                                        <CardContent className="py-8 text-center">
                                            <CheckCircle2 className="w-10 h-10 text-emerald-500 mx-auto mb-3" />
                                            <p className="text-slate-400 text-sm">All clear. No active alerts.</p>
                                        </CardContent>
                                    </Card>
                                ) : (
                                    <div className="space-y-2">
                                        {alerts.slice(0, 5).map((alert) => (
                                            <AlertRow key={alert.id} alert={alert} />
                                        ))}
                                    </div>
                                )}
                            </div>

                            {approvals.length > 0 && (
                                <div>
                                    <h3 className="text-lg font-bold text-white uppercase tracking-widest flex items-center gap-2 mb-3">
                                        <ShieldCheck className="h-5 w-5 text-amber-400" /> Pending Approvals
                                        <Badge className="bg-amber-500/10 text-amber-400 border-none font-mono text-[10px] uppercase ml-auto">{approvals.length}</Badge>
                                    </h3>
                                    <div className="space-y-2">
                                        {approvals.slice(0, 4).map((item: any) => (
                                            <Card key={item.id} className="bg-slate-900/50 border border-slate-700/50 hover:border-[#D4AF37]/20 transition-colors">
                                                <CardContent className="p-4 flex items-center justify-between gap-3">
                                                    <div className="flex items-center gap-3 min-w-0">
                                                        <div className="w-8 h-8 rounded-lg bg-[#D4AF37]/10 flex items-center justify-center shrink-0">
                                                            <FileText className="w-4 h-4 text-[#D4AF37]" />
                                                        </div>
                                                        <div className="min-w-0">
                                                            <p className="text-sm font-medium text-white truncate">{item.title}</p>
                                                            {item.ai_reasoning && <p className="text-xs text-slate-500 truncate">{item.ai_reasoning}</p>}
                                                        </div>
                                                    </div>
                                                    <div className="flex gap-2 shrink-0">
                                                        <Button
                                                            size="sm"
                                                            onClick={() => setApprovals(prev => prev.filter(a => a.id !== item.id))}
                                                            className="bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/30 text-xs h-8"
                                                        >
                                                            <Check className="w-3 h-3 mr-1" /> Approve
                                                        </Button>
                                                        <Button
                                                            size="sm"
                                                            variant="outline"
                                                            onClick={() => setApprovals(prev => prev.filter(a => a.id !== item.id))}
                                                            className="border-red-500/30 text-red-400 hover:bg-red-500/10 text-xs h-8"
                                                        >
                                                            <X className="w-3 h-3" />
                                                        </Button>
                                                    </div>
                                                </CardContent>
                                            </Card>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Intelligence Feed — Margin Opportunities */}
                            {margins.length > 0 && (
                                <div>
                                    <h3 className="text-lg font-bold text-white uppercase tracking-widest flex items-center gap-2 mb-3">
                                        <BrainCircuit className="h-5 w-5 text-[#D4AF37]" /> Intelligence Feed
                                    </h3>
                                    <div className="space-y-2">
                                        {margins.slice(0, 3).map((m: any, i: number) => (
                                            <Card key={i} className="bg-[#0F172A] border-[#1E293B] border-l-4 border-l-[#D4AF37]">
                                                <CardContent className="p-4 flex flex-col md:flex-row gap-3 justify-between items-start md:items-center">
                                                    <div className="flex gap-3">
                                                        <div className="p-2 bg-[#D4AF37]/10 rounded-lg h-fit"><Scale className="w-5 h-5 text-[#D4AF37]" /></div>
                                                        <div>
                                                            <h4 className="text-white font-bold">{m.product_key}: {m.buy_market} → {m.sell_market}</h4>
                                                            <p className="text-sm text-slate-400">
                                                                Margin: <strong className="text-[#D4AF37]">{m.estimated_margin_pct?.toFixed(1)}%</strong> · {m.status}
                                                            </p>
                                                        </div>
                                                    </div>
                                                    <Link href="/brain">
                                                        <Button className="bg-[#D4AF37]/10 text-[#D4AF37] border border-[#D4AF37]/30 hover:bg-[#D4AF37] hover:text-[#050A15] font-bold text-xs uppercase h-9">
                                                            Analyze <ArrowRight className="w-3 h-3 ml-1" />
                                                        </Button>
                                                    </Link>
                                                </CardContent>
                                            </Card>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Risk Alerts */}
                            {riskItems.filter((r: any) => r.risk_level === "high").length > 0 && (
                                <div className="space-y-2">
                                    {riskItems.filter((r: any) => r.risk_level === "high").slice(0, 2).map((risk: any, i: number) => (
                                        <Card key={`risk-${i}`} className="bg-[#0F172A] border-[#1E293B] border-l-4 border-l-red-500">
                                            <CardContent className="p-4 flex gap-3 items-center">
                                                <div className="p-2 bg-red-500/10 rounded-lg"><AlertTriangle className="w-5 h-5 text-red-500" /></div>
                                                <div>
                                                    <h4 className="text-white font-bold">{risk.country} — {risk.risk_level?.toUpperCase()}</h4>
                                                    <p className="text-sm text-slate-400">{risk.description} (Score: {risk.risk_score})</p>
                                                </div>
                                            </CardContent>
                                        </Card>
                                    ))}
                                </div>
                            )}
                        </div>

                        {/* Right 4 cols: Quick Actions */}
                        <div className="lg:col-span-4">
                            <Card className="bg-[#0F172A] border-[#1E293B] shadow-2xl relative overflow-hidden h-full">
                                <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-[#D4AF37] to-transparent opacity-50" />
                                <CardHeader className="pb-4 border-b border-[#1E293B]">
                                    <CardTitle className="text-md font-medium text-white flex items-center gap-2">
                                        <Zap className="h-4 w-4 text-[#D4AF37]" /> Quick Actions
                                    </CardTitle>
                                </CardHeader>
                                <CardContent className="pt-6 space-y-3">
                                    <QuickActionCard href="/deals" icon={Handshake} color="emerald" label="New Deal" desc="Create a new deal in the pipeline" />
                                    <QuickActionCard href="/acquisition/buyer-leads" icon={Search} color="blue" label="Launch Buyer Hunt" desc="AI-powered buyer lead generation" />
                                    <QuickActionCard href="/acquisition/supplier-leads" icon={Package} color="purple" label="Launch Supplier Hunt" desc="Find and qualify new suppliers" />
                                    <QuickActionCard href="/acquisition/expo" icon={Globe} color="amber" label="Open Expo" desc="Manage exhibition leads & visitors" />
                                    <QuickActionCard href="/scanner" icon={Camera} color="cyan" label="Scan Document" desc="Smart document scanning & classification" />
                                    <QuickActionCard href="/acquisition/broadcasts" icon={Send} color="green" label="Start Broadcast" desc="Send campaign to leads via messaging" />
                                </CardContent>
                            </Card>
                        </div>
                    </div>
                </>
            )}
        </div>
    );
}

// ─── Sub-components ──────────────────────────────────────────────────────────

function KpiMiniCard({ label, value, icon: Icon, color }: { label: string; value: any; icon: any; color: string }) {
    const colorMap: Record<string, string> = {
        blue: "border-blue-500/20 text-blue-400",
        emerald: "border-emerald-500/20 text-emerald-400",
        green: "border-emerald-500/20 text-emerald-400",
        amber: "border-amber-500/20 text-amber-400",
        red: "border-red-500/20 text-red-400",
        purple: "border-purple-500/20 text-purple-400",
        gold: "border-[#D4AF37]/20 text-[#D4AF37]",
        cyan: "border-cyan-500/20 text-cyan-400",
    };
    return (
        <Card className={`bg-[#0F172A] border ${colorMap[color] || colorMap.blue} hover:border-[#D4AF37]/30 transition-colors`}>
            <CardContent className="p-4">
                <div className="flex items-center justify-between mb-1">
                    <Icon className="w-4 h-4 opacity-60" />
                </div>
                <div className="text-2xl font-bold text-white">{value}</div>
                <p className="text-[10px] uppercase tracking-widest opacity-60 mt-1">{label}</p>
            </CardContent>
        </Card>
    );
}

function AlertRow({ alert }: { alert: Alert }) {
    const severityColors: Record<string, string> = {
        critical: "border-l-red-500 bg-red-500/5",
        warning: "border-l-amber-500 bg-amber-500/5",
        opportunity: "border-l-emerald-500 bg-emerald-500/5",
        info: "border-l-blue-500 bg-blue-500/5",
    };
    return (
        <Card className={`bg-[#0F172A] border-[#1E293B] border-l-4 ${severityColors[alert.severity] || severityColors.info}`}>
            <CardContent className="p-3 flex items-center gap-3">
                <AlertTriangle className={`w-4 h-4 shrink-0 ${alert.severity === "critical" ? "text-red-500" : alert.severity === "warning" ? "text-amber-400" : "text-blue-400"}`} />
                <div className="min-w-0 flex-1">
                    <p className="text-sm text-white font-medium truncate">{alert.title_en}</p>
                    {alert.description_en && <p className="text-xs text-slate-500 truncate">{alert.description_en}</p>}
                </div>
                {alert.ai_confidence != null && alert.ai_confidence > 0 && (
                    <Badge className="bg-[#D4AF37]/10 text-[#D4AF37] border-none text-[10px] shrink-0">
                        AI {Math.round(alert.ai_confidence * 100)}%
                    </Badge>
                )}
            </CardContent>
        </Card>
    );
}

function QuickActionCard({ href, icon: Icon, color, label, desc }: { href: string; icon: any; color: string; label: string; desc: string }) {
    const bgMap: Record<string, string> = {
        emerald: "bg-emerald-500/10 text-emerald-400",
        blue: "bg-blue-500/10 text-blue-400",
        purple: "bg-purple-500/10 text-purple-400",
        amber: "bg-amber-500/10 text-amber-400",
        cyan: "bg-cyan-500/10 text-cyan-400",
        green: "bg-green-500/10 text-green-400",
    };
    return (
        <Link href={href} className="block">
            <div className="p-3.5 bg-[#050A15] border border-[#1E293B] rounded-lg cursor-pointer hover:border-[#D4AF37]/50 transition-colors group">
                <div className="flex items-center gap-3 mb-1">
                    <div className={`p-1.5 rounded ${bgMap[color] || bgMap.blue}`}>
                        <Icon className="w-4 h-4" />
                    </div>
                    <span className="font-bold text-sm text-white group-hover:text-[#D4AF37] transition-colors">{label}</span>
                </div>
                <p className="text-xs text-slate-500 pl-10">{desc}</p>
            </div>
        </Link>
    );
}
