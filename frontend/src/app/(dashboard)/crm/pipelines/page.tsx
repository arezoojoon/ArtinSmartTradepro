"use client";

import { useState, useEffect } from "react";
import { Plus, MoreHorizontal, LayoutGrid, List } from "lucide-react";
import { BASE_URL } from "@/lib/api";
import Link from "next/link";

export default function PipelinesPage() {
    const [pipelines, setPipelines] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchPipelines();
    }, []);

    const fetchPipelines = async () => {
        setLoading(true);
        try {
            const token = localStorage.getItem("access_token");
            const res = await fetch(`${BASE_URL}/crm/pipelines`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setPipelines(data.pipelines || []);
            }
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="p-6 max-w-7xl mx-auto">
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h1 className="text-2xl font-bold text-white">Pipelines & Deals</h1>
                    <p className="text-sm text-navy-400">Manage your sales pipelines and track deals</p>
                </div>
                <button className="flex items-center gap-2 px-4 py-2 bg-[#f5a623] text-navy-950 rounded-lg font-semibold hover:bg-gold-500 transition-colors">
                    <Plus className="h-4 w-4" />
                    Create Pipeline
                </button>
            </div>

            {loading ? (
                <div className="text-center py-12 text-navy-500">Loading pipelines...</div>
            ) : pipelines.length === 0 ? (
                <div className="text-center py-12 bg-[#0e1e33] border border-[#1e3a5f] rounded-xl">
                    <div className="text-navy-400 mb-2">No pipelines configured yet.</div>
                    <button className="text-[#f5a623] font-medium hover:underline">Create your first pipeline</button>
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
        </div>
    );
}
