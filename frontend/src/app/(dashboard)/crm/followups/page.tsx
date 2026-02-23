"use client";

import { useState, useEffect } from "react";
import { Plus, Zap, Clock, CheckCircle2, XCircle, PauseCircle, PlayCircle, History } from "lucide-react";
import { useRouter } from "next/navigation";
import { formatDistanceToNow } from "date-fns";
import { BASE_URL } from "@/lib/api";

export default function FollowUpRulesPage() {
    const [rules, setRules] = useState([]);
    const [loading, setLoading] = useState(true);
    const router = useRouter();

    useEffect(() => {
        fetchRules();
    }, []);

    const fetchRules = async () => {
        try {
            const token = localStorage.getItem("access_token");
            const res = await fetch(`${BASE_URL}/crm/followups/rules`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setRules(data);
            }
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const toggleRule = async (id: string) => {
        try {
            const token = localStorage.getItem("access_token");
            const res = await fetch(`${BASE_URL}/crm/followups/rules/${id}/toggle`, {
                method: "POST",
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (res.ok) {
                fetchRules();
            }
        } catch (err) {
            console.error(err);
        }
    };

    return (
        <div className="p-6 max-w-7xl mx-auto">
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h1 className="text-2xl font-bold text-white">Follow-Up Rules</h1>
                    <p className="text-sm text-navy-400">Automate revenue collection with reply-aware chasers</p>
                </div>
                <div className="flex gap-3">
                    <button
                        onClick={() => router.push("/crm/followups/executions")}
                        className="flex items-center gap-2 px-4 py-2 bg-navy-800 text-white rounded-lg font-semibold hover:bg-navy-700 transition-colors border border-navy-700"
                    >
                        <History className="h-4 w-4" />
                        Audit Log
                    </button>
                    <button
                        onClick={() => router.push("/crm/followups/new")}
                        className="flex items-center gap-2 px-4 py-2 bg-[#f5a623] text-navy-950 rounded-lg font-semibold hover:bg-gold-500 transition-colors"
                    >
                        <Plus className="h-4 w-4" />
                        New Rule
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {loading ? (
                    <div className="col-span-3 text-center text-navy-500 py-12">Loading rules...</div>
                ) : rules.length === 0 ? (
                    <div className="col-span-3 text-center text-navy-500 py-12 bg-[#0e1e33]/50 rounded-xl border border-[#1e3a5f] border-dashed">
                        No active follow-up rules. Create one to start automating.
                    </div>
                ) : (
                    rules.map((rule: any) => (
                        <div key={rule.id} className={`bg-[#0e1e33] border ${rule.is_active ? 'border-navy-700' : 'border-[#1e3a5f] opacity-75'} rounded-xl p-6 transition-all`}>
                            <div className="flex justify-between items-start mb-4">
                                <div className="flex items-center gap-3">
                                    <div className={`h-10 w-10 rounded-lg flex items-center justify-center ${rule.is_active ? 'bg-gold-500/10 text-[#f5a623]' : 'bg-navy-800 text-navy-500'}`}>
                                        <Zap className="h-5 w-5" />
                                    </div>
                                    <div>
                                        <h3 className="font-bold text-white text-lg">{rule.name}</h3>
                                        <div className="flex items-center gap-2 text-xs text-navy-400">
                                            <span className="capitalize">{rule.trigger_event.replace('_', ' ')}</span>
                                            <span>•</span>
                                            <span>{rule.channel}</span>
                                        </div>
                                    </div>
                                </div>
                                <button onClick={() => toggleRule(rule.id)} className="text-navy-400 hover:text-white transition-colors">
                                    {rule.is_active ? <PauseCircle className="h-6 w-6 text-green-400" /> : <PlayCircle className="h-6 w-6" />}
                                </button>
                            </div>

                            <div className="space-y-3 mb-6">
                                <div className="flex justify-between text-sm">
                                    <span className="text-navy-400 flex items-center gap-1"><Clock className="h-3 w-3" /> Delay</span>
                                    <span className="text-white font-mono">{rule.delay_minutes / 60}h</span>
                                </div>
                                <div className="flex justify-between text-sm">
                                    <span className="text-navy-400">Max Attempts</span>
                                    <span className="text-white font-mono">{rule.max_attempts}</span>
                                </div>
                            </div>

                            <div className="bg-navy-950 p-3 rounded text-xs text-navy-300 font-mono line-clamp-2 mb-4 h-12">
                                {rule.template_body}
                            </div>

                            <div className="flex justify-between items-center text-xs text-navy-500 pt-4 border-t border-[#1e3a5f]">
                                <span>Created {formatDistanceToNow(new Date(rule.created_at), { addSuffix: true })}</span>
                                <div className="flex items-center gap-1">
                                    <div className={`h-1.5 w-1.5 rounded-full ${rule.is_active ? 'bg-green-500' : 'bg-gray-500'}`}></div>
                                    {rule.is_active ? 'Active' : 'Paused'}
                                </div>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}
