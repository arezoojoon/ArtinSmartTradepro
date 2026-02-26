"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, BarChart3, Loader2, Trophy, Clock, DollarSign, FileText, AlertTriangle, CheckCircle2, TrendingDown } from "lucide-react";
import api from "@/lib/api";

export default function CompareRFQPage() {
    const params = useParams();
    const router = useRouter();
    const rfqId = params.id as string;

    const [loading, setLoading] = useState(true);
    const [comparison, setComparison] = useState<any>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (rfqId) fetchComparison();
    }, [rfqId]);

    const fetchComparison = async () => {
        setLoading(true);
        try {
            const { data } = await api.get(`/sourcing/rfqs/${rfqId}/compare`);
            setComparison(data);
        } catch (err: any) {
            setError(err?.message || "Failed to load comparison");
        } finally {
            setLoading(false);
        }
    };

    if (loading) return (
        <div className="flex items-center justify-center p-12 text-slate-400">
            <Loader2 className="h-6 w-6 animate-spin mr-2" /> Loading comparison...
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

    const quotes = comparison?.quotes || [];
    const bestQuote = comparison?.best_quote;

    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            <div className="flex items-center gap-4">
                <button onClick={() => router.back()} className="text-navy-400 hover:text-white">
                    <ArrowLeft className="h-6 w-6" />
                </button>
                <div>
                    <h1 className="text-2xl font-bold text-white flex items-center gap-2">
                        <BarChart3 className="h-6 w-6 text-violet-400" /> Quote Comparison
                    </h1>
                    <p className="text-sm text-navy-400">RFQ: {comparison?.rfq?.product_name || rfqId}</p>
                </div>
            </div>

            {/* RFQ Details */}
            {comparison?.rfq && (
                <div className="bg-[#12253f]/80 border border-[#1e3a5f] rounded-xl p-5">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                            <span className="text-navy-400">Product</span>
                            <p className="text-white font-medium">{comparison.rfq.product_name}</p>
                        </div>
                        <div>
                            <span className="text-navy-400">HS Code</span>
                            <p className="text-white font-medium">{comparison.rfq.hs_code || "—"}</p>
                        </div>
                        <div>
                            <span className="text-navy-400">Target Qty</span>
                            <p className="text-white font-medium">{comparison.rfq.target_qty?.toLocaleString()}</p>
                        </div>
                        <div>
                            <span className="text-navy-400">Incoterm</span>
                            <p className="text-white font-medium">{comparison.rfq.target_incoterm || "FOB"}</p>
                        </div>
                    </div>
                </div>
            )}

            {quotes.length === 0 ? (
                <div className="bg-[#0e1e33] border border-[#1e3a5f] rounded-xl p-12 text-center">
                    <FileText className="h-12 w-12 text-navy-600 mx-auto mb-3" />
                    <p className="text-navy-400 font-medium">No quotes received yet</p>
                    <p className="text-xs text-navy-500 mt-1">Quotes will appear here once suppliers respond to this RFQ.</p>
                </div>
            ) : (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {quotes.map((q: any, idx: number) => {
                        const isBest = bestQuote && q.id === bestQuote.id;
                        return (
                            <div key={q.id || idx} className={`bg-[#12253f]/80 border rounded-xl p-5 space-y-4 transition-all ${isBest ? "border-emerald-500/50 ring-1 ring-emerald-500/20" : "border-[#1e3a5f]"}`}>
                                {isBest && (
                                    <div className="flex items-center gap-2 text-emerald-400 text-xs font-bold uppercase">
                                        <Trophy className="h-4 w-4" /> Best Value
                                    </div>
                                )}
                                <div>
                                    <p className="text-white font-bold text-lg">{q.supplier_name || `Supplier ${idx + 1}`}</p>
                                    <p className="text-navy-400 text-xs">{q.incoterm || "FOB"}</p>
                                </div>
                                <div className="grid grid-cols-2 gap-3 text-sm">
                                    <div className="bg-[#0e1e33] rounded-lg p-3">
                                        <div className="flex items-center gap-1 text-navy-400 text-xs mb-1">
                                            <DollarSign className="h-3 w-3" /> Unit Price
                                        </div>
                                        <p className="text-white font-bold">${q.unit_price?.toFixed(2)} <span className="text-navy-400 font-normal text-xs">{q.currency || "USD"}</span></p>
                                    </div>
                                    <div className="bg-[#0e1e33] rounded-lg p-3">
                                        <div className="flex items-center gap-1 text-navy-400 text-xs mb-1">
                                            <Clock className="h-3 w-3" /> Lead Time
                                        </div>
                                        <p className="text-white font-bold">{q.lead_time_days} <span className="text-navy-400 font-normal text-xs">days</span></p>
                                    </div>
                                    <div className="bg-[#0e1e33] rounded-lg p-3">
                                        <div className="flex items-center gap-1 text-navy-400 text-xs mb-1">
                                            <TrendingDown className="h-3 w-3" /> MOQ
                                        </div>
                                        <p className="text-white font-bold">{q.moq?.toLocaleString() || "—"}</p>
                                    </div>
                                    <div className="bg-[#0e1e33] rounded-lg p-3">
                                        <div className="flex items-center gap-1 text-navy-400 text-xs mb-1">
                                            <FileText className="h-3 w-3" /> Payment
                                        </div>
                                        <p className="text-white font-bold text-xs">{q.payment_terms || "—"}</p>
                                    </div>
                                </div>
                                {q.reliability_score !== undefined && (
                                    <div className="flex items-center gap-2 text-sm">
                                        <CheckCircle2 className="h-4 w-4 text-blue-400" />
                                        <span className="text-navy-300">Reliability: <span className="text-white font-bold">{q.reliability_score}%</span></span>
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
