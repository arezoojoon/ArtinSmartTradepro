'use client';

import { useEffect, useState } from 'react';
import { listWlDomains, activateDomain } from '@/lib/sys-api';
import { Globe, CheckCircle, XCircle, Clock } from 'lucide-react';

const STATUS_ICON: Record<string, React.ElementType> = {
    active: CheckCircle,
    pending_dns: Clock,
    disabled: XCircle,
};
const STATUS_COLOR: Record<string, string> = {
    active: 'text-emerald-400',
    pending_dns: 'text-amber-400',
    disabled: 'text-red-400',
};

export default function SysWhitelabelPage() {
    const [domains, setDomains] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [acting, setActing] = useState<string | null>(null);

    const load = async () => {
        setLoading(true);
        try { setDomains(await listWlDomains()); } finally { setLoading(false); }
    };

    useEffect(() => { load(); }, []);

    const handleActivate = async (d: any) => {
        if (!confirm(`Activate domain '${d.domain}'? This is audited.`)) return;
        setActing(d.id);
        try { await activateDomain(d.id); await load(); } finally { setActing(null); }
    };

    return (
        <div className="space-y-5">
            <div>
                <h1 className="text-xl font-bold text-slate-100">White-label Domains</h1>
                <p className="text-sm text-slate-500">Manually verify and activate custom domain requests</p>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
                {loading && <div className="text-center py-10 text-slate-600 text-sm">Loading…</div>}
                {!loading && domains.length === 0 && (
                    <div className="text-center py-10 text-slate-600 text-sm">No domain requests yet</div>
                )}
                {domains.map(d => {
                    const Icon = STATUS_ICON[d.status] || Clock;
                    return (
                        <div key={d.id} className="px-5 py-4 border-b border-slate-800 last:border-0 flex items-start justify-between">
                            <div className="space-y-1">
                                <div className="flex items-center gap-2">
                                    <Globe className="h-4 w-4 text-slate-500 flex-shrink-0" />
                                    <span className="text-sm font-medium text-slate-200">{d.domain}</span>
                                    <span className={`flex items-center gap-1 text-xs font-medium ${STATUS_COLOR[d.status]}`}>
                                        <Icon className="h-3 w-3" /> {d.status}
                                    </span>
                                </div>
                                <div className="text-xs text-slate-600 font-mono ml-6">Tenant: {d.tenant_id?.slice(0, 16)}…</div>
                                {d.verification_token && (
                                    <div className="ml-6 mt-2 bg-slate-800 rounded-lg px-3 py-2">
                                        <p className="text-xs text-slate-500 mb-1">DNS Verification TXT Record</p>
                                        <p className="font-mono text-xs text-amber-400">_artin-verify.{d.domain}</p>
                                        <p className="font-mono text-xs text-slate-400 mt-0.5 break-all">{d.verification_token}</p>
                                    </div>
                                )}
                                {d.verified_at && <div className="text-xs text-slate-600 ml-6">Verified {new Date(d.verified_at).toLocaleDateString()}</div>}
                            </div>
                            <div className="ml-4 flex-shrink-0">
                                {d.status === 'pending_dns' && (
                                    <button
                                        onClick={() => handleActivate(d)}
                                        disabled={acting === d.id}
                                        className="px-3 py-1.5 text-xs bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 rounded-lg transition"
                                    >
                                        {acting === d.id ? 'Activating…' : 'Activate'}
                                    </button>
                                )}
                            </div>
                        </div>
                    );
                })}
            </div>

            <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4 text-xs text-slate-500 space-y-1">
                <p className="font-medium text-slate-400">How domain verification works:</p>
                <p>1. Tenant submits domain via the API → gets a verification token</p>
                <p>2. Tenant adds <code className="text-amber-400">TXT _artin-verify.&lt;domain&gt;</code> with the token to their DNS</p>
                <p>3. Sys admin verifies the DNS record manually and clicks Activate here</p>
            </div>
        </div>
    );
}
