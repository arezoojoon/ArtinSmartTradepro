"use client";

import { useState, useEffect } from "react";
import { Plus, MoreHorizontal, LayoutGrid, List, X, Loader2 } from "lucide-react";
import api from "@/lib/api";
import Link from "next/link";

export default function PipelinesPage() {
    const [pipelines, setPipelines] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [saving, setSaving] = useState(false);
    const [form, setForm] = useState({ name: "", stages: "Lead, Qualified, Proposal, Negotiation, Won, Lost" });

    useEffect(() => {
        fetchPipelines();
    }, []);

    const fetchPipelines = async () => {
        setLoading(true);
        try {
            const res = await api.get("/crm/pipelines");
            setPipelines(res.data.pipelines || res.data || []);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const createPipeline = async () => {
        if (!form.name.trim()) return;
        setSaving(true);
        try {
            const stages = form.stages.split(",").map((s, i) => ({ name: s.trim(), order: i })).filter(s => s.name);
            await api.post("/crm/pipelines", { name: form.name, stages });
            setShowModal(false);
            setForm({ name: "", stages: "Lead, Qualified, Proposal, Negotiation, Won, Lost" });
            fetchPipelines();
        } catch (e) { console.error("Failed to create pipeline", e); }
        finally { setSaving(false); }
    };

    const openModal = () => { setForm({ name: "", stages: "Lead, Qualified, Proposal, Negotiation, Won, Lost" }); setShowModal(true); };

    return (
        <div className="p-6 max-w-7xl mx-auto">
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h1 className="text-2xl font-bold text-white">Pipelines & Deals</h1>
                    <p className="text-sm text-navy-400">Manage your sales pipelines and track deals</p>
                </div>
                <button onClick={openModal} className="flex items-center gap-2 px-4 py-2 bg-[#f5a623] text-navy-950 rounded-lg font-semibold hover:bg-gold-500 transition-colors">
                    <Plus className="h-4 w-4" />
                    Create Pipeline
                </button>
            </div>

            {loading ? (
                <div className="text-center py-12 text-navy-500">Loading pipelines...</div>
            ) : pipelines.length === 0 ? (
                <div className="text-center py-12 bg-[#0e1e33] border border-[#1e3a5f] rounded-xl">
                    <div className="text-navy-400 mb-2">No pipelines configured yet.</div>
                    <button onClick={openModal} className="text-[#f5a623] font-medium hover:underline">Create your first pipeline</button>
                </div>
            ) : (
                <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                    {pipelines.map((pipeline: any) => (
                        <div key={pipeline.id} className="bg-[#0e1e33] border border-[#1e3a5f] rounded-xl p-5 hover:border-navy-700 transition-all flex flex-col">
                            <div className="flex justify-between items-start mb-4">
                                <h3 className="text-lg font-semibold text-white">{pipeline.name}</h3>
                                <button className="text-navy-400 hover:text-white">
                                    <MoreHorizontal className="h-5 w-5" />
                                </button>
                            </div>

                            <div className="mb-6 flex-1">
                                <p className="text-xs font-semibold text-navy-400 mb-2 uppercase tracking-wider">Stages</p>
                                <div className="flex flex-wrap gap-2">
                                    {pipeline.stages?.map((stage: any, idx: number) => (
                                        <div key={idx} className="px-2 py-1 bg-navy-950 border border-[#1e3a5f] rounded text-xs text-navy-300">
                                            {stage.name}
                                        </div>
                                    ))}
                                </div>
                            </div>

                            <div className="pt-4 border-t border-[#1e3a5f] flex gap-3">
                                <Link
                                    href={`/crm/pipelines/${pipeline.id}/board`}
                                    className="flex-1 flex items-center justify-center gap-2 py-2 bg-navy-800 hover:bg-navy-700 rounded-lg text-sm font-medium text-white transition-colors"
                                >
                                    <LayoutGrid className="h-4 w-4 text-[#f5a623]" />
                                    Board View
                                </Link>
                                <Link
                                    href={`/crm/pipelines/${pipeline.id}/list`}
                                    className="flex items-center justify-center p-2 bg-navy-800 hover:bg-navy-700 rounded-lg transition-colors text-navy-300 hover:text-white"
                                    title="List View"
                                >
                                    <List className="h-4 w-4" />
                                </Link>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Create Pipeline Modal */}
            {showModal && (
                <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4" onClick={() => setShowModal(false)}>
                    <div className="bg-[#0e1e33] border border-[#1e3a5f] rounded-2xl w-full max-w-md p-6" onClick={e => e.stopPropagation()}>
                        <div className="flex justify-between items-center mb-5">
                            <h3 className="text-lg font-bold text-white">Create Pipeline</h3>
                            <button onClick={() => setShowModal(false)} className="text-navy-400 hover:text-white"><X className="h-5 w-5" /></button>
                        </div>
                        <div className="space-y-4">
                            <div>
                                <label className="block text-xs text-navy-400 mb-1">Pipeline Name *</label>
                                <input value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} placeholder="e.g. Main Sales Pipeline" className="w-full px-3 py-2 bg-navy-800 border border-navy-600 rounded-lg text-white text-sm focus:border-gold-400 focus:outline-none" />
                            </div>
                            <div>
                                <label className="block text-xs text-navy-400 mb-1">Stages (comma-separated)</label>
                                <input value={form.stages} onChange={e => setForm(f => ({ ...f, stages: e.target.value }))} className="w-full px-3 py-2 bg-navy-800 border border-navy-600 rounded-lg text-white text-sm focus:border-gold-400 focus:outline-none" />
                                <p className="text-[10px] text-navy-600 mt-1">Separate stage names with commas</p>
                            </div>
                        </div>
                        <button onClick={createPipeline} disabled={saving || !form.name.trim()} className="mt-6 w-full py-2.5 bg-[#f5a623] text-navy-950 rounded-lg font-semibold hover:bg-gold-300 transition-all disabled:opacity-50 flex items-center justify-center gap-2">
                            {saving ? <><Loader2 className="h-4 w-4 animate-spin" /> Creating...</> : <><Plus className="h-4 w-4" /> Create Pipeline</>}
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}
