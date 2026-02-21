"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Search, Globe, FileText, Loader2, Check, AlertTriangle, Download } from "lucide-react";

interface HunterResult {
    id: string;
    type: "lead" | "trade_data" | "supplier" | "buyer" | "company";
    source: string;
    name?: string;
    company?: string;
    email?: string;
    phone?: string;
    website?: string;
    confidence_score?: number;
    raw_data?: any;
    is_imported?: boolean;
}

export default function HunterPage() {
    // Inputs
    const [keyword, setKeyword] = useState("");
    const [location, setLocation] = useState("");
    const [selectedSources, setSelectedSources] = useState<string[]>([
        "maps", "un_comtrade", "trademap"
    ]);

    // State
    const [jobId, setJobId] = useState<string | null>(null);
    const [status, setStatus] = useState<"idle" | "pending" | "processing" | "completed" | "failed">("idle");
    const [results, setResults] = useState<HunterResult[]>([]);
    const [importing, setImporting] = useState<string | null>(null);

    // Config
    const availableSources = [
        { id: "maps", label: "Google Maps", category: "Scraper" },
        { id: "linkedin_serp", label: "LinkedIn SERP", category: "Scraper" },
        { id: "website", label: "Company Websites", category: "Scraper" },
        { id: "un_comtrade", label: "UN Comtrade", category: "Official API" },
        { id: "trademap", label: "TradeMap", category: "Official API" },
        { id: "freight", label: "Freight Market", category: "Official API" },
        { id: "fx", label: "FX Rates", category: "Official API" },
        { id: "weather", label: "Weather Risk", category: "Official API" },
        { id: "political", label: "Political Risk", category: "Official API" },
    ];

    const [hsCode, setHsCode] = useState("");
    const [minVolume, setMinVolume] = useState("");
    const [minGrowth, setMinGrowth] = useState("");

    // Toggle Source
    const toggleSource = (sourceId: string) => {
        if (selectedSources.includes(sourceId)) {
            setSelectedSources(selectedSources.filter(s => s !== sourceId));
        } else {
            setSelectedSources([...selectedSources, sourceId]);
        }
    };

    // 1. Start Hunt
    const startHunt = async () => {
        if (!keyword || selectedSources.length === 0) {
            alert("Please enter a keyword and select at least one source.");
            return;
        }

        setStatus("pending");
        setResults([]);

        try {
            const { data } = await api.post("/hunter/start", {
                keyword,
                location,
                sources: selectedSources,
                hs_code: hsCode,
                min_volume_usd: minVolume ? parseFloat(minVolume) : undefined,
                min_growth_pct: minGrowth ? parseFloat(minGrowth) : undefined
            });
            setJobId(data.job_id);
            setStatus("processing");
        } catch (error) {
            console.error("Failed to start hunter:", error);
            setStatus("failed");
            alert("Failed to start job.");
        }
    };

    // 2. Poll Status
    useEffect(() => {
        if (!jobId || status === "completed" || status === "failed") return;

        const interval = setInterval(async () => {
            try {
                const { data } = await api.get(`/hunter/status/${jobId}`);
                if (data.job_status === "completed") {
                    setStatus("completed");
                    fetchResults(jobId);
                } else if (data.job_status === "failed") {
                    setStatus("failed");
                }
            } catch (error) {
                console.error("Polling error:", error);
            }
        }, 2000);

        return () => clearInterval(interval);
    }, [jobId, status]);

    // 3. Fetch Results
    const fetchResults = async (id: string) => {
        try {
            const { data } = await api.get(`/hunter/results/${id}`);
            setResults(data);
        } catch (error) {
            console.error("Msg:", error);
        }
    };

    // 4. Import to CRM
    const importToCRM = async (resultId: string) => {
        setImporting(resultId);
        try {
            await api.post("/hunter/import-to-crm", { result_id: resultId });
            // Update local state to show imported
            setResults(prev => prev.map(r => r.id === resultId ? { ...r, is_imported: true } : r));
        } catch (error) {
            alert("Failed to import lead.");
        } finally {
            setImporting(null);
        }
    };

    // Filtered Views
    const leads = results.filter(r => r.type === "lead" || r.type === "company" || r.type === "supplier");
    const dataPoints = results.filter(r => r.type === "trade_data");

    return (
        <div className="p-8 space-y-8 min-h-screen text-white">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-white">Hunter <span className="text-gold-400">AI</span></h1>
                    <p className="text-gray-400">Global Trade Intelligence & Lead Scraper</p>
                </div>
                {status === "processing" && (
                    <div className="flex items-center gap-2 text-gold-400 animate-pulse">
                        <Loader2 className="h-5 w-5 animate-spin" />
                        Hunting in progress...
                    </div>
                )}
            </div>

            {/* CONFIG PANEL */}
            <Card className="bg-navy-900 border-navy-800">
                <CardHeader>
                    <CardTitle className="text-white">Mission Configuration</CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                    <div className="grid md:grid-cols-3 gap-4">
                        <div className="space-y-2">
                            <label className="text-sm text-gray-400">HS Code (e.g. 1006.30)</label>
                            <Input
                                placeholder="4 or 6 digit code"
                                value={hsCode}
                                onChange={(e) => setHsCode(e.target.value)}
                                className="bg-navy-950 border-navy-700 text-white"
                            />
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm text-gray-400">Min Volume (USD)</label>
                            <Input
                                type="number"
                                placeholder="e.g. 5000000"
                                value={minVolume}
                                onChange={(e) => setMinVolume(e.target.value)}
                                className="bg-navy-950 border-navy-700 text-white"
                            />
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm text-gray-400">Min Growth (%)</label>
                            <Input
                                type="number"
                                placeholder="e.g. 10"
                                value={minGrowth}
                                onChange={(e) => setMinGrowth(e.target.value)}
                                className="bg-navy-950 border-navy-700 text-white"
                            />
                        </div>
                    </div>

                    <div className="space-y-2">
                        <label className="text-sm text-gray-400">Intelligence Sources</label>
                        <div className="flex flex-wrap gap-2">
                            {availableSources.map((src) => (
                                <div
                                    key={src.id}
                                    onClick={() => toggleSource(src.id)}
                                    className={`cursor-pointer px-3 py-1.5 rounded-full border text-xs font-medium transition-all flex items-center gap-2
                                        ${selectedSources.includes(src.id)
                                            ? "bg-gold-500/20 border-gold-500 text-gold-400"
                                            : "bg-navy-950 border-navy-700 text-gray-500 hover:border-gray-500"}`}
                                >
                                    {src.label}
                                    {selectedSources.includes(src.id) && <Check className="h-3 w-3" />}
                                </div>
                            ))}
                        </div>
                    </div>

                    <Button
                        onClick={startHunt}
                        disabled={status === "processing"}
                        className="w-full bg-gold-500 text-black hover:bg-gold-400 font-bold"
                    >
                        {status === "processing" ? "Scanning Global Networks..." : "Start Global Hunt"}
                    </Button>
                </CardContent>
            </Card>

            {/* RESULTS SECTION */}
            {results.length > 0 && (
                <div className="space-y-6">
                    {/* LEADS TABLE */}
                    {leads.length > 0 && (
                        <Card className="bg-navy-900 border-navy-800">
                            <CardHeader>
                                <CardTitle className="text-white flex items-center gap-2">
                                    <Globe className="h-5 w-5 text-blue-400" />
                                    Verified Leads ({leads.length})
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="overflow-x-auto">
                                    <table className="w-full text-sm text-left">
                                        <thead className="bg-navy-950 text-gray-400 uppercase text-xs">
                                            <tr>
                                                <th className="px-4 py-3">Company</th>
                                                <th className="px-4 py-3">Contact</th>
                                                <th className="px-4 py-3">Source</th>
                                                <th className="px-4 py-3">Confidence</th>
                                                <th className="px-4 py-3 text-right">Action</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-navy-800">
                                            {leads.map((lead) => (
                                                <tr key={lead.id} className="hover:bg-navy-800/50">
                                                    <td className="px-4 py-3 font-medium text-white">
                                                        {lead.company || lead.name}
                                                        {lead.website && <a href={lead.website} target="_blank" className="block text-xs text-blue-400 hover:underline">{lead.website}</a>}
                                                    </td>
                                                    <td className="px-4 py-3 text-gray-300">
                                                        {lead.email || "-"}<br />
                                                        <span className="text-xs text-gray-500">{lead.phone}</span>
                                                    </td>
                                                    <td className="px-4 py-3">
                                                        <Badge variant="outline" className="text-xs border-gray-600 text-gray-400">
                                                            {lead.source}
                                                        </Badge>
                                                    </td>
                                                    <td className="px-4 py-3">
                                                        <span className={`text-xs font-bold ${(lead.confidence_score || 0) > 0.8 ? "text-green-500" : "text-yellow-500"
                                                            }`}>
                                                            {Math.round((lead.confidence_score || 0) * 100)}%
                                                        </span>
                                                    </td>
                                                    <td className="px-4 py-3 text-right">
                                                        {lead.is_imported ? (
                                                            <span className="text-xs text-green-500 flex items-center justify-end gap-1">
                                                                <Check className="h-3 w-3" /> Imported
                                                            </span>
                                                        ) : (
                                                            <Button
                                                                size="sm"
                                                                variant="outline"
                                                                className="h-7 text-xs border-gold-500/50 text-gold-400 hover:bg-gold-500 hover:text-black"
                                                                onClick={() => importToCRM(lead.id)}
                                                                disabled={importing === lead.id}
                                                            >
                                                                {importing === lead.id ? "..." : "Import"}
                                                            </Button>
                                                        )}
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </CardContent>
                        </Card>
                    )}

                    {/* MARKET DATA TABLE */}
                    {dataPoints.length > 0 && (
                        <Card className="bg-navy-900 border-navy-800">
                            <CardHeader>
                                <CardTitle className="text-white flex items-center gap-2">
                                    <AlertTriangle className="h-5 w-5 text-purple-400" />
                                    Market Intelligence ({dataPoints.length})
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                    {dataPoints.map((dp) => (
                                        <div key={dp.id} className="bg-navy-950 p-4 rounded-lg border border-navy-800">
                                            <div className="flex justify-between items-start mb-2">
                                                <Badge className="bg-navy-800 text-gray-300 hover:bg-navy-700">
                                                    {dp.source}
                                                </Badge>
                                                <span className="text-xs text-gray-500">
                                                    {new Date().toLocaleDateString()}
                                                </span>
                                            </div>
                                            <div className="text-sm font-mono text-gray-300 break-all">
                                                <pre className="whitespace-pre-wrap text-xs">
                                                    {JSON.stringify(dp.raw_data, null, 2)}
                                                </pre>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </CardContent>
                        </Card>
                    )}
                </div>
            )}
        </div>
    );
}
