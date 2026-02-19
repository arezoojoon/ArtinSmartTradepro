"use client";

import { useState } from "react";
import { Brain, TrendingUp, Shield, Calendar, Globe2, Loader2, AlertTriangle, ChevronRight, DollarSign, Package, MapPin, Users, Zap } from "lucide-react";
import { BASE_URL } from "@/lib/api";

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
        <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
            <svg className="transform -rotate-90" width={size} height={size}>
                <circle cx={size / 2} cy={size / 2} r={radius} stroke="#1e293b" strokeWidth="4" fill="transparent" />
                <circle cx={size / 2} cy={size / 2} r={radius} stroke={color} strokeWidth="4" fill="transparent"
                    strokeDasharray={circumference} strokeDashoffset={strokeDashoffset} strokeLinecap="round" className="transition-all duration-1000" />
            </svg>
            <span className="absolute text-white font-bold" style={{ fontSize: size / 4 }}>{pct}%</span>
        </div>
    );
}

function RiskBadge({ level }: { level: string }) {
    const colors: Record<string, string> = {
        LOW: "text-green-400 bg-green-400/10", MODERATE: "text-yellow-400 bg-yellow-400/10",
        ELEVATED: "text-orange-400 bg-orange-400/10", HIGH: "text-red-400 bg-red-400/10",
        CRITICAL: "text-red-500 bg-red-500/10",
    };
    return <span className={`px-2 py-0.5 rounded-full text-xs font-bold uppercase ${colors[level] || colors.MODERATE}`}>{level}</span>;
}

function VerdictBanner({ verdict }: { verdict: TradeDecision["verdict"] }) {
    const bg: Record<string, string> = {
        "GO": "from-green-500/20 to-emerald-600/20 border-green-500/30",
        "CONDITIONAL GO": "from-yellow-500/20 to-amber-600/20 border-yellow-500/30",
        "PROCEED WITH CAUTION": "from-orange-500/20 to-red-600/20 border-orange-500/30",
        "DO NOT PROCEED": "from-red-500/20 to-red-800/20 border-red-500/30",
    };
    return (
        <div className={`bg-gradient-to-r ${bg[verdict.decision] || bg["CONDITIONAL GO"]} border rounded-xl p-6`}>
            <div className="flex items-center justify-between">
                <div>
                    <p className="text-4xl mb-1">{verdict.emoji}</p>
                    <h3 className="text-2xl font-bold text-white">{verdict.decision}</h3>
                    <p className="text-navy-300 mt-1">{verdict.summary}</p>
                </div>
                <ConfidenceRing value={verdict.confidence} size={90} />
            </div>
            <div className="flex items-center gap-6 mt-4 text-sm text-navy-400">
                <span>Buy: <strong className="text-white">{verdict.best_buy_country}</strong></span>
                <ChevronRight className="h-4 w-4" />
                <span>Sell: <strong className="text-white">{verdict.best_sell_country}</strong></span>
                <span className="ml-auto">Best entry: <strong className="text-white">{verdict.best_entry_month}</strong></span>
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
            const token = localStorage.getItem("access_token");
            const res = await fetch(`${BASE_URL}/brain/decide`, {
                method: "POST",
                headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
                body: JSON.stringify(form),
            });
            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || "Analysis failed");
            }
            const data = await res.json();
            setResult(data.result);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="p-6 max-w-7xl mx-auto">
            {/* Header */}
            <div className="mb-8">
                <div className="flex items-center gap-3 mb-2">
                    <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center">
                        <Brain className="h-5 w-5 text-white" />
                    </div>
                    <div>
                        <h1 className="text-2xl font-bold text-white">AI Brain — Trade Intelligence</h1>
                        <p className="text-sm text-navy-400">One-click trade decisions powered by arbitrage, risk, demand & cultural engines</p>
                    </div>
                </div>
                <div className="flex items-center gap-4 mt-3 text-xs text-navy-500">
                    <span className="flex items-center gap-1"><Zap className="h-3 w-3" /> 10 credits/decision</span>
                    <span className="flex items-center gap-1"><Shield className="h-3 w-3" /> Deterministic math (no hallucination)</span>
                    <span className="flex items-center gap-1"><Brain className="h-3 w-3" /> 4 engines combined</span>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Input Form */}
                <div className="lg:col-span-1 space-y-4">
                    <div className="bg-navy-900 border border-navy-800 rounded-xl p-5">
                        <h3 className="text-white font-semibold mb-4 flex items-center gap-2"><Package className="h-4 w-4 text-violet-400" /> Trade Parameters</h3>

                        <div className="space-y-3">
                            <div>
                                <label className="text-xs text-navy-400 mb-1 block">Product Name</label>
                                <input value={form.product_name} onChange={(e) => setForm({ ...form, product_name: e.target.value })}
                                    className="w-full bg-navy-950 border border-navy-700 rounded-lg px-3 py-2 text-white text-sm focus:border-violet-500 outline-none" />
                            </div>
                            <div className="grid grid-cols-2 gap-2">
                                <div>
                                    <label className="text-xs text-navy-400 mb-1 block">HS Code</label>
                                    <input value={form.product_hs} onChange={(e) => setForm({ ...form, product_hs: e.target.value })}
                                        className="w-full bg-navy-950 border border-navy-700 rounded-lg px-3 py-2 text-white text-sm focus:border-violet-500 outline-none" />
                                </div>
                                <div>
                                    <label className="text-xs text-navy-400 mb-1 block">Quantity (kg)</label>
                                    <input type="number" value={form.quantity_kg} onChange={(e) => setForm({ ...form, quantity_kg: parseFloat(e.target.value) || 0 })}
                                        className="w-full bg-navy-950 border border-navy-700 rounded-lg px-3 py-2 text-white text-sm focus:border-violet-500 outline-none" />
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-2">
                                <div>
                                    <label className="text-xs text-navy-400 mb-1 block">Origin</label>
                                    <input value={form.origin_country} onChange={(e) => setForm({ ...form, origin_country: e.target.value })}
                                        className="w-full bg-navy-950 border border-navy-700 rounded-lg px-3 py-2 text-white text-sm focus:border-violet-500 outline-none" placeholder="CH" />
                                </div>
                                <div>
                                    <label className="text-xs text-navy-400 mb-1 block">Destination</label>
                                    <input value={form.destination_country} onChange={(e) => setForm({ ...form, destination_country: e.target.value })}
                                        className="w-full bg-navy-950 border border-navy-700 rounded-lg px-3 py-2 text-white text-sm focus:border-violet-500 outline-none" placeholder="AE" />
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-2">
                                <div>
                                    <label className="text-xs text-navy-400 mb-1 block">Buy ($/kg)</label>
                                    <input type="number" step="0.01" value={form.buy_price_per_kg} onChange={(e) => setForm({ ...form, buy_price_per_kg: parseFloat(e.target.value) || 0 })}
                                        className="w-full bg-navy-950 border border-navy-700 rounded-lg px-3 py-2 text-white text-sm focus:border-violet-500 outline-none" />
                                </div>
                                <div>
                                    <label className="text-xs text-navy-400 mb-1 block">Sell ($/kg)</label>
                                    <input type="number" step="0.01" value={form.sell_price_per_kg} onChange={(e) => setForm({ ...form, sell_price_per_kg: parseFloat(e.target.value) || 0 })}
                                        className="w-full bg-navy-950 border border-navy-700 rounded-lg px-3 py-2 text-white text-sm focus:border-violet-500 outline-none" />
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-2">
                                <div>
                                    <label className="text-xs text-navy-400 mb-1 block">Buy Currency</label>
                                    <input value={form.buy_currency} onChange={(e) => setForm({ ...form, buy_currency: e.target.value })}
                                        className="w-full bg-navy-950 border border-navy-700 rounded-lg px-3 py-2 text-white text-sm focus:border-violet-500 outline-none" />
                                </div>
                                <div>
                                    <label className="text-xs text-navy-400 mb-1 block">Sell Currency</label>
                                    <input value={form.sell_currency} onChange={(e) => setForm({ ...form, sell_currency: e.target.value })}
                                        className="w-full bg-navy-950 border border-navy-700 rounded-lg px-3 py-2 text-white text-sm focus:border-violet-500 outline-none" />
                                </div>
                            </div>
                        </div>

                        <button onClick={handleAnalyze} disabled={loading}
                            className="w-full mt-5 py-3 bg-gradient-to-r from-violet-500 to-purple-600 text-white rounded-lg font-semibold hover:opacity-90 transition-opacity disabled:opacity-50 flex items-center justify-center gap-2">
                            {loading ? <><Loader2 className="h-4 w-4 animate-spin" /> Analyzing...</> : <><Brain className="h-4 w-4" /> Analyze Trade (10 credits)</>}
                        </button>
                    </div>
                </div>

                {/* Results */}
                <div className="lg:col-span-2 space-y-4">
                    {error && (
                        <div className="p-4 bg-red-400/10 border border-red-400/20 rounded-xl flex items-center gap-3">
                            <AlertTriangle className="h-5 w-5 text-red-400" />
                            <p className="text-red-400 text-sm">{error}</p>
                        </div>
                    )}

                    {!result && !loading && (
                        <div className="bg-navy-900 border border-navy-800 rounded-xl p-16 text-center">
                            <Brain className="h-20 w-20 mx-auto text-navy-700 mb-4" />
                            <h3 className="text-white font-semibold text-lg mb-2">Enter Trade Parameters</h3>
                            <p className="text-navy-500 text-sm max-w-md mx-auto">
                                Get a complete trade intelligence report: profit analysis, risk assessment, market timing, and negotiation strategy.
                            </p>
                        </div>
                    )}

                    {loading && (
                        <div className="bg-navy-900 border border-navy-800 rounded-xl p-16 text-center">
                            <div className="h-16 w-16 mx-auto border-4 border-violet-500 border-t-transparent rounded-full animate-spin mb-4"></div>
                            <h3 className="text-white font-semibold mb-2">Running 4 Engines...</h3>
                            <p className="text-navy-500 text-sm">Arbitrage → Risk → Demand → Cultural</p>
                        </div>
                    )}

                    {result && (
                        <>
                            {/* Verdict */}
                            <VerdictBanner verdict={result.verdict} />

                            {/* Scenarios */}
                            <div className="grid grid-cols-3 gap-3">
                                {Object.entries(result.scenarios).map(([key, s]) => (
                                    <div key={key} className={`bg-navy-900 border rounded-xl p-4 ${key === "realistic" ? "border-violet-500/50" : "border-navy-800"}`}>
                                        <p className="text-xs text-navy-400 uppercase">{s.label}</p>
                                        <p className={`text-xl font-bold mt-1 ${s.profit >= 0 ? "text-green-400" : "text-red-400"}`}>
                                            ${s.profit.toLocaleString()}
                                        </p>
                                        <p className="text-xs text-navy-500 mt-1">{s.margin_pct}% margin • {s.probability}% likely</p>
                                    </div>
                                ))}
                            </div>

                            {/* Tabs */}
                            <div className="flex gap-1 bg-navy-900 rounded-xl p-1 border border-navy-800">
                                {[
                                    { key: "financials", label: "Financials", icon: DollarSign },
                                    { key: "risk", label: "Risk", icon: Shield },
                                    { key: "timing", label: "Timing", icon: Calendar },
                                    { key: "negotiation", label: "Negotiation", icon: Users },
                                ].map(tab => (
                                    <button key={tab.key} onClick={() => setActiveTab(tab.key as any)}
                                        className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-all flex items-center justify-center gap-1.5 ${activeTab === tab.key ? "bg-violet-500/20 text-violet-400" : "text-navy-400 hover:text-white"}`}>
                                        <tab.icon className="h-3.5 w-3.5" /> {tab.label}
                                    </button>
                                ))}
                            </div>

                            {/* Tab Content */}
                            <div className="bg-navy-900 border border-navy-800 rounded-xl p-5">
                                {activeTab === "financials" && (
                                    <div className="space-y-4">
                                        <div className="grid grid-cols-2 gap-4">
                                            <div className="bg-navy-950 rounded-lg p-4">
                                                <p className="text-xs text-navy-400">Gross Margin</p>
                                                <p className="text-2xl font-bold text-white">{result.financials.gross_margin_pct}%</p>
                                            </div>
                                            <div className="bg-navy-950 rounded-lg p-4">
                                                <p className="text-xs text-navy-400">Risk-Adjusted Margin</p>
                                                <p className="text-2xl font-bold text-white">{result.financials.risk_adjusted_margin_pct}%</p>
                                            </div>
                                            <div className="bg-navy-950 rounded-lg p-4">
                                                <p className="text-xs text-navy-400">Total Profit</p>
                                                <p className={`text-2xl font-bold ${result.financials.total_profit >= 0 ? "text-green-400" : "text-red-400"}`}>
                                                    ${result.financials.total_profit.toLocaleString()}
                                                </p>
                                            </div>
                                            <div className="bg-navy-950 rounded-lg p-4">
                                                <p className="text-xs text-navy-400">Profit Probability</p>
                                                <p className="text-2xl font-bold text-white">{result.financials.profit_probability_score}/100</p>
                                            </div>
                                        </div>
                                        <div className="bg-navy-950 rounded-lg p-4">
                                            <h4 className="text-sm font-semibold text-white mb-3">Cost Breakdown (per kg)</h4>
                                            {Object.entries(result.cost_breakdown).map(([key, val]) => (
                                                <div key={key} className="flex justify-between py-1 text-sm">
                                                    <span className="text-navy-400">{key.replace(/_/g, " ")}</span>
                                                    <span className="text-white font-mono">${(val as number).toFixed(4)}</span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {activeTab === "risk" && (
                                    <div className="space-y-4">
                                        <div className="flex items-center justify-between">
                                            <div>
                                                <p className="text-xs text-navy-400">Composite Risk</p>
                                                <p className="text-3xl font-bold text-white">{(result.risk.composite_score * 100).toFixed(0)}%</p>
                                            </div>
                                            <RiskBadge level={result.risk.level} />
                                        </div>
                                        <div className="space-y-2">
                                            {Object.entries(result.risk.factors).map(([key, factor]) => (
                                                <div key={key} className="flex items-center gap-3">
                                                    <span className="text-sm text-navy-400 w-40">{key.replace(/_/g, " ")}</span>
                                                    <div className="flex-1 bg-navy-950 rounded-full h-2">
                                                        <div className="h-2 rounded-full bg-gradient-to-r from-green-500 to-red-500 transition-all"
                                                            style={{ width: `${(factor as any).score * 100}%` }}></div>
                                                    </div>
                                                    <span className="text-xs text-navy-500 font-mono w-12 text-right">{((factor as any).score * 100).toFixed(0)}%</span>
                                                </div>
                                            ))}
                                        </div>
                                        {result.risk.alerts.length > 0 && (
                                            <div className="space-y-2 pt-3 border-t border-navy-800">
                                                {result.risk.alerts.map((alert, i) => (
                                                    <div key={i} className={`flex items-start gap-2 text-sm ${alert.severity === "critical" ? "text-red-400" : "text-yellow-400"}`}>
                                                        <AlertTriangle className="h-4 w-4 mt-0.5 shrink-0" />
                                                        <span>{alert.message}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                        <div className="bg-navy-950 rounded-lg p-3">
                                            <p className="text-xs text-navy-400">Recommended Payment Terms</p>
                                            <p className="text-white text-sm font-semibold">{result.risk.payment_terms}</p>
                                        </div>
                                    </div>
                                )}

                                {activeTab === "timing" && (
                                    <div className="space-y-4">
                                        <div className="grid grid-cols-2 gap-4">
                                            <div className="bg-navy-950 rounded-lg p-4">
                                                <p className="text-xs text-navy-400">Best Entry Month</p>
                                                <p className="text-xl font-bold text-violet-400">{result.timing.best_entry_month}</p>
                                                <p className="text-xs text-navy-500 mt-1">{result.timing.best_entry_reason}</p>
                                            </div>
                                            <div className="bg-navy-950 rounded-lg p-4">
                                                <p className="text-xs text-navy-400">Peak Demand</p>
                                                <p className="text-xl font-bold text-emerald-400">{result.timing.peak_month}</p>
                                            </div>
                                        </div>
                                        {result.timing.cultural_events.length > 0 && (
                                            <div className="bg-navy-950 rounded-lg p-4">
                                                <h4 className="text-sm font-semibold text-white mb-2">Cultural Events Affecting Demand</h4>
                                                {result.timing.cultural_events.map((evt, i) => (
                                                    <div key={i} className="flex justify-between py-1 text-sm">
                                                        <span className="text-navy-300">{evt.event.replace(/_/g, " ")}</span>
                                                        <span className="text-emerald-400 font-mono">×{evt.demand_multiplier.toFixed(1)}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                )}

                                {activeTab === "negotiation" && (
                                    <div className="space-y-4">
                                        {result.negotiation.approach && (
                                            <div className="bg-navy-950 rounded-lg p-4">
                                                <h4 className="text-sm font-semibold text-white mb-2">Negotiation Approach</h4>
                                                <p className="text-sm text-navy-300">{result.negotiation.approach}</p>
                                            </div>
                                        )}
                                        {result.negotiation.communication_style && (
                                            <div className="bg-navy-950 rounded-lg p-4">
                                                <h4 className="text-sm font-semibold text-white mb-2">Communication Style</h4>
                                                <p className="text-sm text-navy-300">{result.negotiation.communication_style}</p>
                                            </div>
                                        )}
                                        {result.negotiation.power_moves.length > 0 && (
                                            <div className="bg-navy-950 rounded-lg p-4">
                                                <h4 className="text-sm font-semibold text-emerald-400 mb-2">Power Moves</h4>
                                                <ul className="space-y-1">
                                                    {result.negotiation.power_moves.map((m, i) => (
                                                        <li key={i} className="text-sm text-navy-300 flex items-start gap-2">
                                                            <span className="text-emerald-400">✓</span> {m}
                                                        </li>
                                                    ))}
                                                </ul>
                                            </div>
                                        )}
                                        {result.negotiation.red_flags.length > 0 && (
                                            <div className="bg-navy-950 rounded-lg p-4">
                                                <h4 className="text-sm font-semibold text-red-400 mb-2">Red Flags — Avoid</h4>
                                                <ul className="space-y-1">
                                                    {result.negotiation.red_flags.map((f, i) => (
                                                        <li key={i} className="text-sm text-navy-300 flex items-start gap-2">
                                                            <span className="text-red-400">✗</span> {f}
                                                        </li>
                                                    ))}
                                                </ul>
                                            </div>
                                        )}
                                        <div className="bg-navy-950 rounded-lg p-3">
                                            <p className="text-xs text-navy-400">Suggested Payment</p>
                                            <p className="text-sm text-white font-semibold">{result.negotiation.payment_suggestion}</p>
                                        </div>
                                    </div>
                                )}
                            </div>

                            <p className="text-xs text-navy-600 text-center">
                                ⚠️ AI-assisted analysis. Financial decisions should consider multiple data sources.
                                Math engines are deterministic. Cultural analysis is Gemini-generated.
                            </p>
                        </>
                    )}
                </div>
            </div>
        </div>
    );
}
