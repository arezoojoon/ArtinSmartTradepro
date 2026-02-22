"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getActiveTenantId, getMyTenants, type Tenant } from "@/lib/tenant";
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    LineChart, Line, AreaChart, Area, Cell
} from 'recharts';
import {
    TrendingUp, ShieldAlert, Activity, Users, DollarSign, Package,
    ArrowUpRight, ArrowDownRight, RefreshCw, AlertTriangle
} from "lucide-react";
import { Badge } from "@/components/ui/badge";

const COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6'];

export default function DashboardPage() {
    const router = useRouter();
    const [tenant, setTenant] = useState<Tenant | null>(null);
    const [data, setData] = useState<any>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const activeId = getActiveTenantId();
        if (!activeId) {
            router.push("/select-tenant");
            return;
        }

        getMyTenants().then(list => {
            const found = list.find(t => t.id === activeId);
            if (found) setTenant(found);
        });

        const fetchWebDashboard = async () => {
            try {
                const { api } = await import("@/lib/api");
                const res = await api.get("/dashboard/web");
                setData(res.data);
            } catch (error) {
                console.error("Dashboard error:", error);
            } finally {
                setIsLoading(false);
            }
        };

        fetchWebDashboard();
    }, [router]);

    if (isLoading) {
        return (
            <div className="p-8 flex items-center justify-center min-h-[60vh]">
                <div className="flex flex-col items-center gap-4 text-slate-400">
                    <RefreshCw className="h-8 w-8 animate-spin" />
                    <span>Aggregating Platform Data...</span>
                </div>
            </div>
        );
    }

    if (!data) return null;

    return (
        <div className="p-4 md:p-8 space-y-8 max-w-7xl mx-auto">
            {/* Header */}
            <div className="flex justify-between items-end">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Main Hub</h1>
                    <p className="text-slate-500 mt-1">
                        Workspace: <span className="font-semibold text-slate-700">{tenant?.name || "..."}</span>
                    </p>
                </div>
                <div className="flex items-center gap-2">
                    <Badge variant="outline" className="bg-emerald-50 text-emerald-700 border-emerald-200 py-1">
                        <span className="flex h-2 w-2 rounded-full bg-emerald-500 mr-2 animate-pulse"></span>
                        Live Sync
                    </Badge>
                </div>
            </div>

            {/* Top Summaries (Pipeline & Cash Flow Overview) */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

                {/* 1. Pipeline Summary Chart */}
                <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 overflow-hidden">
                    <div className="flex justify-between items-center mb-6">
                        <div className="flex items-center gap-2">
                            <Activity className="h-5 w-5 text-indigo-500" />
                            <h2 className="text-lg font-semibold text-slate-800">Pipeline Value</h2>
                        </div>
                        <span className="text-xs font-medium text-slate-400 uppercase">Active Deals</span>
                    </div>
                    <div className="h-64 w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={data.pipeline} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                                <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#64748b' }} axisLine={false} tickLine={false} />
                                <YAxis tick={{ fontSize: 12, fill: '#64748b' }} axisLine={false} tickLine={false} tickFormatter={(val) => `$${val / 1000}k`} />
                                <Tooltip
                                    cursor={{ fill: '#f8fafc' }}
                                    contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                                    formatter={(value: any) => [`$${value.toLocaleString()}`, "Value"]}
                                />
                                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                                    {data.pipeline.map((entry: any, index: number) => (
                                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* 2. Cash Flow & DSO Trends */}
                <div className="bg-slate-900 rounded-xl border border-slate-800 shadow-lg p-6 overflow-hidden relative">
                    <div className="flex justify-between items-center mb-6 relative z-10">
                        <div className="flex items-center gap-2">
                            <DollarSign className="h-5 w-5 text-emerald-400" />
                            <h2 className="text-lg font-semibold text-white">Cash Flow Trends</h2>
                        </div>
                        <span className="text-xs font-medium text-slate-400 uppercase">6 Months</span>
                    </div>
                    <div className="h-64 w-full relative z-10">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={data.cash_flow} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                                <defs>
                                    <linearGradient id="colorCashIn" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#34d399" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#34d399" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#1e293b" />
                                <XAxis dataKey="period" tick={{ fontSize: 12, fill: '#64748b' }} axisLine={false} tickLine={false} />
                                <YAxis tick={{ fontSize: 12, fill: '#64748b' }} axisLine={false} tickLine={false} tickFormatter={(val) => `$${val / 1000}k`} />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '8px', color: '#f8fafc' }}
                                    itemStyle={{ color: '#f8fafc' }}
                                />
                                <Area type="monotone" dataKey="cash_in" stroke="#34d399" strokeWidth={3} fillOpacity={1} fill="url(#colorCashIn)" name="Cash In" />
                                <Line type="monotone" dataKey="cash_out" stroke="#f43f5e" strokeWidth={2} dot={false} name="Cash Out" />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                    <div className="absolute top-0 right-0 -mr-16 -mt-16 h-64 w-64 rounded-full bg-blue-500/10 blur-3xl"></div>
                </div>

            </div>

            {/* Bottom Grid (Margins, Risk, Performance) */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                {/* 3. Margin Overview Matrix */}
                <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 flex flex-col">
                    <div className="flex items-center gap-2 mb-4">
                        <TrendingUp className="h-5 w-5 text-blue-500" />
                        <h2 className="text-md font-semibold text-slate-800">Arbitrage Margins</h2>
                    </div>
                    {data.margin_matrix.length === 0 ? (
                        <div className="flex-1 flex items-center justify-center text-sm text-slate-500">No arbitrage detected.</div>
                    ) : (
                        <div className="space-y-3">
                            {data.margin_matrix.map((row: any, i: number) => (
                                <div key={i} className="flex justify-between items-center p-3 rounded-lg border border-slate-100 bg-slate-50/50 hover:bg-slate-50 transition-colors">
                                    <div>
                                        <div className="font-semibold text-sm text-slate-800">{row.product}</div>
                                        <div className="text-xs text-slate-500 mt-0.5">{row.origin} → {row.destination}</div>
                                    </div>
                                    <div className="text-right">
                                        <div className="font-bold text-emerald-600 text-sm">${row.net_margin.toLocaleString()}</div>
                                        <div className="text-[10px] text-slate-400 font-medium uppercase tracking-wider">{row.roi.toFixed(1)}% ROI</div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* 4. Risk Heatmap List */}
                <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 flex flex-col">
                    <div className="flex items-center gap-2 mb-4">
                        <ShieldAlert className="h-5 w-5 text-rose-500" />
                        <h2 className="text-md font-semibold text-slate-800">Global Risk Heatmap</h2>
                    </div>
                    {data.risk_heatmap.length === 0 ? (
                        <div className="flex-1 flex items-center justify-center text-sm text-slate-500">No critical risks detected.</div>
                    ) : (
                        <div className="space-y-3">
                            {data.risk_heatmap.map((r: any, i: number) => (
                                <div key={i} className="flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <div className={`h-2 w-2 rounded-full ${r.score >= 80 ? 'bg-rose-500' : r.score >= 50 ? 'bg-amber-500' : 'bg-blue-500'}`}></div>
                                        <div>
                                            <div className="text-sm font-medium text-slate-700">{r.country}</div>
                                            <div className="text-xs text-slate-400">{r.category} Risk</div>
                                        </div>
                                    </div>
                                    <Badge variant="outline" className={`${r.score >= 80 ? 'border-rose-200 text-rose-700 bg-rose-50' : r.score >= 50 ? 'border-amber-200 text-amber-700 bg-amber-50' : 'border-slate-200 text-slate-700'}`}>
                                        {r.score}/100
                                    </Badge>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* 5. Performance Snapshots */}
                <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 flex flex-col">
                    <div className="flex items-center gap-2 mb-4">
                        <Users className="h-5 w-5 text-purple-500" />
                        <h2 className="text-md font-semibold text-slate-800">Top Counterparties</h2>
                    </div>
                    {data.performance.length === 0 ? (
                        <div className="flex-1 flex items-center justify-center text-sm text-slate-500">No counterparty data.</div>
                    ) : (
                        <div className="space-y-4">
                            {data.performance.map((p: any, i: number) => (
                                <div key={p.id}>
                                    <div className="flex justify-between items-center mb-1.5">
                                        <div className="text-sm font-semibold text-slate-800 truncate pr-2">{p.name}</div>
                                        <div className="text-xs font-medium text-slate-500 capitalize">{p.type}</div>
                                    </div>
                                    <div className="flex items-center gap-3">
                                        <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                                            <div
                                                className={`h-full rounded-full ${p.score >= 80 ? 'bg-emerald-500' : p.score >= 50 ? 'bg-amber-500' : 'bg-rose-500'}`}
                                                style={{ width: `${Math.max(10, p.score)}%` }}
                                            ></div>
                                        </div>
                                        <span className="text-xs font-bold text-slate-700 w-8 text-right">{Math.round(p.score)}</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

            </div>
        </div>
    );
}
