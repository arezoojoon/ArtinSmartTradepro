'use client';

import { useEffect, useState } from 'react';
import { listTenants, listDlq, listAuditLogs, listPlans } from '@/lib/sys-api';
import { Users, CreditCard, AlertTriangle, ClipboardList, TrendingUp, Activity } from 'lucide-react';

interface StatCard {
    label: string;
    value: string | number;
    sub?: string;
    icon: React.ElementType;
    accent: string;
}

function StatCard({ label, value, sub, icon: Icon, accent }: StatCard) {
    return (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
            <div className="flex items-start justify-between">
                <div>
                    <p className="text-xs text-slate-500 font-medium uppercase tracking-wide">{label}</p>
                    <p className={`text-3xl font-bold mt-1 ${accent}`}>{value}</p>
                    {sub && <p className="text-xs text-slate-500 mt-1">{sub}</p>}
                </div>
                <div className={`p-2 rounded-lg bg-slate-800`}>
                    <Icon className={`h-5 w-5 ${accent}`} />
                </div>
            </div>
        </div>
    );
}

export default function SysOverviewPage() {
    const [tenants, setTenants] = useState<{ total: number; active: number }>({ total: 0, active: 0 });
    const [dlqCount, setDlqCount] = useState(0);
    const [recentAudits, setRecentAudits] = useState<any[]>([]);
    const [planCount, setPlanCount] = useState(0);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        Promise.allSettled([
            listTenants('', 200, 0).then(r => setTenants({ total: r.total, active: r.items.filter((t: any) => t.is_active).length })),
            listDlq().then(r => setDlqCount(r.total)),
            listAuditLogs({ limit: 8 }).then(r => setRecentAudits(r.items)),
            listPlans().then(r => setPlanCount(r.length)),
        ]).finally(() => setLoading(false));
    }, []);

    if (loading) return (
        <div className="flex items-center justify-center h-64 text-slate-500">Loading…</div>
    );

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-xl font-bold text-slate-100">Ops Overview</h1>
                <p className="text-sm text-slate-500 mt-0.5">Platform health at a glance</p>
            </div>

            {/* Stats grid */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard label="Total Tenants" value={tenants.total} sub={`${tenants.active} active`} icon={Users} accent="text-sky-400" />
                <StatCard label="Active Plans" value={planCount} sub="Configured plans" icon={CreditCard} accent="text-emerald-400" />
                <StatCard label="DLQ Items" value={dlqCount} sub="Failed jobs" icon={AlertTriangle} accent={dlqCount > 0 ? 'text-red-400' : 'text-slate-400'} />
                <StatCard label="MRR" value={`$${(planCount * 299).toLocaleString()}`} sub="Monthly Recurring Revenue" icon={TrendingUp} accent="text-emerald-400" />
            </div>

            {/* DLQ alert */}
            {dlqCount > 0 && (
                <div className="flex items-center gap-3 px-4 py-3 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm">
                    <AlertTriangle className="h-4 w-4 flex-shrink-0" />
                    <span><strong>{dlqCount}</strong> items in the dead-letter queue. <a href="/sys/dlq" className="underline hover:text-red-300">Review DLQ →</a></span>
                </div>
            )}

            {/* Recent audit log */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl">
                <div className="px-5 py-4 border-b border-slate-800 flex items-center gap-2">
                    <ClipboardList className="h-4 w-4 text-slate-400" />
                    <h2 className="text-sm font-semibold text-slate-200">Recent Admin Actions</h2>
                </div>
                <div className="divide-y divide-slate-800">
                    {recentAudits.length === 0 && (
                        <p className="px-5 py-6 text-sm text-slate-600 text-center">No audit log entries yet</p>
                    )}
                    {recentAudits.map(log => (
                        <div key={log.id} className="px-5 py-3 flex items-center justify-between">
                            <div>
                                <span className="text-xs font-mono bg-slate-800 text-amber-400 px-1.5 py-0.5 rounded mr-2">
                                    {log.action}
                                </span>
                                <span className="text-xs text-slate-500">{log.resource_type} {log.resource_id?.slice(0, 8)}</span>
                            </div>
                            <span className="text-xs text-slate-600">
                                {log.created_at ? new Date(log.created_at).toLocaleString() : ''}
                            </span>
                        </div>
                    ))}
                </div>
                <div className="px-5 py-3 border-t border-slate-800">
                    <a href="/sys/audit" className="text-xs text-amber-400 hover:text-amber-300">View all audit logs →</a>
                </div>
            </div>
        </div>
    );
}
