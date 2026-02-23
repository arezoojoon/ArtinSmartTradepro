"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Brain, ArrowRight, Loader2, AlertTriangle, TrendingUp } from "lucide-react";
import api from "@/lib/api";

interface Opportunity {
    id: string;
    title: string;
    description: string;
    type: string;
    estimated_profit: number;
    confidence_score: number;
    actions: any;
}

interface Signal {
    id: string;
    headline: string;
    summary: string;
    severity: "low" | "medium" | "high" | "critical";
    impact_area: string;
}

interface BrainFeedProps {
    mode: "buyer" | "seller" | "hybrid";
}

export default function BrainFeed({ mode }: BrainFeedProps) {
    const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
    const [signals, setSignals] = useState<Signal[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchFeed();
    }, []);

    const fetchFeed = async () => {
        try {
            const res = await api.get("/brain/feed");
            setOpportunities(res.data.opportunities);
            setSignals(res.data.signals);
        } catch (error) {
            console.error("Failed to fetch brain feed", error);
        } finally {
            setLoading(false);
        }
    };

    const triggerScan = async () => {
        setLoading(true);
        try {
            await api.post("/brain/scan");
            // Wait a bit for "scan" to finish (mock) then refetch
            setTimeout(fetchFeed, 2000);
        } catch (error) {
            console.error("Scan failed", error);
            setLoading(false);
        }
    };

    if (loading && opportunities.length === 0) {
        return (
            <div className="flex justify-center p-8">
                <Loader2 className="h-8 w-8 animate-spin text-[#f5a623]" />
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                    <Brain className="h-5 w-5 text-[#f5a623]" />
                    Proactive Intelligence
                </h2>
                <Button variant="outline" size="sm" onClick={triggerScan} className="border-gold-500 text-[#f5a623] hover:bg-gold-500/10">
                    {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : "Run AI Scan"}
                </Button>
            </div>

            {/* Signals Ticker */}
            {signals.length > 0 && (
                <div className="bg-navy-800/50 border border-navy-700 rounded-lg p-3 flex gap-4 overflow-x-auto">
                    {signals.map(sig => (
                        <div key={sig.id} className="min-w-[300px] flex items-start gap-2 bg-[#0e1e33] p-2 rounded border border-[#1e3a5f]">
                            <AlertTriangle className={`h-4 w-4 mt-1 ${sig.severity === 'critical' ? 'text-red-500' : 'text-yellow-500'}`} />
                            <div>
                                <p className="text-sm font-semibold text-gray-200">{sig.headline}</p>
                                <p className="text-xs text-gray-400 line-clamp-2">{sig.summary}</p>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Opportunities Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {opportunities.map(opp => (
                    <Card key={opp.id} className="bg-[#0e1e33] border-[#1e3a5f] hover:border-gold-500/30 transition-all">
                        <CardHeader className="pb-2">
                            <div className="flex justify-between items-start">
                                <Badge variant="outline" className="border-gold-500/50 text-[#f5a623] uppercase text-[10px]">
                                    {opp.type}
                                </Badge>
                                <span className={`text-xs font-bold ${opp.confidence_score > 0.8 ? 'text-green-400' : 'text-yellow-400'}`}>
                                    {Math.round(opp.confidence_score * 100)}% Confidence
                                </span>
                            </div>
                            <CardTitle className="text-lg text-white mt-2">{opp.title}</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <p className="text-sm text-gray-400 mb-4 h-10 line-clamp-2">{opp.description}</p>

                            <div className="flex justify-between items-center mb-4">
                                <div className="text-left">
                                    <p className="text-xs text-gray-500">Est. Profit</p>
                                    <p className="text-lg font-bold text-green-400">${opp.estimated_profit?.toLocaleString()}</p>
                                </div>
                                <TrendingUp className="h-8 w-8 text-navy-700" />
                            </div>

                            <Button className="w-full bg-navy-800 hover:bg-gold-600 hover:text-navy-900 border border-navy-700 text-gray-300">
                                View Details <ArrowRight className="ml-2 h-4 w-4" />
                            </Button>
                        </CardContent>
                    </Card>
                ))}
            </div>

            {opportunities.length === 0 && !loading && (
                <div className="text-center py-12 text-gray-500">
                    No active opportunities. Run a scan to find new deals.
                </div>
            )}
        </div>
    );
}
