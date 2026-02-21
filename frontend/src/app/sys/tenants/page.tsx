'use client';

import { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { Search, CheckCircle, XCircle, UserX, UserCheck, Eye } from 'lucide-react';
import { listTenants, suspendTenant, restoreTenant } from '@/lib/sys-api';

export default function SysTenantsPage() {
    const [query, setQuery] = useState('');
    const [data, setData] = useState<{ total: number; items: any[] }>({ total: 0, items: [] });
    const [loading, setLoading] = useState(true);
    const [actionId, setActionId] = useState<string | null>(null);

    const load = useCallback(async () => {
        setLoading(true);
        try { const r = await listTenants(query); setData(r); } finally { setLoading(false); }
    }, [query]);

    useEffect(() => { load(); }, [load]);

    const handleSuspend = async (id: string, active: boolean) => {
        if (!confirm(`Are you sure you want to ${active ? 'suspend' : 'restore'} this tenant? This action is audited.`)) return;
        setActionId(id);
        try {
            if (active) await suspendTenant(id);
            else await restoreTenant(id);
            await load();
        } finally { setActionId(null); }
    };

    return (
        <div className="space-y-5">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-xl font-bold text-slate-100">Tenants</h1>
                    <p className="text-sm text-slate-500">{data.total} total</p>
                </div>
            </div>

            {/* Search */}
            <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                <input
                    value={query}
                    onChange={e => setQuery(e.target.value)}
                    placeholder="Search by name…"
                    className="w-full pl-9 pr-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-amber-500"
                />
            </div>

            {/* Table */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
                <table className="w-full text-sm">
                    <thead className="border-b border-slate-800">
                        <tr>
                            <th className="text-left px-4 py-3 text-xs font-medium text-slate-500 uppercase">Tenant</th>
                            <th className="text-left px-4 py-3 text-xs font-medium text-slate-500 uppercase">Status</th>
                            <th className="text-left px-4 py-3 text-xs font-medium text-slate-500 uppercase">Created</th>
                            <th className="px-4 py-3 text-xs font-medium text-slate-500 uppercase text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800">
                        {loading && (
                            <tr><td colSpan={4} className="text-center py-10 text-slate-600">Loading…</td></tr>
                        )}
                        {!loading && data.items.length === 0 && (
                            <tr><td colSpan={4} className="text-center py-10 text-slate-600">No tenants found</td></tr>
                        )}
                        {data.items.map((t: any) => (
                            <tr key={t.id} className="hover:bg-slate-800/50">
                                <td className="px-4 py-3">
                                    <div className="font-medium text-slate-200">{t.name}</div>
                                    <div className="text-xs text-slate-600 font-mono">{t.id}</div>
                                </td>
                                <td className="px-4 py-3">
                                    {t.is_active ? (
                                        <span className="inline-flex items-center gap-1 text-xs text-emerald-400 bg-emerald-400/10 px-2 py-0.5 rounded-full">
                                            <CheckCircle className="h-3 w-3" /> Active
                                        </span>
                                    ) : (
                                        <span className="inline-flex items-center gap-1 text-xs text-red-400 bg-red-400/10 px-2 py-0.5 rounded-full">
                                            <XCircle className="h-3 w-3" /> Suspended
                                        </span>
                                    )}
                                </td>
                                <td className="px-4 py-3 text-xs text-slate-500">
                                    {t.created_at ? new Date(t.created_at).toLocaleDateString() : '—'}
                                </td>
                                <td className="px-4 py-3 text-right">
                                    <div className="flex items-center justify-end gap-2">
                                        <Link
                                            href={`/sys/tenants/${t.id}`}
                                            className="p-1.5 rounded text-slate-400 hover:text-sky-400 hover:bg-sky-400/10 transition"
                                            title="View detail"
                                        >
                                            <Eye className="h-4 w-4" />
                                        </Link>
                                        <button
                                            onClick={() => handleSuspend(t.id, t.is_active)}
                                            disabled={actionId === t.id}
                                            className={`p-1.5 rounded transition ${t.is_active ? 'text-slate-400 hover:text-red-400 hover:bg-red-400/10' : 'text-slate-400 hover:text-emerald-400 hover:bg-emerald-400/10'}`}
                                            title={t.is_active ? 'Suspend' : 'Restore'}
                                        >
                                            {t.is_active ? <UserX className="h-4 w-4" /> : <UserCheck className="h-4 w-4" />}
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
