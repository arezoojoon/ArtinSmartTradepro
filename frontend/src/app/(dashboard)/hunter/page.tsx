"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import {
    Radar, ShoppingCart, TrendingUp, Globe, Loader2, Target,
    ShieldCheck, CloudLightning, BrainCircuit, Activity, ArrowRight,
    Scale, AlertTriangle, Building2, Landmark, Filter, Search,
    Linkedin, Facebook, MessageSquare, Database, Users, Briefcase
} from "lucide-react";
import { useToast } from "@/components/ui/use-toast";

export default function HunterTerminalPage() {
    const { toast } = useToast();
    const [activeMode, setActiveMode] = useState<"sourcing" | "sales">("sales");
    const [keyword, setKeyword] = useState("");
    const [hsCode, setHsCode] = useState("");
    const [targetRegion, setTargetRegion] = useState("");

    // Scraping Sources State
    const [sources, setSources] = useState({
        linkedin_profiles: true,
        linkedin_posts: false,
        facebook_groups: false,
        trade_forums: false,
        b2b_directories: true,
        customs_data: true
    });

    // Filtering State
    const [companySize, setCompanySize] = useState("all");
    const [minVolume, setMinVolume] = useState("");

    const [jobId, setJobId] = useState<string | null>(null);
    const [status, setStatus] = useState<"idle" | "scraping" | "analyzing" | "completed" | "error">("idle");
    const [results, setResults] = useState<any[]>([]);
    const [marketAnalysis, setMarketAnalysis] = useState<any>(null);

    const toggleSource = (source: keyof typeof sources) => {
        setSources(prev => ({ ...prev, [source]: !prev[source] }));
    };

    const runHunterEngine = async () => {
        if (!keyword || !targetRegion) {
            toast({ title: "Command Error", description: "Target Product and Region are mandatory fields.", variant: "destructive" });
            return;
        }

        const activeSources = Object.entries(sources).filter(([_, isActive]) => isActive).map(([key]) => key);

        if (activeSources.length === 0) {
            toast({ title: "Command Error", description: "You must select at least one scraping source.", variant: "destructive" });
            return;
        }

        setStatus("scraping");
        setResults([]);

        try {
            const response = await api.post("/hunter/start", {
                keyword,
                hs_code: hsCode,
                location: targetRegion,
                sources: activeSources,
                mode: activeMode,
                filters: {
                    company_size: companySize,
                    min_volume: minVolume
                }
            });
            setJobId(response.data.job_id);
        } catch (error) {
            console.error(error);
            setStatus("error");
            // Simulation logic
            setTimeout(() => {
                setStatus("analyzing");
                setTimeout(simulateAdvancedData, 2000);
            }, 1500);
        }
    };

    useEffect(() => {
        if (!jobId || status === "completed" || status === "error") return;
        const interval = setInterval(async () => {
            try {
                const { data } = await api.get(`/hunter/status/${jobId}`);
                if (data.job_status === "completed") {
                    clearInterval(interval);
                    setStatus("analyzing");
                    fetchFinalIntelligence(jobId);
                } else if (data.job_status === "failed") {
                    clearInterval(interval);
                    setStatus("error");
                }
            } catch (error) {
                console.error("Polling error", error);
            }
        }, 3000);
        return () => clearInterval(interval);
    }, [jobId, status]);

    const fetchFinalIntelligence = async (id: string) => {
        try {
            const { data } = await api.get(`/hunter/results/${id}`);
            if (!data || data.length === 0) simulateAdvancedData();
            else { setResults(data); setStatus("completed"); }
        } catch (error) {
            simulateAdvancedData();
        }
    };

    const simulateAdvancedData = () => {
        setMarketAnalysis({
            climate_impact: activeMode === "sourcing" ? "Drought warnings in origin may increase FOB prices by 8%." : "Summer peak season approaching. Urgent stocking required.",
            cultural_playbook: activeMode === "sourcing" ? "Highly relational market. Recommend WhatsApp voice notes over email." : "Strict corporate buyers. Ensure ISO certifications are attached in first pitch.",
            arbitrage_score: 94,
            est_margin: "22% - 28%"
        });

        setResults([
            {
                id: "1",
                entity_name: activeMode === "sourcing" ? "Anatolian Pasta & Mills" : "Lulu Hypermarkets HQ",
                country: activeMode === "sourcing" ? "Turkey (Mersin)" : "UAE (Dubai)",
                pricing: activeMode === "sourcing" ? "FOB $520/MT" : "Target CIF: $680/MT",
                reliability: 96,
                payment_term: activeMode === "sourcing" ? "30% Advance, 70% BL" : "OA 60 Days",
                source_found: sources.linkedin_posts ? "LinkedIn Post (Searching for suppliers)" : "B2B Directory",
                risk_flag: "Verified Entity",
                match_score: 99.1,
                decision_maker: "Procurement Director (Found via LinkedIn)"
            },
            {
                id: "2",
                entity_name: activeMode === "sourcing" ? "ItalMacaroni Export SpA" : "Carrefour Regional Dist.",
                country: activeMode === "sourcing" ? "Italy (Genoa)" : "Saudi Arabia (Riyadh)",
                pricing: activeMode === "sourcing" ? "FOB $610/MT" : "Target CIF: $750/MT",
                reliability: 98,
                payment_term: "100% LC at sight",
                source_found: sources.trade_forums ? "Active on FoodTrade Forum" : "Customs Data (Comtrade)",
                risk_flag: "High Quality Stringency",
                match_score: 95.4,
                decision_maker: "Category Manager (Found via Web Scraping)"
            }
        ]);
        setStatus("completed");
    };

    return (
        <div className="min-h-screen bg-[#050A15] text-slate-300 p-4 md:p-8 pt-6 selection:bg-[#D4AF37] selection:text-black space-y-8">

            {/* Header */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4 border-b border-[#1E293B] pb-6">
                <div>
                    <div className="flex items-center gap-3 mb-2">
                        <div className="p-2 bg-[#D4AF37]/10 rounded-md border border-[#D4AF37]/30 shadow-[0_0_15px_rgba(212,175,55,0.15)]">
                            <Radar className="h-6 w-6 text-[#D4AF37]" />
                        </div>
                        <h1 className="text-3xl font-bold tracking-tight text-white uppercase">Hunter Control Tower</h1>
                    </div>
                    <p className="text-[#94A3B8] text-sm flex items-center gap-2">
                        <Activity className="w-4 h-4 text-emerald-400" />
                        Configure deep-web scraping directives and analytical engines.
                    </p>
                </div>
            </div>

            {/* Main Layout Grid */}
            <div className="grid lg:grid-cols-12 gap-8">

                {/* LEFT PANEL: CONFIGURATION */}
                <div className="lg:col-span-5 space-y-6">

                    {/* Strategy Mode */}
                    <div className="flex p-1 bg-[#0F172A] border border-[#1E293B] rounded-lg w-full relative">
                        <button
                            onClick={() => { setActiveMode("sourcing"); setStatus("idle"); setResults([]); }}
                            className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-md text-sm font-bold transition-all z-10 ${activeMode === "sourcing" ? "bg-[#D4AF37] text-[#050A15] shadow-[0_0_15px_rgba(212,175,55,0.4)]" : "text-[#94A3B8] hover:text-white"
                                }`}
                        >
                            <ShoppingCart className="w-4 h-4" /> FIND SUPPLIERS (Buy)
                        </button>
                        <button
                            onClick={() => { setActiveMode("sales"); setStatus("idle"); setResults([]); }}
                            className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-md text-sm font-bold transition-all z-10 ${activeMode === "sales" ? "bg-[#D4AF37] text-[#050A15] shadow-[0_0_15px_rgba(212,175,55,0.4)]" : "text-[#94A3B8] hover:text-white"
                                }`}
                        >
                            <TrendingUp className="w-4 h-4" /> FIND BUYERS (Sell)
                        </button>
                    </div>

                    <Card className="bg-[#0F172A] border-[#1E293B] shadow-2xl relative overflow-hidden">
                        <div className="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-transparent via-[#D4AF37] to-transparent opacity-70"></div>
                        <CardHeader className="pb-4 border-b border-[#1E293B]">
                            <CardTitle className="text-lg font-medium text-white flex items-center gap-2">
                                <Target className="h-5 w-5 text-[#D4AF37]" /> Core Target Parameters
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="pt-6 space-y-5">
                            <div className="space-y-2">
                                <label className="text-xs font-semibold text-[#D4AF37] uppercase tracking-widest">Product & HS Code</label>
                                <Input
                                    value={keyword} onChange={(e) => setKeyword(e.target.value)}
                                    placeholder="e.g. Pasta / Macaroni (1902.19)"
                                    className="bg-[#050A15] border-[#1E293B] text-white h-12 focus:border-[#D4AF37] focus:ring-1 focus:ring-[#D4AF37]/50"
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-xs font-semibold text-[#D4AF37] uppercase tracking-widest">Geographical Scope (Target Region)</label>
                                <Input
                                    value={targetRegion} onChange={(e) => setTargetRegion(e.target.value)}
                                    placeholder="e.g. GCC, Africa, Russia, Global"
                                    className="bg-[#050A15] border-[#1E293B] text-white h-12 focus:border-[#D4AF37] focus:ring-1 focus:ring-[#D4AF37]/50"
                                />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <label className="text-xs font-semibold text-[#94A3B8] uppercase">Company Size</label>
                                    <Select value={companySize} onValueChange={setCompanySize}>
                                        <SelectTrigger className="bg-[#050A15] border-[#1E293B] text-white focus:border-[#D4AF37]">
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent className="bg-[#0F172A] border-[#1E293B] text-white">
                                            <SelectItem value="all">Any Size</SelectItem>
                                            <SelectItem value="enterprise">Enterprise (Tier 1)</SelectItem>
                                            <SelectItem value="sme">SME & Distributors</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                                <div className="space-y-2">
                                    <label className="text-xs font-semibold text-[#94A3B8] uppercase">Min. Volume/Cap</label>
                                    <Input
                                        value={minVolume} onChange={(e) => setMinVolume(e.target.value)}
                                        placeholder="e.g. 50 MT/mo"
                                        className="bg-[#050A15] border-[#1E293B] text-white focus:border-[#D4AF37]"
                                    />
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Scraping Directives */}
                    <Card className="bg-[#0F172A] border-[#1E293B] shadow-2xl relative overflow-hidden">
                        <CardHeader className="pb-4 border-b border-[#1E293B] bg-[#0A0F1C]">
                            <CardTitle className="text-md font-medium text-white flex items-center gap-2">
                                <Cpu className="h-4 w-4 text-emerald-400" /> Web Scraping Directives
                            </CardTitle>
                            <CardDescription className="text-xs text-slate-400 mt-1">
                                Instruct the AI on exactly *where* to hunt for signals.
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="pt-6">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <label className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${sources.linkedin_posts ? 'bg-[#0B1021] border-[#D4AF37]/50' : 'bg-[#050A15]/50 border-[#1E293B] hover:border-slate-600'}`}>
                                    <Checkbox checked={sources.linkedin_posts} onCheckedChange={() => toggleSource("linkedin_posts")} className="mt-0.5 data-[state=checked]:bg-[#D4AF37] data-[state=checked]:text-black border-slate-600" />
                                    <div>
                                        <div className="text-sm font-semibold text-white flex items-center gap-1"><Linkedin className="w-3 h-3 text-blue-400" /> LinkedIn Posts</div>
                                        <div className="text-[10px] text-slate-500 mt-0.5">Find people actively asking/offering</div>
                                    </div>
                                </label>

                                <label className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${sources.linkedin_profiles ? 'bg-[#0B1021] border-[#D4AF37]/50' : 'bg-[#050A15]/50 border-[#1E293B] hover:border-slate-600'}`}>
                                    <Checkbox checked={sources.linkedin_profiles} onCheckedChange={() => toggleSource("linkedin_profiles")} className="mt-0.5 data-[state=checked]:bg-[#D4AF37] data-[state=checked]:text-black border-slate-600" />
                                    <div>
                                        <div className="text-sm font-semibold text-white flex items-center gap-1"><Briefcase className="w-3 h-3 text-blue-400" /> LinkedIn Companies</div>
                                        <div className="text-[10px] text-slate-500 mt-0.5">Target official company pages & employees</div>
                                    </div>
                                </label>

                                <label className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${sources.facebook_groups ? 'bg-[#0B1021] border-[#D4AF37]/50' : 'bg-[#050A15]/50 border-[#1E293B] hover:border-slate-600'}`}>
                                    <Checkbox checked={sources.facebook_groups} onCheckedChange={() => toggleSource("facebook_groups")} className="mt-0.5 data-[state=checked]:bg-[#D4AF37] data-[state=checked]:text-black border-slate-600" />
                                    <div>
                                        <div className="text-sm font-semibold text-white flex items-center gap-1"><Facebook className="w-3 h-3 text-blue-600" /> Facebook Groups</div>
                                        <div className="text-[10px] text-slate-500 mt-0.5">Scrape B2B trade & export groups</div>
                                    </div>
                                </label>

                                <label className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${sources.trade_forums ? 'bg-[#0B1021] border-[#D4AF37]/50' : 'bg-[#050A15]/50 border-[#1E293B] hover:border-slate-600'}`}>
                                    <Checkbox checked={sources.trade_forums} onCheckedChange={() => toggleSource("trade_forums")} className="mt-0.5 data-[state=checked]:bg-[#D4AF37] data-[state=checked]:text-black border-slate-600" />
                                    <div>
                                        <div className="text-sm font-semibold text-white flex items-center gap-1"><MessageSquare className="w-3 h-3 text-orange-400" /> Industry Forums</div>
                                        <div className="text-[10px] text-slate-500 mt-0.5">Specialized niche portals & Reddit</div>
                                    </div>
                                </label>

                                <label className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${sources.b2b_directories ? 'bg-[#0B1021] border-[#D4AF37]/50' : 'bg-[#050A15]/50 border-[#1E293B] hover:border-slate-600'}`}>
                                    <Checkbox checked={sources.b2b_directories} onCheckedChange={() => toggleSource("b2b_directories")} className="mt-0.5 data-[state=checked]:bg-[#D4AF37] data-[state=checked]:text-black border-slate-600" />
                                    <div>
                                        <div className="text-sm font-semibold text-white flex items-center gap-1"><Globe className="w-3 h-3 text-yellow-400" /> B2B Directories</div>
                                        <div className="text-[10px] text-slate-500 mt-0.5">Alibaba, GlobalSources, Kompass</div>
                                    </div>
                                </label>

                                <label className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${sources.customs_data ? 'bg-[#0B1021] border-[#D4AF37]/50' : 'bg-[#050A15]/50 border-[#1E293B] hover:border-slate-600'}`}>
                                    <Checkbox checked={sources.customs_data} onCheckedChange={() => toggleSource("customs_data")} className="mt-0.5 data-[state=checked]:bg-[#D4AF37] data-[state=checked]:text-black border-slate-600" />
                                    <div>
                                        <div className="text-sm font-semibold text-white flex items-center gap-1"><Database className="w-3 h-3 text-emerald-400" /> Official Customs Data</div>
                                        <div className="text-[10px] text-slate-500 mt-0.5">UN Comtrade & Port BOL databases</div>
                                    </div>
                                </label>
                            </div>

                            <Button
                                onClick={runHunterEngine}
                                disabled={status === "scraping" || status === "analyzing"}
                                className={`w-full h-14 mt-6 text-base font-bold uppercase tracking-widest transition-all duration-500 rounded-md border ${status !== "idle" && status !== "completed"
                                        ? "bg-[#D4AF37]/10 text-[#D4AF37] border-[#D4AF37]/30"
                                        : "bg-[#D4AF37] text-[#050A15] border-[#D4AF37] hover:bg-[#F3E5AB] hover:shadow-[0_0_30px_rgba(212,175,55,0.6)]"
                                    }`}
                            >
                                {status === "idle" && <><Search className="mr-2 h-5 w-5" /> Deploy Hunter Agents</>}
                                {status === "scraping" && <><Loader2 className="animate-spin mr-2 h-5 w-5" /> Scraping Selected Platforms...</>}
                                {status === "analyzing" && <><BrainCircuit className="animate-pulse mr-2 h-5 w-5" /> Filtering Noise & Scoring Leads...</>}
                                {status === "completed" && <><Search className="mr-2 h-5 w-5" /> Deploy New Agents</>}
                            </Button>
                        </CardContent>
                    </Card>
                </div>

                {/* RIGHT PANEL: RESULTS & ANALYSIS */}
                <div className="lg:col-span-7">
                    {status === "idle" && (
                        <div className="h-full min-h-[400px] border border-dashed border-[#1E293B] rounded-xl flex flex-col items-center justify-center text-center p-8 bg-[#0F172A]/30">
                            <Radar className="w-16 h-16 text-[#1E293B] mb-4" />
                            <h3 className="text-xl font-bold text-slate-500">Awaiting Directives</h3>
                            <p className="text-sm text-slate-600 mt-2 max-w-sm">
                                Define your target parameters and select the platforms to scrape. The AI will cross-reference data to find high-probability targets.
                            </p>
                        </div>
                    )}

                    {(status === "scraping" || status === "analyzing") && (
                        <div className="h-full min-h-[400px] border border-[#D4AF37]/20 bg-[#D4AF37]/5 rounded-xl flex flex-col items-center justify-center text-center p-8 relative overflow-hidden">
                            <div className="absolute inset-0 bg-gradient-to-t from-[#D4AF37]/10 to-transparent animate-pulse opacity-50"></div>
                            <Activity className="w-16 h-16 text-[#D4AF37] animate-bounce mb-6 relative z-10" />
                            <h3 className="text-2xl font-bold text-white relative z-10 uppercase tracking-widest">
                                {status === "scraping" ? "Active Web Scraping..." : "Executing AI Validation..."}
                            </h3>
                            <div className="w-64 h-1 bg-[#1E293B] rounded-full overflow-hidden mt-6 relative z-10">
                                <div className="h-full bg-[#D4AF37] animate-pulse w-2/3"></div>
                            </div>
                            <div className="flex gap-4 mt-6 text-xs text-slate-400 font-mono relative z-10">
                                {sources.linkedin_posts && <span className="animate-pulse">Scraping LinkedIn Posts...</span>}
                                {sources.facebook_groups && <span className="animate-pulse delay-75">Scanning FB Groups...</span>}
                            </div>
                        </div>
                    )}

                    {status === "completed" && results.length > 0 && (
                        <div className="space-y-6 animate-in fade-in slide-in-from-right-8 duration-700">

                            {/* Strategic Insight Panels */}
                            <div className="grid grid-cols-2 gap-4">
                                <Card className="bg-[#131A2F] border-l-4 border-l-emerald-500 border-y-[#1E293B] border-r-[#1E293B]">
                                    <CardContent className="p-4">
                                        <div className="text-[10px] text-[#94A3B8] uppercase tracking-widest mb-1 flex items-center gap-1"><CloudLightning className="w-3 h-3 text-emerald-400" /> Climate / Seasonality Insight</div>
                                        <div className="text-sm text-white font-medium">{marketAnalysis?.climate_impact}</div>
                                    </CardContent>
                                </Card>
                                <Card className="bg-[#131A2F] border-l-4 border-l-purple-500 border-y-[#1E293B] border-r-[#1E293B]">
                                    <CardContent className="p-4">
                                        <div className="text-[10px] text-[#94A3B8] uppercase tracking-widest mb-1 flex items-center gap-1"><Building2 className="w-3 h-3 text-purple-400" /> Cultural / Negotiation Playbook</div>
                                        <div className="text-sm text-white font-medium">{marketAnalysis?.cultural_playbook}</div>
                                    </CardContent>
                                </Card>
                            </div>

                            {/* Extracted Leads */}
                            <div className="flex items-center justify-between mt-8 mb-4 border-b border-[#1E293B] pb-2">
                                <h3 className="text-lg font-bold text-white uppercase tracking-wider flex items-center gap-2">
                                    <ShieldCheck className="h-5 w-5 text-[#D4AF37]" />
                                    Extracted Targets ({results.length})
                                </h3>
                            </div>

                            <div className="space-y-4">
                                {results.map((entity, idx) => (
                                    <Card key={idx} className="bg-[#0F172A] border border-[#1E293B] hover:border-[#D4AF37]/50 transition-all duration-300">
                                        <CardContent className="p-5">
                                            <div className="flex justify-between items-start mb-4">
                                                <div>
                                                    <h4 className="font-bold text-xl text-white">
                                                        {entity.entity_name}
                                                    </h4>
                                                    <span className="text-xs text-[#94A3B8] flex items-center gap-1 mt-1">
                                                        <Globe className="w-3 h-3 text-[#D4AF37]" /> {entity.country}
                                                    </span>
                                                </div>
                                                <div className="text-right">
                                                    <div className="text-[10px] text-emerald-400 uppercase tracking-widest font-bold">Match Score</div>
                                                    <div className="text-xl font-bold text-white">{entity.match_score}%</div>
                                                </div>
                                            </div>

                                            <div className="bg-[#050A15] border border-[#1E293B] rounded-lg p-3 grid grid-cols-2 gap-3 mb-4">
                                                <div>
                                                    <div className="text-[10px] text-slate-500 uppercase tracking-wider">Source Point</div>
                                                    <div className="text-xs text-blue-400 font-medium mt-0.5 flex items-center gap-1"><Search className="w-3 h-3" /> {entity.source_found}</div>
                                                </div>
                                                <div>
                                                    <div className="text-[10px] text-slate-500 uppercase tracking-wider">Decision Maker</div>
                                                    <div className="text-xs text-white font-medium mt-0.5 flex items-center gap-1"><Users className="w-3 h-3 text-[#D4AF37]" /> {entity.decision_maker}</div>
                                                </div>
                                                <div>
                                                    <div className="text-[10px] text-slate-500 uppercase tracking-wider">{activeMode === "sourcing" ? "Target FOB Price" : "Est. CIF Budget"}</div>
                                                    <div className="text-xs text-white font-medium mt-0.5">{entity.pricing}</div>
                                                </div>
                                                <div>
                                                    <div className="text-[10px] text-slate-500 uppercase tracking-wider">AI Flag</div>
                                                    <div className="text-xs text-amber-400 font-medium mt-0.5 flex items-center gap-1"><AlertTriangle className="w-3 h-3" /> {entity.risk_flag}</div>
                                                </div>
                                            </div>

                                            <Button className="w-full bg-transparent border border-[#D4AF37]/50 text-[#D4AF37] hover:bg-[#D4AF37] hover:text-[#050A15] transition-colors h-9 font-bold text-xs uppercase tracking-widest">
                                                Push Target to CRM Execution <ArrowRight className="w-3 h-3 ml-2" />
                                            </Button>
                                        </CardContent>
                                    </Card>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
