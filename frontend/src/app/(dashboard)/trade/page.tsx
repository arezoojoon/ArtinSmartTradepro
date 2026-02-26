"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Search, TrendingUp, Globe, Package, Ship, Brain, Camera, Loader2, AlertTriangle, Sparkles } from "lucide-react";
import api, { ApiError } from "@/lib/api";

type AnalysisType = "seasonal" | "market" | "brand" | "shipping" | "card-scan" | "insights";

const analysisTools = [
    { type: "seasonal" as const, label: "Seasonal Demand", icon: TrendingUp, cost: "1.0", color: "text-green-400" },
    { type: "market" as const, label: "Market Intelligence", icon: Globe, cost: "1.5", color: "text-blue-400" },
    { type: "brand" as const, label: "Brand & Supply Chain", icon: Package, cost: "2.0", color: "text-purple-400" },
    { type: "shipping" as const, label: "Shipping & Compliance", icon: Ship, cost: "1.0", color: "text-orange-400" },
    { type: "card-scan" as const, label: "Scan Business Card", icon: Camera, cost: "0.5", color: "text-pink-400" },
    { type: "insights" as const, label: "AI Insights", icon: Brain, cost: "1.0", color: "text-[#f5a623]" },
];

export default function TradePage() {
    const router = useRouter();
    const [active, setActive] = useState<AnalysisType>("seasonal");
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<any>(null);
    const [error, setError] = useState<string | null>(null);

    // Form states
    const [product, setProduct] = useState("");
    const [region, setRegion] = useState("");
    const [season, setSeason] = useState("Q4");
    const [brand, setBrand] = useState("");
    const [origin, setOrigin] = useState("");
    const [destination, setDestination] = useState("");
    const [dataSummary, setDataSummary] = useState("");



    const runAnalysis = async () => {
        setLoading(true);
        setError(null);
        setResult(null);

        let endpoint = "";
        let body: any = {};

        switch (active) {
            case "seasonal":
                endpoint = "/trade/analyze/seasonal";
                body = { product, region: region || "global" };
                break;
            case "market":
                endpoint = "/trade/analyze/market";
                body = { product, season };
                break;
            case "brand":
                endpoint = "/trade/analyze/brand";
                body = { brand_name: brand };
                break;
            case "shipping":
                endpoint = "/trade/shipping";
                body = { product, origin, destination };
                break;
            case "insights":
                endpoint = "/trade/insights";
                body = { data_summary: dataSummary };
                break;
        }

        try {
            const { data } = await api.post(endpoint, body);
            setResult(data.result);
        } catch (err: any) {
            if (err instanceof ApiError && err.status === 403) {
                setError("This feature requires an Enterprise plan. Upgrade to access Trade Intelligence.");
            } else {
                setError(err?.message || "Connection error. Please try again.");
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="p-6 max-w-6xl mx-auto">
            <div className="flex items-center gap-3 mb-8">
                <Sparkles className="h-7 w-7 text-[#f5a623]" />
                <div>
                    <h1 className="text-2xl font-bold">Trade Intelligence</h1>
                    <p className="text-sm text-navy-400">AI-powered market, brand, and logistics analysis</p>
                </div>
            </div>

            {/* Tool Selector */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-8">
                {analysisTools.map((tool) => (
                    <button
                        key={tool.type}
                        onClick={() => { if (tool.type === "card-scan") { router.push("/crm/vision"); return; } setActive(tool.type); setResult(null); setError(null); }}
                        className={`p-4 rounded-xl border transition-all text-left ${active === tool.type
                            ? "bg-navy-800 border-gold-400/50 shadow-lg shadow-gold-400/5"
                            : "bg-[#0e1e33]/50 border-navy-700/30 hover:border-navy-600"
                            }`}
                    >
                        <tool.icon className={`h-5 w-5 mb-2 ${tool.color}`} />
                        <p className="text-xs font-medium text-white">{tool.label}</p>
                        <p className="text-[10px] text-navy-500 mt-1">{tool.cost} credit</p>
                    </button>
                ))}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Input Panel */}
                <div className="bg-[#0e1e33]/50 border border-navy-700/30 rounded-2xl p-6">
                    <h2 className="text-sm font-semibold text-navy-300 mb-4 uppercase tracking-wider">
                        {analysisTools.find(t => t.type === active)?.label}
                    </h2>

                    {(active === "seasonal" || active === "market" || active === "shipping") && (
                        <div className="space-y-4">
                            <div>
                                <label className="block text-xs text-navy-400 mb-1">Product / Category</label>
                                <input value={product} onChange={e => setProduct(e.target.value)}
                                    placeholder="e.g. Cocoa Powder, Canned Tuna, Baby Formula"
                                    className="w-full px-4 py-3 bg-navy-800 border border-navy-600 rounded-xl text-white placeholder:text-navy-500 focus:border-gold-400 focus:outline-none text-sm" />
                            </div>
                            {active === "seasonal" && (
                                <div>
                                    <label className="block text-xs text-navy-400 mb-1">Target Region</label>
                                    <input value={region} onChange={e => setRegion(e.target.value)}
                                        placeholder="e.g. Europe, Middle East, Southeast Asia"
                                        className="w-full px-4 py-3 bg-navy-800 border border-navy-600 rounded-xl text-white placeholder:text-navy-500 focus:border-gold-400 focus:outline-none text-sm" />
                                </div>
                            )}
                            {active === "market" && (
                                <div>
                                    <label className="block text-xs text-navy-400 mb-1">Season</label>
                                    <select value={season} onChange={e => setSeason(e.target.value)}
                                        className="w-full px-4 py-3 bg-navy-800 border border-navy-600 rounded-xl text-white focus:border-gold-400 focus:outline-none text-sm">
                                        <option value="Q1">Q1 (Jan–Mar)</option>
                                        <option value="Q2">Q2 (Apr–Jun)</option>
                                        <option value="Q3">Q3 (Jul–Sep)</option>
                                        <option value="Q4">Q4 (Oct–Dec)</option>
                                    </select>
                                </div>
                            )}
                            {active === "shipping" && (
                                <>
                                    <div>
                                        <label className="block text-xs text-navy-400 mb-1">Origin Country</label>
                                        <input value={origin} onChange={e => setOrigin(e.target.value)}
                                            placeholder="e.g. Turkey, China, Germany"
                                            className="w-full px-4 py-3 bg-navy-800 border border-navy-600 rounded-xl text-white placeholder:text-navy-500 focus:border-gold-400 focus:outline-none text-sm" />
                                    </div>
                                    <div>
                                        <label className="block text-xs text-navy-400 mb-1">Destination Country</label>
                                        <input value={destination} onChange={e => setDestination(e.target.value)}
                                            placeholder="e.g. UAE, Saudi Arabia, Iraq"
                                            className="w-full px-4 py-3 bg-navy-800 border border-navy-600 rounded-xl text-white placeholder:text-navy-500 focus:border-gold-400 focus:outline-none text-sm" />
                                    </div>
                                </>
                            )}
                        </div>
                    )}

                    {active === "brand" && (
                        <div>
                            <label className="block text-xs text-navy-400 mb-1">Brand Name</label>
                            <input value={brand} onChange={e => setBrand(e.target.value)}
                                placeholder="e.g. Nutella, Nescafé, Red Bull"
                                className="w-full px-4 py-3 bg-navy-800 border border-navy-600 rounded-xl text-white placeholder:text-navy-500 focus:border-gold-400 focus:outline-none text-sm" />
                        </div>
                    )}

                    {active === "insights" && (
                        <div>
                            <label className="block text-xs text-navy-400 mb-1">Data Summary</label>
                            <textarea value={dataSummary} onChange={e => setDataSummary(e.target.value)} rows={5}
                                placeholder="Paste your trade data, lead summary, or market notes..."
                                className="w-full px-4 py-3 bg-navy-800 border border-navy-600 rounded-xl text-white placeholder:text-navy-500 focus:border-gold-400 focus:outline-none text-sm resize-none" />
                        </div>
                    )}

                    {active === "card-scan" && (
                        <div className="text-center py-8">
                            <Camera className="h-12 w-12 text-navy-500 mx-auto mb-3" />
                            <p className="text-sm text-navy-400">Upload a business card image to extract contact info</p>
                            <p className="text-xs text-navy-600 mt-1">JPG, PNG — max 5MB</p>
                        </div>
                    )}

                    {active !== "card-scan" && (
                        <button onClick={runAnalysis} disabled={loading}
                            className="mt-6 w-full py-3 bg-[#f5a623] text-navy-950 rounded-xl font-semibold hover:bg-gold-300 transition-all disabled:opacity-50 flex items-center justify-center gap-2">
                            {loading ? <><Loader2 className="h-4 w-4 animate-spin" /> Analyzing...</> : <><Search className="h-4 w-4" /> Run Analysis</>}
                        </button>
                    )}
                </div>

                {/* Results Panel */}
                <div className="bg-[#0e1e33]/50 border border-navy-700/30 rounded-2xl p-6">
                    <h2 className="text-sm font-semibold text-navy-300 mb-4 uppercase tracking-wider">Results</h2>

                    {error && (
                        <div className="flex items-start gap-3 p-4 bg-red-900/20 border border-red-700/30 rounded-xl">
                            <AlertTriangle className="h-5 w-5 text-red-400 mt-0.5" />
                            <p className="text-sm text-red-300">{error}</p>
                        </div>
                    )}

                    {!result && !error && !loading && (
                        <div className="text-center py-16">
                            <Brain className="h-12 w-12 text-navy-700 mx-auto mb-3" />
                            <p className="text-sm text-navy-500">Run an analysis to see results</p>
                        </div>
                    )}

                    {loading && (
                        <div className="text-center py-16">
                            <Loader2 className="h-8 w-8 text-[#f5a623] animate-spin mx-auto mb-3" />
                            <p className="text-sm text-navy-400">AI is analyzing...</p>
                            <p className="text-xs text-navy-600 mt-1">This may take 5-15 seconds</p>
                        </div>
                    )}

                    {result && (
                        <div className="space-y-3 text-sm">
                            {/* Confidence Badge */}
                            {result.confidence !== undefined && (
                                <div className="flex items-center gap-2 mb-4">
                                    <span className="text-xs text-navy-400">Confidence</span>
                                    <div className="flex-1 h-2 bg-navy-800 rounded-full overflow-hidden">
                                        <div
                                            className={`h-full rounded-full ${result.confidence > 0.7 ? "bg-green-400" : result.confidence > 0.4 ? "bg-yellow-400" : "bg-red-400"
                                                }`}
                                            style={{ width: `${(result.confidence || 0) * 100}%` }}
                                        />
                                    </div>
                                    <span className="text-xs text-navy-300">{Math.round((result.confidence || 0) * 100)}%</span>
                                </div>
                            )}

                            {/* Render JSON result */}
                            <pre className="bg-navy-800/50 rounded-xl p-4 overflow-auto max-h-[400px] text-xs text-navy-200 whitespace-pre-wrap">
                                {JSON.stringify(result, null, 2)}
                            </pre>

                            {/* Disclaimer */}
                            {result.disclaimer && (
                                <div className="flex items-start gap-2 p-3 bg-navy-800/30 rounded-lg border border-navy-700/30">
                                    <AlertTriangle className="h-4 w-4 text-yellow-400 mt-0.5 flex-shrink-0" />
                                    <p className="text-xs text-navy-400">{result.disclaimer}</p>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
