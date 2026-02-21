"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { Plus, MoreHorizontal, MoveRight, ArrowLeft } from "lucide-react";
import { BASE_URL } from "@/lib/api";
import Link from "next/link";

export default function PipelineBoardPage() {
    const params = useParams();
    const router = useRouter();
    const [pipeline, setPipeline] = useState<any>(null);
    const [deals, setDeals] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    const pipelineId = params.id as string;

    useEffect(() => {
        if (pipelineId) {
            fetchPipelineData();
        }
    }, [pipelineId]);

    const fetchPipelineData = async () => {
        setLoading(true);
        try {
            const token = localStorage.getItem("access_token");

            // 1. Fetch Pipelines to find this specific one (since we don't have a GET /pipelines/id endpoint yet)
            const pipeRes = await fetch(`${BASE_URL}/crm/pipelines`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (pipeRes.ok) {
                const pipeData = await pipeRes.json();
                const matched = pipeData.pipelines?.find((p: any) => p.id === pipelineId);
                setPipeline(matched);
            }

            // 2. Fetch Deals for this pipeline
            const dealsRes = await fetch(`${BASE_URL}/crm/deals?pipeline_id=${pipelineId}`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (dealsRes.ok) {
                const dealsData = await dealsRes.json();
                setDeals(dealsData.deals || []);
            }
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return <div className="p-6 text-navy-400">Loading board...</div>;
    }

    if (!pipeline) {
        return (
            <div className="p-6 text-center text-white">
                <p>Pipeline not found.</p>
                <Link href="/crm/pipelines" className="text-gold-400 hover:underline mt-4 inline-block">Back to Pipelines</Link>
            </div>
        );
    }

    const stages = pipeline.stages || [];

    // Group deals by stage
    const columnDeals = (stageId: string) => {
        return deals.filter(d => d.stage_id === stageId);
    };

    return (
        <div className="p-6 max-w-[1600px] mx-auto h-[calc(100vh-6rem)] flex flex-col">
            <div className="flex justify-between items-center mb-6">
                <div className="flex items-center gap-4">
                    <button onClick={() => router.push('/crm/pipelines')} className="p-2 bg-navy-900 border border-navy-800 rounded-lg text-navy-400 hover:text-white hover:bg-navy-800 transition-colors">
                        <ArrowLeft className="h-4 w-4" />
                    </button>
                    <div>
                        <h1 className="text-2xl font-bold text-white">{pipeline.name}</h1>
                        <p className="text-sm text-navy-400">Kanban Board View</p>
                    </div>
                </div>
                <button className="flex items-center gap-2 px-4 py-2 bg-gold-400 text-navy-950 rounded-lg font-semibold hover:bg-gold-500 transition-colors">
                    <Plus className="h-4 w-4" />
                    Add Deal
                </button>
            </div>

            {/* Kanban Columns */}
            <div className="flex-1 flex gap-4 overflow-x-auto pb-4 custom-scrollbar">
                {stages.map((stage: any) => (
                    <div key={stage.id} className="min-w-[320px] w-[320px] flex flex-col bg-navy-900/50 border border-navy-800 rounded-xl p-3">
                        <div className="flex justify-between items-center mb-3 px-1">
                            <h3 className="font-semibold text-navy-200">{stage.name}</h3>
                            <span className="text-xs font-medium text-navy-500 bg-navy-950 px-2 py-0.5 rounded-full">
                                {columnDeals(stage.id).length}
                            </span>
                        </div>

                        <div className="flex-1 space-y-3 overflow-y-auto custom-scrollbar pr-1">
                            {columnDeals(stage.id).map(deal => (
                                <div key={deal.id} className="bg-navy-950 border border-navy-800 p-3 rounded-lg hover:border-gold-500/50 cursor-pointer group transition-all">
                                    <div className="flex justify-between items-start mb-2">
                                        <h4 className="font-medium text-white text-sm line-clamp-2">{deal.name}</h4>
                                        <button className="text-navy-600 hover:text-navy-300 opacity-0 group-hover:opacity-100 transition-opacity">
                                            <MoreHorizontal className="h-4 w-4" />
                                        </button>
                                    </div>
                                    <div className="text-gold-400 font-medium mb-3">
                                        {new Intl.NumberFormat('en-US', { style: 'currency', currency: deal.currency || 'AED', maximumFractionDigits: 0 }).format(deal.value)}
                                    </div>
                                    <div className="flex items-center justify-between text-xs">
                                        <span className="text-navy-400">{deal.probability}% Prob.</span>
                                        <span className="text-navy-500 text-[10px] uppercase font-semibold flex items-center gap-1 hover:text-white">
                                            Move
                                            <MoveRight className="h-3 w-3" />
                                        </span>
                                    </div>
                                </div>
                            ))}

                            {columnDeals(stage.id).length === 0 && (
                                <div className="border-2 border-dashed border-navy-800 rounded-lg p-4 text-center text-navy-600 text-sm">
                                    No deals in this stage
                                </div>
                            )}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
