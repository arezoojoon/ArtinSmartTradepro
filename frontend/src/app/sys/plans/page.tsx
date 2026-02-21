'use client';

import { useEffect, useState } from 'react';
import { listPlans, upsertPlan } from '@/lib/sys-api';
import { Plus, Save, ChevronDown, ChevronRight } from 'lucide-react';

const DEFAULT_PLAN = {
    code: '',
    name: '',
    description: '',
    monthly_price_usd: 0,
    features: { brain_engines: true, hunter: true, messaging: true, api_access: true, whitelabel: false },
    limits: { messages_sent_daily: 500, leads_created_monthly: 200, brain_runs_daily: 50, seats: 5 },
};

export default function SysPlansPage() {
    const [plans, setPlans] = useState<any[]>([]);
    const [editing, setEditing] = useState<any | null>(null);
    const [saving, setSaving] = useState(false);
    const [expanded, setExpanded] = useState<string | null>(null);
    const [error, setError] = useState('');

    const load = async () => {
        const r = await listPlans();
        setPlans(r);
    };
    useEffect(() => { load(); }, []);

    const handleSave = async () => {
        if (!editing) return;
        setSaving(true);
        setError('');
        try {
            await upsertPlan(editing);
            await load();
            setEditing(null);
        } catch (e: any) { setError(e.message); }
        finally { setSaving(false); }
    };

    return (
        <div className="space-y-5 max-w-3xl">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-xl font-bold text-slate-100">Plans</h1>
                    <p className="text-sm text-slate-500">{plans.length} configured plans</p>
                </div>
                <button
                    onClick={() => setEditing({ ...DEFAULT_PLAN })}
                    className="flex items-center gap-1.5 px-3 py-2 bg-amber-500 hover:bg-amber-400 text-slate-900 font-medium rounded-lg text-sm transition"
                >
                    <Plus className="h-4 w-4" /> New Plan
                </button>
            </div>

            {/* Plan cards */}
            <div className="space-y-3">
                {plans.map((p: any) => (
                    <div key={p.id} className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
                        <button
                            onClick={() => setExpanded(expanded === p.id ? null : p.id)}
                            className="w-full flex items-center justify-between px-5 py-4 hover:bg-slate-800/50 transition"
                        >
                            <div className="flex items-center gap-3">
                                <span className="text-xs font-mono bg-slate-800 text-amber-400 px-2 py-0.5 rounded">{p.code}</span>
                                <span className="text-sm font-medium text-slate-200">{p.name}</span>
                                {p.monthly_price_usd != null && (
                                    <span className="text-xs text-slate-500">${p.monthly_price_usd}/mo</span>
                                )}
                            </div>
                            <div className="flex items-center gap-2">
                                <button onClick={e => { e.stopPropagation(); setEditing({ ...p }); }}
                                    className="text-xs text-slate-500 hover:text-amber-400 px-2 py-1 rounded hover:bg-slate-800 transition">
                                    Edit
                                </button>
                                {expanded === p.id ? <ChevronDown className="h-4 w-4 text-slate-500" /> : <ChevronRight className="h-4 w-4 text-slate-500" />}
                            </div>
                        </button>
                        {expanded === p.id && (
                            <div className="px-5 pb-4 border-t border-slate-800 pt-4 grid grid-cols-2 gap-4">
                                <div>
                                    <p className="text-xs font-medium text-slate-500 uppercase mb-2">Features</p>
                                    <div className="space-y-1">
                                        {Object.entries(p.features || {}).map(([k, v]) => (
                                            <div key={k} className="flex items-center gap-2 text-xs">
                                                <span className={v ? 'text-emerald-400' : 'text-slate-600'}>{v ? '✓' : '✗'}</span>
                                                <span className="text-slate-400">{k}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                                <div>
                                    <p className="text-xs font-medium text-slate-500 uppercase mb-2">Limits</p>
                                    <div className="space-y-1">
                                        {Object.entries(p.limits || {}).map(([k, v]) => (
                                            <div key={k} className="flex justify-between text-xs">
                                                <span className="text-slate-400">{k}</span>
                                                <span className="text-slate-200 font-mono">{v === -1 ? '∞' : String(v)}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                ))}
            </div>

            {/* Edit Modal */}
            {editing && (
                <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
                    <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-lg max-h-[85vh] overflow-y-auto p-6 space-y-4">
                        <h2 className="text-lg font-bold text-slate-100">{editing.id ? 'Edit Plan' : 'New Plan'}</h2>

                        <div className="grid grid-cols-2 gap-3">
                            {(['code', 'name'] as const).map(field => (
                                <div key={field}>
                                    <label className="text-xs text-slate-400 mb-1 block capitalize">{field}</label>
                                    <input value={editing[field] || ''} onChange={e => setEditing({ ...editing, [field]: e.target.value })}
                                        className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-slate-100 focus:outline-none focus:border-amber-500"
                                        disabled={!!editing.id && field === 'code'} />
                                </div>
                            ))}
                            <div className="col-span-2">
                                <label className="text-xs text-slate-400 mb-1 block">Monthly Price (USD)</label>
                                <input type="number" value={editing.monthly_price_usd || 0} onChange={e => setEditing({ ...editing, monthly_price_usd: +e.target.value })}
                                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-slate-100 focus:outline-none focus:border-amber-500" />
                            </div>
                        </div>

                        <div>
                            <label className="text-xs text-slate-400 mb-1 block">Features (JSON)</label>
                            <textarea rows={4} value={JSON.stringify(editing.features, null, 2)}
                                onChange={e => { try { setEditing({ ...editing, features: JSON.parse(e.target.value) }); } catch { } }}
                                className="w-full font-mono px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-amber-500" />
                        </div>

                        <div>
                            <label className="text-xs text-slate-400 mb-1 block">Limits (JSON) — use -1 for unlimited</label>
                            <textarea rows={6} value={JSON.stringify(editing.limits, null, 2)}
                                onChange={e => { try { setEditing({ ...editing, limits: JSON.parse(e.target.value) }); } catch { } }}
                                className="w-full font-mono px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-amber-500" />
                        </div>

                        {error && <p className="text-xs text-red-400">{error}</p>}

                        <div className="flex gap-3 justify-end">
                            <button onClick={() => setEditing(null)} className="px-4 py-2 text-sm text-slate-400 hover:text-slate-200">Cancel</button>
                            <button onClick={handleSave} disabled={saving}
                                className="flex items-center gap-1.5 px-4 py-2 bg-amber-500 hover:bg-amber-400 disabled:opacity-60 text-slate-900 font-medium rounded-lg text-sm transition">
                                <Save className="h-4 w-4" /> {saving ? 'Saving…' : 'Save Plan'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
