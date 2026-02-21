'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
    getTenant, getTenantUsers, getTenantUsage,
    suspendTenant, restoreTenant, impersonateTenant,
    listPlans, setTenantSubscription,
} from '@/lib/sys-api';
import { ArrowLeft, UserX, UserCheck, LogIn, BarChart2 } from 'lucide-react';

export default function TenantDetailPage() {
    const { tenantId } = useParams<{ tenantId: string }>();
    const router = useRouter();
    const [tenant, setTenant] = useState<any>(null);
    const [users, setUsers] = useState<any[]>([]);
    const [usage, setUsage] = useState<any>(null);
    const [plans, setPlans] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [acting, setActing] = useState(false);
    const [selectedPlan, setSelectedPlan] = useState('');

    const load = async () => {
        setLoading(true);
        try {
            const [t, u, us, p] = await Promise.all([
                getTenant(tenantId), getTenantUsers(tenantId),
                getTenantUsage(tenantId), listPlans(),
            ]);
            setTenant(t); setUsers(u); setUsage(us); setPlans(p);
            setSelectedPlan(t?.subscription?.plan?.code || '');
        } finally { setLoading(false); }
    };

    useEffect(() => { load(); }, [tenantId]);

    const handleSuspend = async () => {
        if (!confirm('Suspend this tenant? This is audited.')) return;
        setActing(true);
        try { await suspendTenant(tenantId); await load(); } finally { setActing(false); }
    };

    const handleRestore = async () => {
        setActing(true);
        try { await restoreTenant(tenantId); await load(); } finally { setActing(false); }
    };

    const handleImpersonate = async () => {
        if (!confirm('This will create an audited 15-minute impersonation token. Continue?')) return;
        setActing(true);
        try {
            const r = await impersonateTenant(tenantId);
            alert(`Impersonation token (expires in ${r.expires_in_minutes}min):\n${r.impersonation_token}`);
        } finally { setActing(false); }
    };

    const handleSetPlan = async () => {
        if (!selectedPlan) return;
        setActing(true);
        try { await setTenantSubscription(tenantId, selectedPlan); await load(); } finally { setActing(false); }
    };

    if (loading) return <div className="flex items-center justify-center h-64 text-slate-500">Loading…</div>;
    if (!tenant) return <div className="text-red-400 p-6">Tenant not found</div>;

    return (
        <div className="space-y-5 max-w-4xl">
            <button onClick={() => router.back()} className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-300">
                <ArrowLeft className="h-3.5 w-3.5" /> Back
            </button>

            {/* Header */}
            <div className="flex items-start justify-between">
                <div>
                    <h1 className="text-xl font-bold text-slate-100">{tenant.name}</h1>
                    <p className="text-xs text-slate-600 font-mono mt-0.5">{tenantId}</p>
                </div>
                <div className="flex gap-2">
                    <button onClick={handleImpersonate} disabled={acting}
                        className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition">
                        <LogIn className="h-3.5 w-3.5" /> Impersonate
                    </button>
                    {tenant.is_active ? (
                        <button onClick={handleSuspend} disabled={acting}
                            className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-lg transition">
                            <UserX className="h-3.5 w-3.5" /> Suspend
                        </button>
                    ) : (
                        <button onClick={handleRestore} disabled={acting}
                            className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 rounded-lg transition">
                            <UserCheck className="h-3.5 w-3.5" /> Restore
                        </button>
                    )}
                </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
                {/* Subscription */}
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 col-span-2 lg:col-span-1">
                    <h2 className="text-xs font-semibold text-slate-400 uppercase mb-3">Subscription</h2>
                    <div className="space-y-3">
                        <div className="flex items-center gap-2">
                            <select value={selectedPlan} onChange={e => setSelectedPlan(e.target.value)}
                                className="flex-1 px-3 py-2 bg-slate-800 border border-slate-700 text-slate-200 rounded-lg text-sm focus:outline-none focus:border-amber-500">
                                <option value="">— No plan —</option>
                                {plans.map((p: any) => (
                                    <option key={p.code} value={p.code}>{p.name} (${p.monthly_price_usd}/mo)</option>
                                ))}
                            </select>
                            <button onClick={handleSetPlan} disabled={acting || !selectedPlan}
                                className="px-3 py-2 bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-slate-900 font-medium rounded-lg text-sm transition">
                                Set
                            </button>
                        </div>
                        <div className="text-xs text-slate-500">
                            Current status: <span className={tenant.subscription?.status === 'active' ? 'text-emerald-400' : 'text-red-400'}>
                                {tenant.subscription?.status || 'No subscription'}
                            </span>
                        </div>
                    </div>
                </div>

                {/* Stats */}
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                    <h2 className="text-xs font-semibold text-slate-400 uppercase mb-3">Overview</h2>
                    <div className="space-y-2 text-sm">
                        <div className="flex justify-between"><span className="text-slate-500">Users</span><span className="text-slate-200">{tenant.user_count}</span></div>
                        <div className="flex justify-between"><span className="text-slate-500">WhiteLabel</span>
                            <span className={tenant.whitelabel?.is_enabled ? 'text-emerald-400' : 'text-slate-500'}>
                                {tenant.whitelabel?.is_enabled ? tenant.whitelabel.brand_name || 'Enabled' : 'Disabled'}
                            </span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Usage */}
            {usage?.counters?.length > 0 && (
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                    <h2 className="text-xs font-semibold text-slate-400 uppercase mb-3 flex items-center gap-2">
                        <BarChart2 className="h-3.5 w-3.5" /> Usage Counters
                    </h2>
                    <div className="grid grid-cols-3 gap-3">
                        {usage.counters.map((c: any) => (
                            <div key={`${c.period}:${c.metric}`} className="bg-slate-800 rounded-lg p-3">
                                <p className="text-xs text-slate-500">{c.metric}</p>
                                <p className="text-lg font-bold text-slate-100">{c.value.toLocaleString()}</p>
                                <p className="text-xs text-slate-600">{c.period}</p>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Users */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl">
                <div className="px-5 py-4 border-b border-slate-800">
                    <h2 className="text-sm font-semibold text-slate-200">Users ({users.length})</h2>
                </div>
                <div className="divide-y divide-slate-800">
                    {users.length === 0 && <p className="px-5 py-6 text-sm text-slate-600 text-center">No users</p>}
                    {users.map((u: any) => (
                        <div key={u.user_id} className="px-5 py-3 flex items-center justify-between">
                            <div>
                                <p className="text-sm text-slate-200">{u.name || u.email}</p>
                                <p className="text-xs text-slate-500">{u.email}</p>
                            </div>
                            <span className="text-xs text-slate-500 bg-slate-800 px-2 py-0.5 rounded">{u.role}</span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
