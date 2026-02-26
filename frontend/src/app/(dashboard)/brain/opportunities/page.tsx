"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { TrendingUp, Loader2, Globe, DollarSign, Target, ArrowRight, RefreshCw, Zap, BarChart3, ShieldCheck } from "lucide-react";
import api from "@/lib/api";

interface Opportunity {
    id: string;
    product: string;
    buy_market: string;
    sell_market: string;
    buy_price: number;
    sell_price: number;
    margin_percent: number;
    confidence: number;
    volume_available?: string;
    risk_level: string;
    expires_at?: string;
    status: string;
}

export default function OpportunitiesPage() {
    const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);

    const fetchOpportunities = async (isRefresh = false) => {
        if (isRefresh) setRefreshing(true);
        try {
            const res = await api.get("/brain/opportunities");
            setOpportunities(Array.isArray(res.data) ? res.data : []);
        } catch { setOpportunities([]); }
        finally { setLoading(false); setRefreshing(false); }
    };

    useEffect(() => { fetchOpportunities(); }, []);

    const riskColor = (level: string) => {
        switch (level?.toLowerCase()) {
            case "low": return "bg-emerald-500/20 text-emerald-400";
            case "high": return "bg-rose-500/20 text-rose-400";
            default: return "bg-amber-500/20 text-amber-400";
        }
    };

    const highMargin = opportunities.filter(o => o.margin_percent >= 15).length;
    const avgConfidence = opportunities.length > 0 ? Math.round(opportunities.reduce((s, o) => s + (o.confidence || 0), 0) / opportunities.length) : 0;

    return (
        <div className="space-y-6 p-4 md:p-8 max-w-[1400px] mx-auto">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold flex items-center gap-2 text-white">
                        <Zap className="h-6 w-6 text-emerald-400" /> Arbitrage Opportunities
                    </h1>
                    <p className="text-white/50 text-sm">AI-identified buy/sell opportunities across markets</p>
                </div>
                <Button onClick={() => fetchOpportunities(true)} disabled={refreshing} variant="outline" className="border-white/20 text-white">
                    <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? "animate-spin" : ""}`} /> Refresh
                </Button>
            </div>

            {/* KPIs */}
            <div className="grid gap-4 sm:grid-cols-4">
                <Card className="bg-[#0e1e33] border-[#1e3a5f]"><CardContent className="p-4 flex items-center justify-between">
                    <div><p className="text-white/50 text-xs uppercase">Active Opportunities</p><p className="text-xl font-bold text-white mt-1">{opportunities.length}</p></div>
                    <Target className="h-7 w-7 text-blue-400/40" />
                </CardContent></Card>
                <Card className="bg-[#0e1e33] border-[#1e3a5f]"><CardContent className="p-4 flex items-center justify-between">
                    <div><p className="text-white/50 text-xs uppercase">High Margin (15%+)</p><p className="text-xl font-bold text-emerald-400 mt-1">{highMargin}</p></div>
                    <TrendingUp className="h-7 w-7 text-emerald-400/40" />
                </CardContent></Card>
                <Card className="bg-[#0e1e33] border-[#1e3a5f]"><CardContent className="p-4 flex items-center justify-between">
                    <div><p className="text-white/50 text-xs uppercase">Avg Confidence</p><p className="text-xl font-bold text-[#f5a623] mt-1">{avgConfidence}%</p></div>
                    <ShieldCheck className="h-7 w-7 text-[#f5a623]/40" />
                </CardContent></Card>
                <Card className="bg-[#0e1e33] border-[#1e3a5f]"><CardContent className="p-4 flex items-center justify-between">
                    <div><p className="text-white/50 text-xs uppercase">Markets</p><p className="text-xl font-bold text-blue-400 mt-1">{new Set([...opportunities.map(o => o.buy_market), ...opportunities.map(o => o.sell_market)]).size}</p></div>
                    <Globe className="h-7 w-7 text-blue-400/40" />
                </CardContent></Card>
            </div>

            {/* Opportunities */}
            {loading ? (
                <div className="flex justify-center py-16"><Loader2 className="h-6 w-6 animate-spin text-white/40" /></div>
            ) : opportunities.length === 0 ? (
                <Card className="bg-[#0e1e33] border-[#1e3a5f]"><CardContent className="py-16 text-center">
                    <Zap className="h-12 w-12 mx-auto mb-3 text-white/10" />
                    <p className="text-white/40 text-sm">No active arbitrage opportunities detected</p>
                    <p className="text-white/30 text-xs mt-1">The AI engine continuously scans for profitable trade gaps</p>
                </CardContent></Card>
            ) : (
                <div className="grid gap-4 sm:grid-cols-2">
                    {opportunities.map(opp => (
                        <Card key={opp.id} className="bg-[#0e1e33] border-[#1e3a5f] hover:border-emerald-400/30 transition-colors">
                            <CardContent className="p-5 space-y-4">
                                <div className="flex items-start justify-between">
                                    <div>
                                        <h3 className="text-white font-bold text-lg">{opp.product}</h3>
                                        <div className="flex items-center gap-2 mt-1 text-white/50 text-xs">
                                            <span className="text-blue-400">{opp.buy_market}</span>
                                            <ArrowRight className="h-3 w-3" />
                                            <span className="text-emerald-400">{opp.sell_market}</span>
                                        </div>
                                    </div>
                                    <Badge className={`text-[10px] ${riskColor(opp.risk_level)}`}>{opp.risk_level} Risk</Badge>
                                </div>
                                <div className="grid grid-cols-3 gap-3">
                                    <div className="p-3 bg-blue-500/10 rounded-lg text-center">
                                        <p className="text-white/40 text-[10px] uppercase">Buy</p>
                                        <p className="text-blue-400 font-bold text-lg">${opp.buy_price?.toLocaleString()}</p>
                                    </div>
                                    <div className="p-3 bg-emerald-500/10 rounded-lg text-center">
                                        <p className="text-white/40 text-[10px] uppercase">Sell</p>
                                        <p className="text-emerald-400 font-bold text-lg">${opp.sell_price?.toLocaleString()}</p>
                                    </div>
                                    <div className="p-3 bg-[#f5a623]/10 rounded-lg text-center">
                                        <p className="text-white/40 text-[10px] uppercase">Margin</p>
                                        <p className="text-[#f5a623] font-bold text-lg">{opp.margin_percent?.toFixed(1)}%</p>
                                    </div>
                                </div>
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-4">
                                        <div className="flex items-center gap-1">
                                            <ShieldCheck className="h-3.5 w-3.5 text-white/30" />
                                            <span className="text-white/50 text-xs">Confidence: <span className="text-white font-medium">{opp.confidence}%</span></span>
                                        </div>
                                        {opp.volume_available && (
                                            <div className="flex items-center gap-1">
                                                <BarChart3 className="h-3.5 w-3.5 text-white/30" />
                                                <span className="text-white/50 text-xs">Vol: {opp.volume_available}</span>
                                            </div>
                                        )}
                                    </div>
                                    {opp.expires_at && <span className="text-white/30 text-xs">Expires: {new Date(opp.expires_at).toLocaleDateString()}</span>}
                                </div>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            )}
        </div>
    );
}
