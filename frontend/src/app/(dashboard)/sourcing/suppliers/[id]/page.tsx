"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Building2, Loader2, AlertTriangle, ShieldCheck, Clock, Package, TrendingUp, MapPin, BarChart3, Star } from "lucide-react";
import api from "@/lib/api";

export default function SupplierDetailPage() {
    const params = useParams();
    const router = useRouter();
    const supplierId = params.id as string;

    const [loading, setLoading] = useState(true);
    const [data, setData] = useState<any>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (supplierId) fetchScorecard();
    }, [supplierId]);

    const fetchScorecard = async () => {
        setLoading(true);
        try {
            const { data: res } = await api.get(`/sourcing/suppliers/${supplierId}/scorecard`);
            setData(res);
        } catch (err: any) {
            setError(err?.message || "Failed to load supplier data");
        } finally {
            setLoading(false);
        }
    };

    const getScoreColor = (score: number) => {
        if (score >= 80) return "text-emerald-400";
        if (score >= 60) return "text-amber-400";
        return "text-red-400";
    };

    const getScoreBg = (score: number) => {
        if (score >= 80) return "bg-emerald-500/10 border-emerald-500/20";
        if (score >= 60) return "bg-amber-500/10 border-amber-500/20";
        return "bg-red-500/10 border-red-500/20";
    };

    if (loading) return (
        <div className="flex items-center justify-center p-12 text-slate-400">
            <Loader2 className="h-6 w-6 animate-spin mr-2" /> Loading supplier profile...
        </div>
    );

    if (error) return (
        <div className="p-6 max-w-4xl mx-auto">
            <button onClick={() => router.back()} className="flex items-center gap-2 text-navy-400 hover:text-white mb-4">
                <ArrowLeft className="h-5 w-5" /> Back
            </button>
            <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-6 text-center">
                <AlertTriangle className="h-8 w-8 text-red-400 mx-auto mb-2" />
                <p className="text-red-400">{error}</p>
            </div>
        </div>
    );

    const supplier = data?.supplier || {};
    const reliability = data?.reliability || {};
    const overallScore = reliability.overall_score ?? reliability.score ?? 0;

    return (
        <div className="p-6 max-w-5xl mx-auto space-y-6">
            <div className="flex items-center gap-4">
                <button onClick={() => router.back()} className="text-navy-400 hover:text-white">
                    <ArrowLeft className="h-6 w-6" />
                </button>
                <div className="flex-1">
                    <h1 className="text-2xl font-bold text-white flex items-center gap-2">
                        <Building2 className="h-6 w-6 text-amber-400" /> {supplier.name || "Supplier"}
                    </h1>
                    <div className="flex items-center gap-3 mt-1">
                        {supplier.country && (
                            <span className="text-sm text-navy-400 flex items-center gap-1">
                                <MapPin className="h-3 w-3" /> {supplier.country}
                            </span>
                        )}
                    </div>
                </div>
            </div>

            {/* Overall Score */}
            <div className={`border rounded-xl p-6 text-center ${getScoreBg(overallScore)}`}>
                <p className="text-navy-400 text-sm font-medium mb-2">Overall Reliability Score</p>
                <p className={`text-5xl font-bold ${getScoreColor(overallScore)}`}>{overallScore}<span className="text-2xl">%</span></p>
                <div className="flex items-center justify-center gap-1 mt-2">
                    {[1,2,3,4,5].map(s => (
                        <Star key={s} className={`h-5 w-5 ${s <= Math.round(overallScore / 20) ? "text-[#f5a623] fill-[#f5a623]" : "text-navy-600"}`} />
                    ))}
                </div>
            </div>

            {/* Metric Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-[#12253f]/80 border border-[#1e3a5f] rounded-xl p-4 text-center">
                    <Clock className="h-5 w-5 text-blue-400 mx-auto mb-2" />
                    <p className="text-xs text-navy-400 mb-1">On-Time Rate</p>
                    <p className="text-xl font-bold text-white">{reliability.on_time_rate ?? "—"}%</p>
                </div>
                <div className="bg-[#12253f]/80 border border-[#1e3a5f] rounded-xl p-4 text-center">
                    <ShieldCheck className="h-5 w-5 text-emerald-400 mx-auto mb-2" />
                    <p className="text-xs text-navy-400 mb-1">Quality Score</p>
                    <p className="text-xl font-bold text-white">{reliability.quality_score ?? "—"}%</p>
                </div>
                <div className="bg-[#12253f]/80 border border-[#1e3a5f] rounded-xl p-4 text-center">
                    <Package className="h-5 w-5 text-purple-400 mx-auto mb-2" />
                    <p className="text-xs text-navy-400 mb-1">MOQ Honesty</p>
                    <p className="text-xl font-bold text-white">{reliability.moq_honesty ?? "—"}%</p>
                </div>
                <div className="bg-[#12253f]/80 border border-[#1e3a5f] rounded-xl p-4 text-center">
                    <TrendingUp className="h-5 w-5 text-[#f5a623] mx-auto mb-2" />
                    <p className="text-xs text-navy-400 mb-1">Capacity Index</p>
                    <p className="text-xl font-bold text-white">{supplier.capacity_index ?? "—"}</p>
                </div>
            </div>

            {/* Issues History */}
            {reliability.issues && reliability.issues.length > 0 && (
                <div className="bg-[#12253f]/80 border border-[#1e3a5f] rounded-xl overflow-hidden">
                    <div className="px-5 py-4 border-b border-[#1e3a5f]">
                        <h3 className="text-white font-bold flex items-center gap-2">
                            <BarChart3 className="h-4 w-4 text-red-400" /> Issue History
                        </h3>
                    </div>
                    <div className="divide-y divide-[#1e3a5f]">
                        {reliability.issues.map((issue: any, idx: number) => (
                            <div key={idx} className="px-5 py-3 flex items-center justify-between">
                                <div>
                                    <p className="text-white text-sm font-medium">{issue.issue_type}</p>
                                    {issue.description && <p className="text-xs text-navy-400 mt-0.5">{issue.description}</p>}
                                </div>
                                <span className={`text-xs px-2 py-1 rounded ${issue.severity >= 3 ? "bg-red-500/10 text-red-400" : issue.severity >= 2 ? "bg-amber-500/10 text-amber-400" : "bg-blue-500/10 text-blue-400"}`}>
                                    Severity {issue.severity}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
