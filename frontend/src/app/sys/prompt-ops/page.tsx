'use client';

import { useEffect, useState } from 'react';
import {
    listPromptFamilies, listPromptVersions, createPromptFamily, createPromptVersion,
    approveVersion, deprecateVersion, listPromptRuns,
} from '@/lib/sys-api';
import { Plus, CheckCircle, XCircle, Clock, ChevronRight } from 'lucide-react';

const STATUS_COLOR: Record<string, string> = {
    draft: 'text-slate-400 bg-slate-800',
    approved: 'text-emerald-400 bg-emerald-400/10',
    deprecated: 'text-red-400 bg-red-400/10',
    success: 'text-emerald-400 bg-emerald-400/10',
    guardrail_rejected: 'text-red-400 bg-red-400/10',
    error: 'text-orange-400 bg-orange-400/10',
};

export default function SysPromptOpsPage() {
    const [families, setFamilies] = useState<any[]>([]);
    const [selectedFamily, setSelectedFamily] = useState<any>(null);
    const [versions, setVersions] = useState<any[]>([]);
    const [runs, setRuns] = useState<{ total: number; items: any[] }>({ total: 0, items: [] });
    const [tab, setTab] = useState<'versions' | 'runs'>('versions');
    const [acting, setActing] = useState<string | null>(null);
    const [newFamilyName, setNewFamilyName] = useState('');
    const [showNewFamily, setShowNewFamily] = useState(false);

    const loadFamilies = async () => {
        const r = await listPromptFamilies();
        setFamilies(r);
    };

    const loadFamily = async (f: any) => {
        setSelectedFamily(f);
        const [v, r] = await Promise.all([
            listPromptVersions(f.id),
            listPromptRuns({ family: f.name, limit: 20 }),
        ]);
        setVersions(v);
        setRuns(r);
    };

    useEffect(() => { loadFamilies(); }, []);

    const handleApprove = async (vId: string) => {
        if (!confirm('Approve this version? All other versions for this family will be deprecated.')) return;
        setActing(vId);
        try { await approveVersion(vId); if (selectedFamily) await loadFamily(selectedFamily); }
        finally { setActing(null); }
    };

    const handleDeprecate = async (vId: string) => {
        setActing(vId);
        try { await deprecateVersion(vId); if (selectedFamily) await loadFamily(selectedFamily); }
        finally { setActing(null); }
    };

    const handleCreateFamily = async () => {
        if (!newFamilyName) return;
        await createPromptFamily({ name: newFamilyName });
        setNewFamilyName('');
        setShowNewFamily(false);
        await loadFamilies();
    };

    return (
        <div className="flex gap-5 h-[calc(100vh-6rem)]">
            {/* Family list */}
            <div className="w-52 flex-shrink-0 bg-slate-900 border border-slate-800 rounded-xl flex flex-col">
                <div className="px-4 py-3 border-b border-slate-800 flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-400 uppercase">Families</span>
                    <button onClick={() => setShowNewFamily(true)} className="text-amber-400 hover:text-amber-300">
                        <Plus className="h-4 w-4" />
                    </button>
                </div>
                {showNewFamily && (
                    <div className="px-3 py-2 border-b border-slate-800 flex gap-2">
                        <input value={newFamilyName} onChange={e => setNewFamilyName(e.target.value)}
                            placeholder="family_name" className="flex-1 text-xs bg-slate-800 border border-slate-700 rounded px-2 py-1 text-slate-200 focus:outline-none focus:border-amber-500" />
                        <button onClick={handleCreateFamily} className="text-xs text-amber-400 font-medium">Add</button>
                    </div>
                )}
                <div className="flex-1 overflow-y-auto divide-y divide-slate-800">
                    {families.map(f => (
                        <button key={f.id} onClick={() => loadFamily(f)}
                            className={`w-full text-left px-4 py-3 flex items-center justify-between hover:bg-slate-800/60 transition ${selectedFamily?.id === f.id ? 'bg-amber-500/10' : ''}`}>
                            <span className={`text-xs ${selectedFamily?.id === f.id ? 'text-amber-400' : 'text-slate-400'}`}>{f.name}</span>
                            <ChevronRight className="h-3 w-3 text-slate-600" />
                        </button>
                    ))}
                </div>
            </div>

            {/* Detail */}
            <div className="flex-1 bg-slate-900 border border-slate-800 rounded-xl flex flex-col overflow-hidden">
                {!selectedFamily ? (
                    <div className="flex items-center justify-center h-full text-slate-600 text-sm">Select a prompt family</div>
                ) : (
                    <>
                        <div className="px-5 py-4 border-b border-slate-800">
                            <h2 className="text-sm font-bold text-slate-100">{selectedFamily.name}</h2>
                            <div className="flex gap-4 mt-3">
                                {(['versions', 'runs'] as const).map(t => (
                                    <button key={t} onClick={() => setTab(t)}
                                        className={`text-xs pb-1 border-b-2 font-medium transition ${tab === t ? 'border-amber-500 text-amber-400' : 'border-transparent text-slate-500 hover:text-slate-300'}`}>
                                        {t === 'versions' ? `Versions (${versions.length})` : `Runs (${runs.total})`}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="flex-1 overflow-y-auto p-4 space-y-3">
                            {tab === 'versions' && versions.map(v => (
                                <div key={v.id} className="bg-slate-800 rounded-lg p-4">
                                    <div className="flex items-center justify-between mb-2">
                                        <div className="flex items-center gap-2">
                                            <span className="text-sm font-bold text-slate-200">v{v.version}</span>
                                            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_COLOR[v.status]}`}>{v.status}</span>
                                            <span className="text-xs text-slate-600">{v.model_target}</span>
                                        </div>
                                        <div className="flex gap-2">
                                            {v.status !== 'approved' && (
                                                <button onClick={() => handleApprove(v.id)} disabled={acting === v.id}
                                                    className="text-xs px-2 py-1 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 rounded transition flex items-center gap-1">
                                                    <CheckCircle className="h-3 w-3" /> Approve
                                                </button>
                                            )}
                                            {v.status !== 'deprecated' && (
                                                <button onClick={() => handleDeprecate(v.id)} disabled={acting === v.id}
                                                    className="text-xs px-2 py-1 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded transition flex items-center gap-1">
                                                    <XCircle className="h-3 w-3" /> Deprecate
                                                </button>
                                            )}
                                        </div>
                                    </div>
                                    {Object.keys(v.guardrails || {}).length > 0 && (
                                        <div className="text-xs text-slate-500">
                                            Guardrails: {Object.keys(v.guardrails).filter(k => v.guardrails[k]).join(', ') || 'none'}
                                        </div>
                                    )}
                                    {v.approved_at && (
                                        <div className="text-xs text-slate-600 mt-1">Approved {new Date(v.approved_at).toLocaleDateString()}</div>
                                    )}
                                </div>
                            ))}

                            {tab === 'runs' && runs.items.map(r => (
                                <div key={r.id} className="bg-slate-800 rounded-lg p-3 flex items-center justify-between">
                                    <div>
                                        <div className="flex items-center gap-2">
                                            <span className={`text-xs px-2 py-0.5 rounded-full ${STATUS_COLOR[r.status]}`}>{r.status}</span>
                                            <span className="text-xs text-slate-400">v{r.version}</span>
                                            <span className="text-xs text-slate-600">{r.created_at ? new Date(r.created_at).toLocaleString() : ''}</span>
                                        </div>
                                        {r.guardrail_result && !r.guardrail_result.pass && (
                                            <div className="text-xs text-red-400 mt-1">
                                                {r.guardrail_result.reasons?.slice(0, 1).join(', ')}
                                            </div>
                                        )}
                                    </div>
                                    {r.token_usage && (
                                        <div className="text-xs text-slate-600 text-right">
                                            {r.token_usage.total_tokens || r.token_usage.tokens} tokens
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </>
                )}
            </div>
        </div>
    );
}
