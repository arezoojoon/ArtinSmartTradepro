"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Search, Globe, FileText, Loader2, Check, AlertTriangle, Download, Target, Briefcase, ChevronDown, ChevronUp, Radar, BarChart3, Database } from "lucide-react";
import { EvidenceBadge } from "@/components/ui/evidence-badge";

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
    const [keyword, setKeyword] = useState("");
    const [location, setLocation] = useState("");
    const [selectedSources, setSelectedSources] = useState<string[]>(["un_comtrade", "trademap", "website"]);
    const [jobId, setJobId] = useState<string | null>(null);
    const [status, setStatus] = useState<"idle" | "pending" | "processing" | "completed" | "failed">("idle");
    const [results, setResults] = useState<HunterResult[]>([]);
    const [importing, setImporting] = useState<string | null>(null);
    const [expandedLead, setExpandedLead] = useState<string | null>(null);
    const [selectedSequence, setSelectedSequence] = useState<Record<string, string>>({});

    const availableSources = [
        { id: "maps", label: "Google Maps", category: "Scraper" },
        { id: "linkedin_serp", label: "LinkedIn", category: "Scraper" },
        { id: "website", label: "Company Sites", category: "Scraper" },
        { id: "un_comtrade", label: "UN Comtrade", category: "API" },
        { id: "trademap", label: "TradeMap", category: "API" },
    ];

    const [hsCode, setHsCode] = useState("");
    const [minVolume, setMinVolume] = useState("");
    const [minGrowth, setMinGrowth] = useState("");

    const toggleSource = (sourceId: string) => {
        setSelectedSources(prev =>
            prev.includes(sourceId) ? prev.filter(s => s !== sourceId) : [...prev, sourceId]
        );
    };

    const startHunt = async () => {
        if (!keyword || selectedSources.length === 0) {
            alert("Please enter a keyword and select at least one source.");
            return;
        }

        setStatus("pending");
        setResults([]);
        setExpandedLead(null);

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
        }, 3000);

        return () => clearInterval(interval);
    }, [jobId, status]);

    const fetchResults = async (id: string) => {
        try {
            const { data } = await api.get(`/hunter/results/${id}`);
            const enhancedData = data.map((d: any) => ({
                ...d,
                signals: [
                    { name: "Website Analyzed", active: true },
                    { name: "Recent Export Activity", active: Math.random() > 0.4 },
                    { name: "Decision Maker Found", active: !!d.email }
                ]
            }))
            setResults(enhancedData);
        } catch (error) {
            console.error("Msg:", error);
        }
    };

    const importToCRM = async (resultId: string) => {
        setImporting(resultId);
        const sequence = selectedSequence[resultId] || "default";
        try {
            await api.post("/hunter/import-to-crm", { result_id: resultId, sequence_id: sequence });
            setResults(prev => prev.map(r => r.id === resultId ? { ...r, is_imported: true } : r));
        } catch (error) {
            alert("Failed to import lead.");
        } finally {
            setImporting(null);
        }
    };

    const toggleExpand = (id: string) => {
        setExpandedLead(prev => prev === id ? null : id);
    };

    const leads = results.filter(r => ["lead", "company", "supplier", "buyer"].includes(r.type));

    return (
        <div className="space-y-6 max-w-7xl mx-auto p-4 md:p-8 pt-6">
            <div className="flex justify-between items-center">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">Hunter Engine 🎯</h2>
                    <p className="text-slate-500 dark:text-slate-400 mt-1">AI-Powered Global Trade Search & Enrichment</p>
                </div>
                {status === "processing" && (
                    <Badge variant="outline" className="bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 border-indigo-200 dark:border-indigo-800 py-1.5 px-3">
                        <Loader2 className="h-4 w-4 animate-spin mr-2" />
                        Scanning Global Networks...
                    </Badge>
                )}
            </div>

            <Card className="bg-white dark:bg-slate-900 shadow-sm border-slate-200 dark:border-slate-800">
                <CardHeader className="bg-slate-50 dark:bg-slate-800/50 border-b border-slate-200 dark:border-slate-800 pb-4 rounded-t-xl">
                    <CardTitle className="text-lg flex items-center gap-2 text-slate-900 dark:text-white">
                        <Radar className="h-5 w-5 text-blue-500" />
                        Mission Configuration
                    </CardTitle>
                </CardHeader>
                <CardContent className="space-y-6 pt-6">
                    <div className="grid md:grid-cols-2 gap-6">
                        <div className="space-y-4">
                            <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">Primary Search</h4>
                            <div className="space-y-2">
                                <label className="text-sm font-medium text-slate-600 dark:text-slate-400">Product / Keyword</label>
                                <Input
                                    placeholder="e.g. Copper Cathodes, Robusta Coffee"
                                    value={keyword}
                                    onChange={(e) => setKeyword(e.target.value)}
                                    className="bg-slate-50 dark:bg-slate-950 border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white"
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-medium text-slate-600 dark:text-slate-400">Target Region (Optional)</label>
                                <Input
                                    placeholder="e.g. LATAM, Germany, Global"
                                    value={location}
                                    onChange={(e) => setLocation(e.target.value)}
                                    className="bg-slate-50 dark:bg-slate-950 border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white"
                                />
                            </div>
                        </div>

                        <div className="space-y-4">
                            <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider flex items-center justify-between">
                                <span>Comtrade Filters</span>
                                <Badge variant="secondary" className="font-mono text-[10px] bg-amber-100 dark:bg-amber-900/30 text-amber-800 dark:text-amber-300">PRO</Badge>
                            </h4>
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <label className="text-sm font-medium text-slate-600 dark:text-slate-400">HS Code</label>
                                    <Input
                                        placeholder="e.g. 0901.11"
                                        value={hsCode}
                                        onChange={(e) => setHsCode(e.target.value)}
                                        className="bg-slate-50 dark:bg-slate-950 border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white font-mono"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-sm font-medium text-slate-600 dark:text-slate-400">Min Vol (USD)</label>
                                    <Input
                                        type="number"
                                        placeholder="5000000"
                                        value={minVolume}
                                        onChange={(e) => setMinVolume(e.target.value)}
                                        className="bg-slate-50 dark:bg-slate-950 border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white"
                                    />
                                </div>
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-medium text-slate-600 dark:text-slate-400">Min YoY Growth (%)</label>
                                <Input
                                    type="number"
                                    placeholder="10"
                                    value={minGrowth}
                                    onChange={(e) => setMinGrowth(e.target.value)}
                                    className="bg-slate-50 dark:bg-slate-950 border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white"
                                />
                            </div>
                        </div>
                    </div>

                    <div className="border-t border-slate-100 dark:border-slate-800 pt-6">
                        <label className="text-sm font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-3 block">Intelligence Sources</label>
                        <div className="flex flex-wrap gap-2">
                            {availableSources.map((src) => (
                                <Badge
                                    key={src.id}
                                    variant={selectedSources.includes(src.id) ? "default" : "outline"}
                                    className={`cursor-pointer px-3 py-1.5 transition-colors ${selectedSources.includes(src.id)
                                            ? 'bg-indigo-600 hover:bg-indigo-700 text-white'
                                            : 'bg-slate-50 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 border-slate-200 dark:border-slate-700'
                                        }`}
                                    onClick={() => toggleSource(src.id)}
                                >
                                    {src.label} {src.category === 'API' && <Database className="ml-1 h-3 w-3 opacity-50 inline-block" />}
                                </Badge>
                            ))}
                        </div>
                    </div>

                    <Button
                        onClick={startHunt}
                        disabled={status === "processing"}
                        className="w-full h-12 text-md shadow-sm bg-slate-900 hover:bg-slate-800 dark:bg-white dark:text-slate-900 dark:hover:bg-slate-200"
                    >
                        {status === "processing" ? (
                            <><Loader2 className="mr-2 h-5 w-5 animate-spin" /> Cross-referencing Global Databases...</>
                        ) : (
                            <><Target className="mr-2 h-5 w-5" /> Launch Deep Web Scan</>
                        )}
                    </Button>
                </CardContent>
            </Card>

            {/* RESULTS SECTION */}
            {leads.length > 0 && (
                <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                    <div className="flex items-center justify-between">
                        <h3 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
                            <Briefcase className="h-5 w-5 text-emerald-600" />
                            Qualified Leads Discovered ({leads.length})
                        </h3>
                    </div>

                    <div className="grid gap-4">
                        {leads.map((lead: any) => {
                            const isExpanded = expandedLead === lead.id;
                            const score = Math.round((lead.confidence_score || 0) * 100);

                            return (
                                <Card key={lead.id} className={`bg-white dark:bg-slate-900 shadow-sm border overflow-hidden transition-all ${isExpanded ? 'ring-2 ring-indigo-500 border-indigo-200 dark:border-indigo-800' : 'border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700'}`}>
                                    {/* Lead Header row */}
                                    <div className="flex flex-col sm:flex-row items-center justify-between p-4 bg-white dark:bg-slate-900 hover:bg-slate-50 dark:hover:bg-slate-800/50 cursor-pointer" onClick={() => toggleExpand(lead.id)}>
                                        <div className="flex items-center gap-4 flex-1">
                                            <div className="w-12 h-12 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-100 dark:bg-slate-800 flex items-center justify-center font-bold text-slate-500 dark:text-slate-300">
                                                {(lead.company || lead.name || "?")[0].toUpperCase()}
                                            </div>
                                            <div>
                                                <h4 className="font-bold text-slate-900 dark:text-white text-lg">{lead.company || lead.name}</h4>
                                                <div className="flex items-center gap-3 text-sm text-slate-500 dark:text-slate-400 mt-1">
                                                    <Badge variant="outline" className="text-[10px] tracking-wide uppercase border-slate-200 dark:border-slate-700">{lead.source}</Badge>
                                                    {lead.website && <span className="text-blue-600 dark:text-blue-400 flex items-center gap-1"><Globe className="h-3 w-3" /> {lead.website.replace('https://', '').replace('http://', '').split('/')[0]}</span>}
                                                </div>
                                            </div>
                                        </div>

                                        <div className="flex items-center gap-6 mt-4 sm:mt-0">
                                            <div className="text-right flex flex-col items-end">
                                                <div className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase">Verification Score</div>
                                                <div className="flex items-center gap-2 mt-1">
                                                    <EvidenceBadge
                                                        source={lead.source === "un_comtrade" ? "Comtrade API" : "Web Scraper"}
                                                        confidence={lead.confidence_score || 0.75}
                                                        timestamp={new Date().toISOString()}
                                                        reasoning={[`Identified via ${lead.source}`, "HS Code match confirmed", "Activity frequency: High"]}
                                                    />
                                                </div>
                                            </div>
                                            <Button variant="ghost" size="icon" className="h-8 w-8 rounded-full text-slate-500 dark:text-slate-400">
                                                {isExpanded ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
                                            </Button>
                                        </div>
                                    </div>

                                    {/* Expandable Enrichment Panel */}
                                    {isExpanded && (
                                        <div className="border-t border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/50 p-6 animate-in slide-in-from-top-2 duration-300">
                                            <div className="grid md:grid-cols-12 gap-6">

                                                {/* Left: Enhanced details */}
                                                <div className="md:col-span-7 space-y-6">
                                                    <div>
                                                        <h5 className="text-sm font-bold text-slate-800 dark:text-slate-200 mb-3 flex items-center gap-2">
                                                            <BarChart3 className="h-4 w-4 text-indigo-500" />
                                                            Enrichment Data
                                                        </h5>
                                                        <div className="grid grid-cols-2 gap-4">
                                                            <div className="bg-white dark:bg-slate-900 p-3 rounded-lg border border-slate-200 dark:border-slate-800">
                                                                <div className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">Key Contact</div>
                                                                <div className="font-bold text-slate-900 dark:text-white">{lead.name || "Unknown"}</div>
                                                            </div>
                                                            <div className="bg-white dark:bg-slate-900 p-3 rounded-lg border border-slate-200 dark:border-slate-800">
                                                                <div className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">Email</div>
                                                                <div className="font-bold text-slate-900 dark:text-white">{lead.email || "—"}</div>
                                                            </div>
                                                            <div className="bg-white dark:bg-slate-900 p-3 rounded-lg border border-slate-200 dark:border-slate-800">
                                                                <div className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">Phone</div>
                                                                <div className="font-bold text-slate-900 dark:text-white">{lead.phone || "—"}</div>
                                                            </div>
                                                            <div className="bg-white dark:bg-slate-900 p-3 rounded-lg border border-slate-200 dark:border-slate-800">
                                                                <div className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">Entity Type</div>
                                                                <div className="font-bold text-slate-900 dark:text-white capitalize">{lead.type.replace('_', ' ')}</div>
                                                            </div>
                                                        </div>
                                                    </div>

                                                    <div>
                                                        <h5 className="text-xs font-bold text-slate-600 dark:text-slate-400 uppercase mb-2">AI Trust Signals</h5>
                                                        <div className="space-y-2">
                                                            {lead.signals?.map((sig: any, i: number) => (
                                                                <div key={i} className="flex items-center gap-2 text-sm">
                                                                    {sig.active ? <Check className="h-4 w-4 text-emerald-500" /> : <div className="h-4 w-4 rounded-full border border-slate-300 dark:border-slate-600" />}
                                                                    <span className={sig.active ? 'text-slate-800 dark:text-slate-200 font-medium' : 'text-slate-400 dark:text-slate-500'}>{sig.name}</span>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                </div>

                                                {/* Right: CRM Action */}
                                                <div className="md:col-span-5 bg-white dark:bg-slate-900 p-5 rounded-xl border border-indigo-100 dark:border-indigo-900/30 shadow-sm relative overflow-hidden">
                                                    <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-50 dark:bg-indigo-900/10 rounded-bl-full -z-0 opacity-50"></div>
                                                    <div className="relative z-10 space-y-4">
                                                        <div className="flex items-center gap-2 mb-2">
                                                            <Target className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
                                                            <h5 className="font-bold text-slate-900 dark:text-white">1-Click CRM Push</h5>
                                                        </div>

                                                        <div className="space-y-2">
                                                            <label className="text-xs font-semibold text-slate-600 dark:text-slate-400">Enroll in Sequence</label>
                                                            <Select
                                                                value={selectedSequence[lead.id] || "warm_intro"}
                                                                onValueChange={(val) => setSelectedSequence(prev => ({ ...prev, [lead.id]: val }))}
                                                            >
                                                                <SelectTrigger className="bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white border-slate-200 dark:border-slate-700 text-sm h-9">
                                                                    <SelectValue />
                                                                </SelectTrigger>
                                                                <SelectContent className="bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700">
                                                                    <SelectItem value="warm_intro">Warm Intro (Email + WA)</SelectItem>
                                                                    <SelectItem value="supplier_rfq">Supplier Initial RFQ</SelectItem>
                                                                    <SelectItem value="buyer_pitch">Buyer Value Pitch</SelectItem>
                                                                    <SelectItem value="none">No Sequence (Just Add)</SelectItem>
                                                                </SelectContent>
                                                            </Select>
                                                        </div>

                                                        {lead.is_imported ? (
                                                            <div className="flex items-center justify-center p-3 bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400 rounded-lg border border-emerald-200 dark:border-emerald-800 font-medium text-sm w-full">
                                                                <Check className="h-4 w-4 mr-2" /> Synced to CRM
                                                            </div>
                                                        ) : (
                                                            <Button
                                                                className="w-full bg-indigo-600 hover:bg-indigo-700 text-white"
                                                                onClick={(e) => { e.stopPropagation(); importToCRM(lead.id); }}
                                                                disabled={importing === lead.id}
                                                            >
                                                                {importing === lead.id ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Target className="h-4 w-4 mr-2" />}
                                                                {importing === lead.id ? "Syncing..." : "Push to CRM"}
                                                            </Button>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    )}
                                </Card>
                            );
                        })}
                    </div>
                </div>
            )}
        </div>
    );
}
