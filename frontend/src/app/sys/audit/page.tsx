'use client';

import { useEffect, useState } from 'react';
import { listAuditLogs } from '@/lib/sys-api';
import { Search } from 'lucide-react';

export default function SysAuditPage() {
    const [logs, setLogs] = useState<{ total: number; items: any[] }>({ total: 0, items: [] });
    const [action, setAction] = useState('');
    const [loading, setLoading] = useState(true);
    const [selected, setSelected] = useState<any>(null);
    const [page, setPage] = useState(0);
    const limit = 50;

    const load = async () => {
        setLoading(true);
        try {
            const r = await listAuditLogs({ action: action || undefined, limit, offset: page * limit });
            setLogs(r);
        } finally { setLoading(false); }
    };

    useEffect(() => { load(); }, [action, page]);

    return (
        <div className="space-y-5">
            <div>
                <h1 className="text-xl font-bold text-slate-100">Audit Logs</h1>
                <p className="text-sm text-slate-500">{logs.total} total entries</p>
            </div>

            <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                <input value={action} onChange={e => { setAction(e.target.value); setPage(0); }}
                    placeholder="Filter by action (e.g. tenant_suspend)…"
                    className="w-full pl-9 pr-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-amber-500" />
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
                <table className="w-full text-sm">
                    <thead className="border-b border-slate-800">
                        <tr>
                            <th className="text-left px-4 py-3 text-xs font-medium text-slate-500 uppercase">Action</th>
                            <th className="text-left px-4 py-3 text-xs font-medium text-slate-500 uppercase">Resource</th>
                            <th className="text-left px-4 py-3 text-xs font-medium text-slate-500 uppercase">IP</th>
                            <th className="text-left px-4 py-3 text-xs font-medium text-slate-500 uppercase">Time</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800">
                        {loading && <tr><td colSpan={4} className="text-center py-10 text-slate-600">Loading…</td></tr>}
                        {!loading && logs.items.length === 0 && <tr><td colSpan={4} className="text-center py-10 text-slate-600">No logs</td></tr>}
                        {logs.items.map(l => (
                            <tr key={l.id} onClick={() => setSelected(selected?.id === l.id ? null : l)}
                                className="hover:bg-slate-800/50 cursor-pointer">
                                <td className="px-4 py-3">
                                    <span className="font-mono text-xs bg-slate-800 text-amber-400 px-1.5 py-0.5 rounded">{l.action}</span>
                                </td>
                                <td className="px-4 py-3 text-xs text-slate-400">
                                    {l.resource_type} {l.resource_id?.slice(0, 8) && <span className="text-slate-600">({l.resource_id.slice(0, 8)})</span>}
                                </td>
                                <td className="px-4 py-3 text-xs text-slate-500">{l.ip_address || '—'}</td>
                                <td className="px-4 py-3 text-xs text-slate-600">{l.created_at ? new Date(l.created_at).toLocaleString() : '—'}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between">
                <button onClick={() => setPage(p => Math.max(0, p - 1))} disabled={page === 0}
                    className="text-xs text-slate-400 hover:text-slate-200 disabled:opacity-30">← Prev</button>
                <span className="text-xs text-slate-600">Page {page + 1}</span>
                <button onClick={() => setPage(p => p + 1)} disabled={(page + 1) * limit >= logs.total}
                    className="text-xs text-slate-400 hover:text-slate-200 disabled:opacity-30">Next →</button>
            </div>

            {/* Detail drawer */}
            {selected && (
                <div className="fixed right-0 top-0 h-full w-96 bg-slate-900 border-l border-slate-800 z-50 overflow-y-auto p-5 shadow-2xl">
                    <button onClick={() => setSelected(null)} className="text-xs text-slate-500 hover:text-slate-300 mb-4">✕ Close</button>
                    <h3 className="text-sm font-bold text-slate-100 mb-4">{selected.action}</h3>
                    <div className="space-y-3 text-xs">
                        {['resource_type', 'resource_id', 'tenant_id', 'actor_sys_admin_id', 'ip_address'].map(k => selected[k] && (
                            <div key={k}><p className="text-slate-500 mb-0.5">{k}</p><p className="text-slate-300 font-mono break-all">{selected[k]}</p></div>
                        ))}
                        {selected.before_state && (
                            <div><p className="text-slate-500 mb-1">Before</p>
                                <pre className="bg-slate-800 rounded p-2 text-xs text-slate-400 overflow-auto">{JSON.stringify(selected.before_state, null, 2)}</pre>
                            </div>
                        )}
                        {selected.after_state && (
                            <div><p className="text-slate-500 mb-1">After</p>
                                <pre className="bg-slate-800 rounded p-2 text-xs text-emerald-400 overflow-auto">{JSON.stringify(selected.after_state, null, 2)}</pre>
                            </div>
                        )}
                        {selected.metadata && (
                            <div><p className="text-slate-500 mb-1">Metadata</p>
                                <pre className="bg-slate-800 rounded p-2 text-xs text-slate-400 overflow-auto">{JSON.stringify(selected.metadata, null, 2)}</pre>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}
