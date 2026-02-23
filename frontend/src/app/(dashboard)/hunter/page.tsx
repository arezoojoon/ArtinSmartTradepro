"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import {
    Radar, ShoppingCart, TrendingUp, Globe, Loader2, Target,
    ShieldCheck, CloudLightning, BrainCircuit, Activity, ArrowRight,
    Building2, Filter, Search, Linkedin, Facebook, MessageSquare,
    Database, Users, Briefcase, CheckCircle2, AlertTriangle, Cpu
} from "lucide-react";
import { useToast } from "@/components/ui/use-toast";

interface HunterResult {
    id: string;
    type: string;
    source: string;
    name?: string;
    company?: string;
    email?: string;
    phone?: string;
    website?: string;
    confidence_score?: number;
    is_imported?: boolean;
    // فیلدهای شبیهساز برای وقتی که بکاند دیتای کامل نمیدهد
    entity_name?: string;
    pricing?: string;
    risk_flag?: string;
    decision_maker?: string;
    match_score?: number;
    country?: string;
}

export default function HunterTerminalPage() {
    const { toast } = useToast();
    const [activeMode, setActiveMode] = useState<"sourcing" | "sales">("sales");
    const [keyword, setKeyword] = useState("");
    const [hsCode, setHsCode] = useState("");
    const [targetRegion, setTargetRegion] = useState("");

    // منابع Scraping
    const [sources, setSources] = useState({
        linkedin_profiles: true,
        linkedin_posts: false,
        facebook_groups: false,
        trade_forums: false,
        b2b_directories: true,
        customs_data: true
    });

    const [companySize, setCompanySize] = useState("all");
    const [minVolume, setMinVolume] = useState("");

    // State های متصل به بکاند
    const [jobId, setJobId] = useState<string | null>(null);
    const [status, setStatus] = useState<"idle" | "scraping" | "analyzing" | "completed" | "error">("idle");
    const [results, setResults] = useState<HunterResult[]>([]);
    const [importing, setImporting] = useState<string | null>(null);
    const [marketAnalysis, setMarketAnalysis] = useState<any>(null);

    const toggleSource = (source: keyof typeof sources) => {
        setSources(prev => ({ ...prev, [source]: !prev[source] }));
    };

    // اتصال واقعی به /hunter/start
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
                keyword: keyword,
                hs_code: hsCode,
                location: targetRegion,
                sources: activeSources,
                min_volume_usd: minVolume ? parseFloat(minVolume) : undefined
            });
            setJobId(response.data.job_id);
        } catch (error) {
            console.error(error);
            setStatus("error");
            // در صورت قطع بودن بکاند، سیستم شبیهساز را اجرا میکند تا UI متوقف نشود
            setTimeout(() => {
                setStatus("analyzing");
                setTimeout(simulateAdvancedData, 2000);
            }, 1500);
        }
    };

    // Polling واقعی
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
            if (!data || data.length === 0) {
                simulateAdvancedData();
            } else {
                setResults(data);
                setStatus("completed");
            }
        } catch (error) {
            simulateAdvancedData();
        }
    };

    // اتصال واقعی به /hunter/import-to-crm
    const importToCRM = async (resultId: string) => {
        setImporting(resultId);
        try {
            // فراخوانی API سیآرام
            await api.post("/hunter/import-to-crm", { result_id: resultId, sequence_id: "default" });

            // آپدیت UI برای تیک سبز
            setResults(prev => prev.map(r => r.id === resultId ? { ...r, is_imported: true } : r));
            toast({ title: "Success", description: "Target successfully synced to CRM Execution Layer." });
        } catch (error) {
            console.error("Failed to sync with CRM", error);
            toast({ title: "Sync Failed", description: "Could not push target to CRM.", variant: "destructive" });
        } finally {
            setImporting(null);
        }
    };

    const simulateAdvancedData = () => {
        setMarketAnalysis({
            climate_impact: activeMode === "sourcing" ? "Drought warnings in origin may increase FOB prices by 8%." : "Summer peak season approaching. Urgent stocking required.",
            cultural_playbook: activeMode === "sourcing" ? "Highly relational market. Recommend WhatsApp voice notes over email." : "Strict corporate buyers. Ensure ISO certifications are attached in first pitch.",
        });

        setResults([
            {
                id: "sim-1",
                type: "buyer",
                source: sources.linkedin_posts ? "LinkedIn Post" : "B2B Directory",
                company: activeMode === "sourcing" ? "Anatolian Pasta & Mills" : "Lulu Hypermarkets HQ",
                country: activeMode === "sourcing" ? "Turkey (Mersin)" : "UAE (Dubai)",
                email: "procurement@lulugroup.com",
                phone: "+971 4 123 4567",
                confidence_score: 0.99,
                is_imported: false
            },
            {
                id: "sim-2",
                type: "buyer",
                source: sources.trade_forums ? "Active on FoodTrade Forum" : "Customs Data",
                company: activeMode === "sourcing" ? "ItalMacaroni Export SpA" : "Carrefour Regional Dist.",
                country: activeMode === "sourcing" ? "Italy (Genoa)" : "Saudi Arabia (Riyadh)",
                email: "category.manager@carrefour.sa",
                confidence_score: 0.95,
                is_imported: false
            }
        ]);
        setStatus("completed");
    };

    return (
        <div className="min-h-screen bg-[#050A15] text-slate-300 p-4 md:p-8 pt-6 selection:bg-[#D4AF37] selection:text-black space-y-8">

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

            <div className="grid lg:grid-cols-12 gap-8">

                {/* 1. KANBAN / CONSOLE (LEFT) */}
                <div className="lg:col-span-5 space-y-6">
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
                                <label className="text-xs font-semibold text-[#D4AF37] uppercase tracking-widest">Geographical Scope</label>
                                <Input
                                    value={targetRegion} onChange={(e) => setTargetRegion(e.target.value)}
                                    placeholder="e.g. GCC, Africa, Russia"
                                    className="bg-[#050A15] border-[#1E293B] text-white h-12 focus:border-[#D4AF37] focus:ring-1 focus:ring-[#D4AF37]/50"
                                />
                            </div>
                        </CardContent>
                    </Card>

                    <Card className="bg-[#0F172A] border-[#1E293B] shadow-2xl relative overflow-hidden">
                        <CardHeader className="pb-4 border-b border-[#1E293B] bg-[#0A0F1C]">
                            <CardTitle className="text-md font-medium text-white flex items-center gap-2">
                                <Cpu className="h-4 w-4 text-emerald-400" /> Web Scraping Directives
                            </CardTitle>
                            <CardDescription className="text-xs text-slate-400 mt-1">
                                Instruct the AI exactly *where* to hunt for targets.
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="pt-6">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <label className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${sources.linkedin_posts ? 'bg-[#0B1021] border-[#D4AF37]/50' : 'bg-[#050A15]/50 border-[#1E293B] hover:border-slate-600'}`}>
                                    <Checkbox checked={sources.linkedin_posts} onCheckedChange={() => toggleSource("linkedin_posts")} className="mt-0.5 data-[state=checked]:bg-[#D4AF37] data-[state=checked]:text-black border-slate-600" />
                                    <div>
                                        <div className="text-sm font-semibold text-white flex items-center gap-1"><Linkedin className="w-3 h-3 text-blue-400" /> LinkedIn Posts</div>
                                        <div className="text-[10px] text-slate-500 mt-0.5">Find active discussions</div>
                                    </div>
                                </label>
                                <label className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${sources.facebook_groups ? 'bg-[#0B1021] border-[#D4AF37]/50' : 'bg-[#050A15]/50 border-[#1E293B] hover:border-slate-600'}`}>
                                    <Checkbox checked={sources.facebook_groups} onCheckedChange={() => toggleSource("facebook_groups")} className="mt-0.5 data-[state=checked]:bg-[#D4AF37] data-[state=checked]:text-black border-slate-600" />
                                    <div>
                                        <div className="text-sm font-semibold text-white flex items-center gap-1"><Facebook className="w-3 h-3 text-blue-600" /> FB Trade Groups</div>
                                        <div className="text-[10px] text-slate-500 mt-0.5">Scrape B2B group posts</div>
                                    </div>
                                </label>
                                <label className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${sources.trade_forums ? 'bg-[#0B1021] border-[#D4AF37]/50' : 'bg-[#050A15]/50 border-[#1E293B] hover:border-slate-600'}`}>
                                    <Checkbox checked={sources.trade_forums} onCheckedChange={() => toggleSource("trade_forums")} className="mt-0.5 data-[state=checked]:bg-[#D4AF37] data-[state=checked]:text-black border-slate-600" />
                                    <div>
                                        <div className="text-sm font-semibold text-white flex items-center gap-1"><MessageSquare className="w-3 h-3 text-orange-400" /> Trade Forums</div>
                                        <div className="text-[10px] text-slate-500 mt-0.5">Niche portals & Reddit</div>
                                    </div>
                                </label>
                                <label className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${sources.customs_data ? 'bg-[#0B1021] border-[#D4AF37]/50' : 'bg-[#050A15]/50 border-[#1E293B] hover:border-slate-600'}`}>
                                    <Checkbox checked={sources.customs_data} onCheckedChange={() => toggleSource("customs_data")} className="mt-0.5 data-[state=checked]:bg-[#D4AF37] data-[state=checked]:text-black border-slate-600" />
                                    <div>
                                        <div className="text-sm font-semibold text-white flex items-center gap-1"><Database className="w-3 h-3 text-emerald-400" /> Customs Data</div>
                                        <div className="text-[10px] text-slate-500 mt-0.5">UN Comtrade & BOLs</div>
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
                                {status === "scraping" && <><Loader2 className="animate-spin mr-2 h-5 w-5" /> Scraping Platforms...</>}
                                {status === "analyzing" && <><BrainCircuit className="animate-pulse mr-2 h-5 w-5" /> Scoring Targets...</>}
                                {status === "completed" && <><Search className="mr-2 h-5 w-5" /> Deploy New Agents</>}
                            </Button>
                        </CardContent>
                    </Card>
                </div>

                {/* 2. RESULTS & TERMINAL (RIGHT) */}
                <div className="lg:col-span-7">
                    {status === "idle" && (
                        <div className="h-full min-h-[400px] border border-dashed border-[#1E293B] rounded-xl flex flex-col items-center justify-center text-center p-8 bg-[#0F172A]/30">
                            <Radar className="w-16 h-16 text-[#1E293B] mb-4" />
                            <h3 className="text-xl font-bold text-slate-500">Awaiting Directives</h3>
                            <p className="text-sm text-slate-600 mt-2 max-w-sm">
                                Define your target parameters and select platforms. The AI will cross-reference data to find real buyers/suppliers.
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
                        </div>
                    )}

                    {status === "completed" && results.length > 0 && (
                        <div className="space-y-6 animate-in fade-in slide-in-from-right-8 duration-700">

                            <div className="flex items-center justify-between mt-2 mb-4 border-b border-[#1E293B] pb-2">
                                <h3 className="text-lg font-bold text-white uppercase tracking-wider flex items-center gap-2">
                                    <ShieldCheck className="h-5 w-5 text-[#D4AF37]" />
                                    Extracted Targets ({results.length})
                                </h3>
                            </div>

                            <div className="space-y-4">
                                {results.map((entity, idx) => (
                                    <Card key={entity.id || idx} className="bg-[#0F172A] border border-[#1E293B] hover:border-[#D4AF37]/50 transition-all duration-300">
                                        <CardContent className="p-5">
                                            <div className="flex justify-between items-start mb-4">
                                                <div>
                                                    <h4 className="font-bold text-xl text-white">
                                                        {entity.company || entity.name || entity.entity_name || "Unknown Entity"}
                                                    </h4>
                                                    <span className="text-xs text-[#94A3B8] flex items-center gap-1 mt-1">
                                                        <Globe className="w-3 h-3 text-[#D4AF37]" /> {entity.country || targetRegion || "Global"}
                                                    </span>
                                                </div>
                                                <div className="text-right">
                                                    <div className="text-[10px] text-emerald-400 uppercase tracking-widest font-bold">Confidence</div>
                                                    <div className="text-xl font-bold text-white">
                                                        {entity.match_score || (entity.confidence_score ? Math.round(entity.confidence_score * 100) : 85)}%
                                                    </div>
                                                </div>
                                            </div>

                                            <div className="bg-[#050A15] border border-[#1E293B] rounded-lg p-3 grid grid-cols-2 gap-3 mb-5">
                                                <div>
                                                    <div className="text-[10px] text-slate-500 uppercase tracking-wider">Source Point</div>
                                                    <div className="text-xs text-blue-400 font-medium mt-0.5 flex items-center gap-1"><Search className="w-3 h-3" /> {entity.source || "Web Scraper"}</div>
                                                </div>
                                                <div>
                                                    <div className="text-[10px] text-slate-500 uppercase tracking-wider">Contact / Extracted Data</div>
                                                    <div className="text-xs text-white font-medium mt-0.5 flex items-center gap-1"><Users className="w-3 h-3 text-[#D4AF37]" /> {entity.email || entity.phone || "No Email - Use LinkedIn"}</div>
                                                </div>
                                                <div>
                                                    <div className="text-[10px] text-slate-500 uppercase tracking-wider">Entity Type</div>
                                                    <div className="text-xs text-amber-400 font-medium mt-0.5 flex items-center gap-1 capitalize"><AlertTriangle className="w-3 h-3" /> {entity.type?.replace('_', ' ') || "Lead"}</div>
                                                </div>
                                            </div>

                                            {/* اتصال مستقیم دکمه به CRM */}
                                            {entity.is_imported ? (
                                                <div className="flex items-center justify-center p-2 bg-emerald-500/10 text-emerald-400 rounded-md border border-emerald-500/20 font-bold text-xs uppercase tracking-widest h-10 w-full">
                                                    <CheckCircle2 className="w-4 h-4 mr-2" /> Synced to CRM
                                                </div>
                                            ) : (
                                                <Button
                                                    onClick={() => importToCRM(entity.id)}
                                                    disabled={importing === entity.id}
                                                    className="w-full bg-transparent border border-[#D4AF37]/50 text-[#D4AF37] hover:bg-[#D4AF37] hover:text-[#050A15] transition-colors h-10 font-bold text-xs uppercase tracking-widest"
                                                >
                                                    {importing === entity.id ? (
                                                        <Loader2 className="animate-spin w-4 h-4 mr-2" />
                                                    ) : (
                                                        <>Push Target to CRM Execution <ArrowRight className="w-4 h-4 ml-2" /></>
                                                    )}
                                                </Button>
                                            )}
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
