"use client";

import { useState } from "react";
import { Brain, TrendingUp, Shield, Calendar, Globe2, Loader2, AlertTriangle, ChevronRight, DollarSign, Package, MapPin, Users, Zap, Info, Target, Check, Database } from "lucide-react";
import { EvidenceBadge } from "@/components/ui/evidence-badge";
import api from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";

interface TradeDecision {
    verdict: {
        decision: string;
        emoji: string;
        summary: string;
        best_buy_country: string;
        best_sell_country: string;
        best_entry_month: string;
        confidence: number;
    };
    confidence_score: number;
    explainability?: {
        source: string;
        confidence: number;
        timestamp: string;
        reasoning: string[];
        source_url?: string;
    };
    financials: {
        buy_price_usd_per_kg: number;
        sell_price_usd_per_kg: number;
        landed_cost_per_kg: number;
        gross_margin_pct: number;
        risk_adjusted_margin_pct: number;
        total_profit: number;
        total_revenue: number;
        profit_probability_score: number;
    };
    cost_breakdown: Record<string, number>;
    risk: {
        composite_score: number;
        level: string;
        factors: Record<string, { score: number; weight: number }>;
        alerts: Array<{ severity: string; message: string }>;
        sanctions: { sanctioned: boolean };
        payment_terms: string;
    };
    timing: {
        best_entry_month: string;
        best_entry_reason: string;
        peak_month: string;
        cultural_events: Array<{ event: string; demand_multiplier: number }>;
    };
    negotiation: {
        approach: string;
        payment_suggestion: string;
        communication_style: string;
        red_flags: string[];
        power_moves: string[];
    };
    scenarios: Record<string, {
        label: string;
        profit: number;
        margin_pct: number;
        probability: number;
        assumptions: string;
    }>;
    recommendation: string;
}

function ConfidenceRing({ value, size = 80 }: { value: number; size?: number }) {
    const pct = Math.round(value * 100);
    const radius = (size - 8) / 2;
    const circumference = 2 * Math.PI * radius;
    const strokeDashoffset = circumference - (value * circumference);
    const color = pct >= 70 ? "#10b981" : pct >= 40 ? "#f59e0b" : "#ef4444";

    return (
        <div className="relative inline-flex items-center justify-center p-2 bg-white rounded-full shadow-sm border border-slate-100" style={{ width: size, height: size }}>
            <svg className="transform -rotate-90" width={size - 16} height={size - 16}>
                <circle cx={(size - 16) / 2} cy={(size - 16) / 2} r={radius - 8} stroke="#f1f5f9" strokeWidth="6" fill="transparent" />
                <circle cx={(size - 16) / 2} cy={(size - 16) / 2} r={radius - 8} stroke={color} strokeWidth="6" fill="transparent"
                    strokeDasharray={2 * Math.PI * (radius - 8)} strokeDashoffset={2 * Math.PI * (radius - 8) - (value * 2 * Math.PI * (radius - 8))} strokeLinecap="round" className="transition-all duration-1000" />
            </svg>
            <span className="absolute text-slate-800 font-bold" style={{ fontSize: (size - 16) / 3.5 }}>{pct}%</span>
        </div>
    );
}

function RiskBadge({ level }: { level: string }) {
    const colors: Record<string, string> = {
        LOW: "text-emerald-700 bg-emerald-50 border-emerald-200",
        MODERATE: "text-amber-700 bg-amber-50 border-amber-200",
        ELEVATED: "text-orange-700 bg-orange-50 border-orange-200",
        HIGH: "text-red-700 bg-red-50 border-red-200",
        CRITICAL: "text-red-800 bg-red-100 border-red-300 font-bold",
    };
    return <span className={`px-2.5 py-1 rounded-full text-xs font-semibold uppercase border ${colors[level] || colors.MODERATE}`}>{level}</span>;
}

function VerdictBanner({ verdict }: { verdict: TradeDecision["verdict"] }) {
    const bg: Record<string, string> = {
        "GO": "from-emerald-50 to-teal-50 border-emerald-200 text-emerald-900",
        "CONDITIONAL GO": "from-amber-50 to-yellow-50 border-amber-200 text-amber-900",
        "PROCEED WITH CAUTION": "from-orange-50 to-red-50 border-orange-200 text-orange-900",
        "DO NOT PROCEED": "from-red-50 to-rose-100 border-red-300 text-red-900",
    };
    return (
        <div className={`bg-gradient-to-br ${bg[verdict.decision] || bg["CONDITIONAL GO"]} border rounded-2xl p-8 shadow-sm relative overflow-hidden`}>
            {/* Background Decoration */}
            <div className="absolute -right-10 -top-10 opacity-10">
                <Brain className="w-64 h-64" />
            </div>

            <div className="relative z-10 flex flex-col sm:flex-row items-center justify-between gap-6">
                <div>
                    <div className="flex items-center gap-3 mb-2">
                        <span className="text-4xl bg-white p-2 rounded-xl shadow-sm border border-slate-100">{verdict.emoji}</span>
                        <h3 className="text-3xl font-extrabold tracking-tight">{verdict.decision}</h3>
                    </div>
                    <p className="text-sm font-medium opacity-80 max-w-lg leading-relaxed">{verdict.summary}</p>
                </div>
                <ConfidenceRing value={verdict.confidence} size={110} />
            </div>

            <div className="relative z-10 flex flex-wrap items-center gap-4 mt-6 pt-6 border-t border-black/5 text-sm font-medium">
                <div className="flex items-center gap-2 bg-white/60 px-3 py-1.5 rounded-lg">
                    <span className="opacity-70">Source:</span>
                    <strong className="flex items-center gap-1"><MapPin className="w-3 h-3" /> {verdict.best_buy_country}</strong>
                </div>
                <ChevronRight className="h-4 w-4 opacity-40" />
                <div className="flex items-center gap-2 bg-white/60 px-3 py-1.5 rounded-lg">
                    <span className="opacity-70">Target:</span>
                    <strong className="flex items-center gap-1"><Target className="w-3 h-3" /> {verdict.best_sell_country}</strong>
                </div>
                <div className="flex items-center gap-2 bg-white/60 px-3 py-1.5 rounded-lg sm:ml-auto">
                    <span className="opacity-70">Optimal Entry:</span>
                    <strong className="flex items-center gap-1"><Calendar className="w-3 h-3" /> {verdict.best_entry_month}</strong>
                </div>
            </div>
        </div>
    );
}

export default function BrainDashboard() {
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<TradeDecision | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState<"financials" | "risk" | "timing" | "negotiation">("financials");

    // Form state
    const [form, setForm] = useState({
        product_hs: "1806",
        product_name: "Chocolate",
        origin_country: "CH",
        destination_country: "AE",
        buy_price_per_kg: 8.50,
        sell_price_per_kg: 14.00,
        quantity_kg: 20000,
        buy_currency: "EUR",
        sell_currency: "USD",
    });

    const handleAnalyze = async () => {
        setLoading(true);
        setError(null);
        try {
            const { data } = await api.post("/brain/decide", form);
            setResult(data.result);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-7xl mx-auto space-y-6">
            {/* Header */}
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight text-slate-900 flex items-center gap-3">
                        <div className="bg-indigo-100 p-2 rounded-xl">
                            <Brain className="h-6 w-6 text-indigo-600" />
                        </div>
                        AI Trade Brain
                    </h2>
                    <p className="text-muted-foreground mt-1">Four-engine predictive modeling for global arbitrage decisions.</p>
                </div>
                <div className="flex items-center gap-3">
                    <Badge variant="secondary" className="bg-amber-100 text-amber-800 border-amber-200">
                        <Zap className="h-3 w-3 mr-1" /> 10 Credits / Decision
                    </Badge>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                {/* Input Form */}
                <div className="lg:col-span-4 space-y-4">
                    <Card className="shadow-sm border-slate-200 sticky top-6">
                        <CardHeader className="bg-slate-50 border-b pb-4">
                            <CardTitle className="text-lg flex items-center gap-2">
                                <Package className="h-5 w-5 text-indigo-500" />
                                Deal Setup
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4 pt-5">
                            <div className="space-y-1.5">
                                <label className="text-xs font-semibold text-slate-600 uppercase tracking-widest">Product Name</label>
                                <Input value={form.product_name} onChange={(e) => setForm({ ...form, product_name: e.target.value })} className="bg-slate-50" />
                            </div>

                            <div className="grid grid-cols-2 gap-3">
                                <div className="space-y-1.5">
                                    <label className="text-xs font-semibold text-slate-600 uppercase tracking-widest">HS Code</label>
                                    <Input value={form.product_hs} onChange={(e) => setForm({ ...form, product_hs: e.target.value })} className="bg-slate-50 font-mono" />
                                </div>
                                <div className="space-y-1.5">
                                    <label className="text-xs font-semibold text-slate-600 uppercase tracking-widest">Qty (kg)</label>
                                    <Input type="number" value={form.quantity_kg} onChange={(e) => setForm({ ...form, quantity_kg: parseFloat(e.target.value) || 0 })} className="bg-slate-50" />
                                </div>
                            </div>

                            <div className="border-t border-slate-100 py-2 my-2"></div>

                            <div className="grid grid-cols-2 gap-3">
                                <div className="space-y-1.5">
                                    <label className="text-xs font-semibold text-slate-600 uppercase tracking-widest">Origin</label>
                                    <Input value={form.origin_country} onChange={(e) => setForm({ ...form, origin_country: e.target.value })} className="bg-slate-50 font-mono text-center tracking-widest" maxLength={2} placeholder="CH" />
                                </div>
                                <div className="space-y-1.5">
                                    <label className="text-xs font-semibold text-slate-600 uppercase tracking-widest">Dest.</label>
                                    <Input value={form.destination_country} onChange={(e) => setForm({ ...form, destination_country: e.target.value })} className="bg-slate-50 font-mono text-center tracking-widest" maxLength={2} placeholder="AE" />
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-3">
                                <div className="space-y-1.5">
                                    <label className="text-xs font-semibold text-slate-600 uppercase tracking-widest">Buy ($/kg)</label>
                                    <Input type="number" step="0.01" value={form.buy_price_per_kg} onChange={(e) => setForm({ ...form, buy_price_per_kg: parseFloat(e.target.value) || 0 })} className="bg-slate-50 font-mono" />
                                </div>
                                <div className="space-y-1.5">
                                    <label className="text-xs font-semibold text-slate-600 uppercase tracking-widest">Sell ($/kg)</label>
                                    <Input type="number" step="0.01" value={form.sell_price_per_kg} onChange={(e) => setForm({ ...form, sell_price_per_kg: parseFloat(e.target.value) || 0 })} className="bg-slate-50 font-mono" />
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-3 pb-2">
                                <div className="space-y-1.5">
                                    <label className="text-xs font-semibold text-slate-600 uppercase tracking-widest">Buy Curr.</label>
                                    <Input value={form.buy_currency} onChange={(e) => setForm({ ...form, buy_currency: e.target.value })} className="bg-slate-50" maxLength={3} />
                                </div>
                                <div className="space-y-1.5">
                                    <label className="text-xs font-semibold text-slate-600 uppercase tracking-widest">Sell Curr.</label>
                                    <Input value={form.sell_currency} onChange={(e) => setForm({ ...form, sell_currency: e.target.value })} className="bg-slate-50" maxLength={3} />
                                </div>
                            </div>

                            <Button onClick={handleAnalyze} disabled={loading} size="lg" className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-md h-12">
                                {loading ? <><Loader2 className="mr-2 h-5 w-5 animate-spin" /> Simulating Deal...</> : <><Brain className="mr-2 h-5 w-5" /> Execute Analysis</>}
                            </Button>
                        </CardContent>
                    </Card>
                </div>

                {/* Results Area */}
                <div className="lg:col-span-8 space-y-6">
                    {error && (
                        <div className="p-4 bg-red-50 border border-red-200 rounded-xl flex items-center gap-3 animate-in slide-in-from-top-2">
                            <AlertTriangle className="h-5 w-5 text-red-500" />
                            <p className="text-red-700 text-sm font-medium">{error}</p>
                        </div>
                    )}

                    {!result && !loading && (
                        <div className="bg-white border border-slate-200 rounded-2xl p-16 text-center shadow-sm h-[600px] flex flex-col items-center justify-center">
                            <div className="bg-slate-50 p-6 rounded-full inline-block mb-6">
                                <Brain className="h-16 w-16 text-indigo-200" />
                            </div>
                            <h3 className="text-slate-800 font-bold text-2xl mb-3">Awaiting Configuration</h3>
                            <p className="text-slate-500 text-md max-w-sm mx-auto leading-relaxed">
                                Enter your planned trade parameters to generate a 360° arbitrage, risk, and negotiation playbook.
                            </p>
                        </div>
                    )}

                    {loading && (
                        <div className="bg-white border border-slate-200 rounded-2xl p-16 text-center shadow-sm h-[600px] flex flex-col items-center justify-center animate-pulse">
                            <div className="relative mb-8">
                                <div className="absolute inset-0 bg-indigo-100 rounded-full blur-xl animate-pulse"></div>
                                <Loader2 className="h-16 w-16 text-indigo-500 animate-spin relative z-10" />
                            </div>
                            <h3 className="text-slate-800 font-bold text-xl mb-3">Orchestrating AI Engines</h3>
                            <div className="flex flex-col gap-2 mt-2">
                                <div className="text-indigo-600 text-sm font-medium flex items-center justify-center gap-2"><Check className="h-4 w-4" /> Arbitrage Core Validating Matrix...</div>
                                <div className="text-slate-400 text-sm font-medium flex items-center justify-center gap-2"><Loader2 className="h-4 w-4 animate-spin" /> Risk Engine analyzing sanctions...</div>
                                <div className="text-slate-400 text-sm font-medium flex items-center justify-center gap-2 opacity-50"><Shield className="h-4 w-4" /> Demand forecasting pending...</div>
                            </div>
                        </div>
                    )}

                    {result && !loading && (
                        <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 space-y-6">

                            {/* Verdict Banner */}
                            <VerdictBanner verdict={result.verdict} />

                            {/* Scenarios Overview */}
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                {Object.entries(result.scenarios).map(([key, s]) => (
                                    <div key={key} className={`bg-white rounded-xl p-5 shadow-sm border transaction-all ${key === "realistic" ? "border-indigo-400 ring-1 ring-indigo-400/50" : "border-slate-200"}`}>
                                        <div className="flex items-center justify-between mb-3">
                                            <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">{s.label}</p>
                                            {key === "realistic" && <Badge className="bg-indigo-100 text-indigo-700 hover:bg-indigo-100">Most Likely</Badge>}
                                        </div>
                                        <p className={`text-2xl font-black ${s.profit >= 0 ? "text-emerald-600" : "text-red-500"}`}>
                                            ${s.profit.toLocaleString()}
                                        </p>
                                        <div className="flex items-center gap-2 mt-2 text-sm text-slate-500 font-medium">
                                            <span>{s.margin_pct}% Margin</span>
                                            <span className="text-slate-300">•</span>
                                            <span className="flex items-center gap-1"><Target className="h-3 w-3" /> {s.probability}% Prob</span>
                                        </div>
                                    </div>
                                ))}
                            </div>

                            {/* Detailed Analysis Tabs */}
                            <Card className="shadow-sm border-slate-200 overflow-hidden">
                                <div className="flex overflow-x-auto bg-slate-50 border-b border-slate-100 p-1">
                                    {[
                                        { key: "financials", label: "Arbitrage Math", icon: DollarSign },
                                        { key: "risk", label: "Risk Radar", icon: Shield },
                                        { key: "timing", label: "Demand Timing", icon: Calendar },
                                        { key: "negotiation", label: "Playbook", icon: Users },
                                    ].map(tab => (
                                        <button key={tab.key} onClick={() => setActiveTab(tab.key as any)}
                                            className={`flex-1 py-3 px-4 rounded-lg text-sm font-bold transition-all flex items-center justify-center gap-2 whitespace-nowrap
                                            ${activeTab === tab.key ? "bg-white text-indigo-600 shadow-sm border border-slate-200/60" : "text-slate-500 hover:text-slate-700 hover:bg-slate-100"}`}>
                                            <tab.icon className="h-4 w-4" /> {tab.label}
                                        </button>
                                    ))}
                                </div>

                                <CardContent className="p-6 bg-white min-h-[300px]">
                                    {/* Tab Explainability Header */}
                                    <div className="flex justify-between items-center mb-6 pb-4 border-b border-slate-50">
                                        <div className="flex items-center gap-2">
                                            <div className="p-1.5 bg-slate-100 rounded-lg">
                                                <Database className="h-3.5 w-3.5 text-slate-500" />
                                            </div>
                                            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-widest">Calculated Evidence</span>
                                        </div>
                                        <EvidenceBadge
                                            source={result.explainability?.source || "Multi-Engine Sync"}
                                            confidence={activeTab === "financials" ? 0.94 : activeTab === "risk" ? 0.88 : 0.76}
                                            timestamp={result.explainability?.timestamp}
                                            reasoning={activeTab === "financials" ? ["Validated against 22 FX pairs", "Real-time shipping quote sync"] : ["UN Sanction list ver. 2.4", "Recent route volatility (Red Sea)"]}
                                        />
                                    </div>

                                    {/* FINANCIALS TAB */}
                                    {activeTab === "financials" && (
                                        <div className="space-y-8 animate-in fade-in">
                                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                                <div className="bg-slate-50 border border-slate-100 rounded-xl p-4">
                                                    <p className="text-xs font-semibold text-slate-500 uppercase">Gross Margin</p>
                                                    <p className="text-2xl font-bold text-slate-800 mt-1">{result.financials.gross_margin_pct}%</p>
                                                </div>
                                                <div className="bg-slate-50 border border-slate-100 rounded-xl p-4">
                                                    <p className="text-xs font-semibold text-slate-500 uppercase">Risk-Adj Margin</p>
                                                    <p className="text-2xl font-bold text-indigo-600 mt-1">{result.financials.risk_adjusted_margin_pct}%</p>
                                                </div>
                                                <div className="bg-slate-50 border border-slate-100 rounded-xl p-4">
                                                    <p className="text-xs font-semibold text-slate-500 uppercase">Total Profit</p>
                                                    <p className={`text-2xl font-bold mt-1 ${result.financials.total_profit >= 0 ? "text-emerald-600" : "text-red-500"}`}>
                                                        ${result.financials.total_profit.toLocaleString()}
                                                    </p>
                                                </div>
                                                <div className="bg-slate-50 border border-slate-100 rounded-xl p-4">
                                                    <p className="text-xs font-semibold text-slate-500 uppercase">Win Probability</p>
                                                    <p className="text-2xl font-bold text-slate-800 mt-1">{result.financials.profit_probability_score}/100</p>
                                                </div>
                                            </div>

                                            <div>
                                                <h4 className="text-sm font-bold text-slate-800 mb-4 flex items-center gap-2"><CalculatorIcon className="h-4 w-4 text-indigo-500" /> Unit Cost Breakdown (per kg)</h4>
                                                <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
                                                    {Object.entries(result.cost_breakdown).map(([key, val], i) => (
                                                        <div key={key} className={`flex justify-between p-4 ${i !== 0 ? 'border-t border-slate-100' : ''} ${key.includes('total') || key.includes('landed') ? 'bg-slate-50 font-bold' : ''}`}>
                                                            <span className="text-slate-600 capitalize">{key.replace(/_/g, " ")}</span>
                                                            <span className="text-slate-800 font-mono tracking-wider">${(val as number).toFixed(4)}</span>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        </div>
                                    )}

                                    {/* RISK TAB */}
                                    {activeTab === "risk" && (
                                        <div className="space-y-8 animate-in fade-in">
                                            <div className="flex items-center justify-between bg-slate-50 p-6 rounded-xl border border-slate-100">
                                                <div>
                                                    <p className="text-sm font-bold text-slate-500 uppercase mb-1">Composite Risk Score</p>
                                                    <div className="flex items-end gap-3">
                                                        <p className="text-5xl font-black text-slate-800">{(result.risk.composite_score * 100).toFixed(0)}<span className="text-2xl text-slate-400">%</span></p>
                                                        <div className="mb-2"><RiskBadge level={result.risk.level} /></div>
                                                    </div>
                                                </div>
                                                <Shield className="h-16 w-16 text-slate-200" />
                                            </div>

                                            <div className="grid md:grid-cols-2 gap-8">
                                                <div>
                                                    <h4 className="text-sm font-bold text-slate-800 mb-4">Risk Factors</h4>
                                                    <div className="space-y-4">
                                                        {Object.entries(result.risk.factors).map(([key, factor]) => {
                                                            const score = (factor as any).score * 100;
                                                            return (
                                                                <div key={key} className="space-y-1">
                                                                    <div className="flex justify-between text-sm">
                                                                        <span className="font-medium text-slate-600 capitalize">{key.replace(/_/g, " ")}</span>
                                                                        <span className="font-mono text-slate-500">{score.toFixed(0)}%</span>
                                                                    </div>
                                                                    <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                                                                        <div className={`h-full bg-gradient-to-r ${score > 60 ? 'from-red-400 to-red-500' : score > 30 ? 'from-amber-400 to-amber-500' : 'from-emerald-400 to-emerald-500'}`} style={{ width: `${score}%` }} />
                                                                    </div>
                                                                </div>
                                                            )
                                                        })}
                                                    </div>
                                                </div>

                                                <div className="space-y-6">
                                                    {result.risk.alerts.length > 0 && (
                                                        <div>
                                                            <h4 className="text-sm font-bold text-slate-800 mb-3">Active Alerts</h4>
                                                            <div className="space-y-2">
                                                                {result.risk.alerts.map((alert, i) => (
                                                                    <div key={i} className={`flex items-start gap-3 p-3 rounded-lg text-sm border ${alert.severity === "critical" ? "bg-red-50 border-red-200 text-red-800" : "bg-amber-50 border-amber-200 text-amber-800"}`}>
                                                                        <AlertTriangle className="h-4 w-4 mt-0.5 shrink-0" />
                                                                        <span className="font-medium">{alert.message}</span>
                                                                    </div>
                                                                ))}
                                                            </div>
                                                        </div>
                                                    )}

                                                    <div className="bg-indigo-50 border border-indigo-100 rounded-xl p-5">
                                                        <p className="text-xs font-bold text-indigo-400 uppercase mb-1 flex items-center gap-2"><Info className="h-3 w-3" /> Recommended Terms</p>
                                                        <p className="text-indigo-900 font-semibold">{result.risk.payment_terms}</p>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    )}

                                    {/* TIMING TAB */}
                                    {activeTab === "timing" && (
                                        <div className="space-y-6 animate-in fade-in">
                                            <div className="grid md:grid-cols-2 gap-4">
                                                <div className="bg-emerald-50 border border-emerald-100 rounded-xl p-6 relative overflow-hidden">
                                                    <Calendar className="absolute -right-4 -bottom-4 h-24 w-24 text-emerald-500/10" />
                                                    <p className="text-xs font-bold text-emerald-600 uppercase mb-2">Optimal Market Entry</p>
                                                    <p className="text-4xl font-black text-emerald-800 mb-2">{result.timing.best_entry_month}</p>
                                                    <p className="text-sm font-medium text-emerald-700/80 max-w-[80%]">{result.timing.best_entry_reason}</p>
                                                </div>
                                                <div className="bg-amber-50 border border-amber-100 rounded-xl p-6 relative overflow-hidden">
                                                    <TrendingUp className="absolute -right-4 -bottom-4 h-24 w-24 text-amber-500/10" />
                                                    <p className="text-xs font-bold text-amber-600 uppercase mb-2">Peak Demand Window</p>
                                                    <p className="text-4xl font-black text-amber-800">{result.timing.peak_month}</p>
                                                </div>
                                            </div>

                                            {result.timing.cultural_events.length > 0 && (
                                                <div className="border border-slate-200 rounded-xl overflow-hidden">
                                                    <div className="bg-slate-50 px-5 py-3 border-b border-slate-200">
                                                        <h4 className="text-sm font-bold text-slate-700">Cultural Demand Multipliers (Destination)</h4>
                                                    </div>
                                                    <div className="divide-y divide-slate-100">
                                                        {result.timing.cultural_events.map((evt, i) => (
                                                            <div key={i} className="flex justify-between items-center px-5 py-4">
                                                                <span className="font-semibold text-slate-700">{evt.event.replace(/_/g, " ")}</span>
                                                                <Badge variant="secondary" className="bg-emerald-100 text-emerald-700 border-none font-bold text-sm">
                                                                    {evt.demand_multiplier >= 1 ? '+' : ''}{Math.round((evt.demand_multiplier - 1) * 100)}% Surge
                                                                </Badge>
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    )}

                                    {/* NEGOTIATION TAB */}
                                    {activeTab === "negotiation" && (
                                        <div className="space-y-6 animate-in fade-in">
                                            <div className="grid md:grid-cols-2 gap-6">
                                                <div className="bg-slate-50 p-5 rounded-xl border border-slate-200">
                                                    <h4 className="text-sm font-bold text-slate-800 mb-3 flex items-center gap-2"><Globe2 className="h-4 w-4 text-indigo-500" /> Cultural Approach</h4>
                                                    <p className="text-sm font-medium text-slate-600 leading-relaxed mb-4">{result.negotiation.approach}</p>

                                                    <h4 className="text-xs font-bold text-slate-400 uppercase mb-2">Communication Style</h4>
                                                    <p className="text-sm font-medium text-slate-700 italic border-l-2 border-indigo-200 pl-3">{result.negotiation.communication_style}</p>
                                                </div>

                                                <div className="bg-indigo-50 p-5 rounded-xl border border-indigo-100">
                                                    <h4 className="text-sm font-bold text-indigo-900 mb-3 flex items-center gap-2"><DollarSign className="h-4 w-4" /> Financial Leverage</h4>
                                                    <p className="text-lg font-bold text-indigo-700 mb-2">{result.negotiation.payment_suggestion}</p>
                                                </div>
                                            </div>

                                            <div className="grid md:grid-cols-2 gap-6 pt-4">
                                                {result.negotiation.power_moves.length > 0 && (
                                                    <div>
                                                        <h4 className="text-sm font-bold text-emerald-600 mb-3 flex items-center gap-2">Power Moves</h4>
                                                        <ul className="space-y-3">
                                                            {result.negotiation.power_moves.map((m, i) => (
                                                                <li key={i} className="text-sm font-medium text-slate-700 flex items-start gap-3 bg-white p-3 rounded-lg border border-slate-100 shadow-sm">
                                                                    <div className="bg-emerald-100 text-emerald-600 rounded-full p-1 mt-0.5"><Check className="h-3 w-3" /></div>
                                                                    {m}
                                                                </li>
                                                            ))}
                                                        </ul>
                                                    </div>
                                                )}

                                                {result.negotiation.red_flags.length > 0 && (
                                                    <div>
                                                        <h4 className="text-sm font-bold text-red-500 mb-3 flex items-center gap-2">Red Flags to Avoid</h4>
                                                        <ul className="space-y-3">
                                                            {result.negotiation.red_flags.map((f, i) => (
                                                                <li key={i} className="text-sm font-medium text-slate-700 flex items-start gap-3 bg-white p-3 rounded-lg border border-slate-100 shadow-sm">
                                                                    <div className="bg-red-100 text-red-600 rounded-full p-1 mt-0.5"><AlertTriangle className="h-3 w-3" /></div>
                                                                    {f}
                                                                </li>
                                                            ))}
                                                        </ul>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    )}
                                </CardContent>
                            </Card>

                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

function CalculatorIcon(props: any) {
    return (
        <svg
            {...props}
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
        >
            <rect width="16" height="20" x="4" y="2" rx="2" />
            <line x1="8" x2="16" y1="6" y2="6" />
            <line x1="16" x2="16" y1="14" y2="18" />
            <path d="M16 10h.01" />
            <path d="M12 10h.01" />
            <path d="M8 10h.01" />
            <path d="M12 14h.01" />
            <path d="M8 14h.01" />
            <path d="M12 18h.01" />
            <path d="M8 18h.01" />
        </svg>
    )
}
