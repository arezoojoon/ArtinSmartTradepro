"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
    Globe, Loader2, Target, Radar, ShoppingCart, TrendingUp,
    ShieldCheck, Cpu, Zap, Database, Filter, ChevronDown, CheckCircle2
} from "lucide-react";

export default function HunterPage() {
    const [status, setStatus] = useState<"idle" | "scanning" | "analyzing" | "completed">("idle");
    const [activeMode, setActiveMode] = useState<"sourcing" | "sales">("sourcing");

    const startDeepScan = () => {
        setStatus("scanning");
        setTimeout(() => setStatus("analyzing"), 2000);
        setTimeout(() => setStatus("completed"), 4500);
    };

    return (
        <div className="space-y-8 max-w-[1400px] mx-auto p-4 md:p-8 pt-6 min-h-screen">
            {/* Header Section */}
            <div className="flex flex-col md:flex-row md:justify-between md:items-end gap-6 border-b border-white/10 pb-6">
                <div>
                    <div className="flex items-center gap-3 mb-2">
                        <div className="p-2 bg-[#D4AF37]/10 rounded-lg border border-[#D4AF37]/20 backdrop-blur-md">
                            <Radar className="h-6 w-6 text-[#D4AF37]" />
                        </div>
                        <h2 className="text-3xl font-bold tracking-tight text-white">Hunter Engine</h2>
                    </div>
                    <p className="text-slate-400 text-sm">Advanced AI-driven lead generation and market intelligence terminal.</p>
                </div>

                <div className="flex items-center gap-3 bg-black/40 backdrop-blur-md px-4 py-2 rounded-lg border border-white/5">
                    <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></div>
                    <span className="text-xs font-medium text-slate-300 uppercase tracking-widest">System Status: Optimal</span>
                </div>
            </div>

            {/* Premium Mode Toggle (Glassmorphism) */}
            <div className="flex p-1 bg-black/40 backdrop-blur-xl border border-white/10 rounded-xl w-full max-w-md mx-auto relative overflow-hidden">
                <button
                    onClick={() => { setActiveMode("sourcing"); setStatus("idle"); }}
                    className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-lg text-sm font-bold transition-all duration-300 z-10 ${activeMode === "sourcing"
                            ? "bg-[#D4AF37] text-black shadow-[0_0_20px_rgba(212,175,55,0.4)]"
                            : "text-slate-400 hover:text-white"
                        }`}
                >
                    <ShoppingCart className="w-4 h-4" /> Global Sourcing
                </button>
                <button
                    onClick={() => { setActiveMode("sales"); setStatus("idle"); }}
                    className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-lg text-sm font-bold transition-all duration-300 z-10 ${activeMode === "sales"
                            ? "bg-[#D4AF37] text-black shadow-[0_0_20px_rgba(212,175,55,0.4)]"
                            : "text-slate-400 hover:text-white"
                        }`}
                >
                    <TrendingUp className="w-4 h-4" /> B2B Sales
                </button>
            </div>

            {/* Query Builder Form (Advanced Terminal Look) */}
            <Card className="bg-black/40 backdrop-blur-2xl border border-white/10 shadow-2xl overflow-hidden">
                {/* Decorative glowing top line */}
                <div className="h-[2px] w-full bg-gradient-to-r from-transparent via-[#D4AF37] to-transparent opacity-50"></div>

                <CardHeader className="pb-4">
                    <CardTitle className="text-lg font-medium text-white flex items-center gap-2">
                        <Filter className="h-4 w-4 text-[#D4AF37]" />
                        {activeMode === "sourcing" ? "Target Supplier Parameters" : "Target Buyer Parameters"}
                    </CardTitle>
                </CardHeader>

                <CardContent className="space-y-6">
                    <div className="grid md:grid-cols-3 gap-6">
                        <div className="space-y-2">
                            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Commodity / HS Code</label>
                            <Input
                                defaultValue={activeMode === "sourcing" ? "1001.99 - Wheat" : "1902.19 - Pasta"}
                                className="bg-black/50 border-white/10 text-white focus:border-[#D4AF37] focus:ring-1 focus:ring-[#D4AF37]/50 h-11"
                            />
                        </div>
                        <div className="space-y-2">
                            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Target Geographies</label>
                            <Input
                                defaultValue={activeMode === "sourcing" ? "CIS, Russia, Ukraine" : "GCC, North Africa"}
                                className="bg-black/50 border-white/10 text-white focus:border-[#D4AF37] focus:ring-1 focus:ring-[#D4AF37]/50 h-11"
                            />
                        </div>
                        <div className="space-y-2">
                            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                                {activeMode === "sourcing" ? "Required Certifications" : "Buyer Persona"}
                            </label>
                            <Select defaultValue="all">
                                <SelectTrigger className="bg-black/50 border-white/10 text-white h-11 focus:border-[#D4AF37]">
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent className="bg-slate-900 border-white/10 text-white">
                                    {activeMode === "sourcing" ? (
                                        <>
                                            <SelectItem value="all">Any Commercial Standard</SelectItem>
                                            <SelectItem value="iso">ISO 9001 / 22000</SelectItem>
                                            <SelectItem value="halal">Halal Certified</SelectItem>
                                        </>
                                    ) : (
                                        <>
                                            <SelectItem value="all">All Buyer Types</SelectItem>
                                            <SelectItem value="retail">Supermarket Chains</SelectItem>
                                            <SelectItem value="distributor">Wholesale Distributors</SelectItem>
                                        </>
                                    )}
                                </SelectContent>
                            </Select>
                        </div>
                    </div>

                    {/* Data Sources Indicators */}
                    <div className="pt-4 border-t border-white/5 flex flex-wrap items-center gap-4">
                        <span className="text-xs text-slate-500 font-medium">Cross-referencing databases:</span>
                        <Badge variant="outline" className="bg-white/5 border-white/10 text-slate-300 py-1"><Database className="w-3 h-3 mr-1" /> UN Comtrade</Badge>
                        <Badge variant="outline" className="bg-white/5 border-white/10 text-slate-300 py-1"><Globe className="w-3 h-3 mr-1" /> TradeMap</Badge>
                        <Badge variant="outline" className="bg-white/5 border-white/10 text-slate-300 py-1"><Database className="w-3 h-3 mr-1" /> Global Customs Data</Badge>
                    </div>

                    {/* Action Button */}
                    <Button
                        onClick={startDeepScan}
                        disabled={status !== "idle"}
                        className={`w-full h-14 text-base font-bold transition-all duration-500 ${status !== "idle"
                                ? "bg-[#D4AF37]/20 text-[#D4AF37] border border-[#D4AF37]/30"
                                : "bg-[#D4AF37] text-black hover:bg-[#F3E5AB] hover:shadow-[0_0_30px_rgba(212,175,55,0.5)]"
                            }`}
                    >
                        {status === "idle" && <><Zap className="mr-2 h-5 w-5" /> Initialize Deep Web Scan</>}
                        {status === "scanning" && <><Loader2 className="animate-spin mr-2 h-5 w-5" /> Scraping Global Trade Registries...</>}
                        {status === "analyzing" && <><Cpu className="animate-spin mr-2 h-5 w-5" /> AI Validating Entities & Signals...</>}
                    </Button>
                </CardContent>
            </Card>

            {/* Results Section */}
            {status === "completed" && (
                <div className="space-y-6 animate-in fade-in slide-in-from-bottom-8 duration-700">
                    <div className="flex items-center justify-between">
                        <h3 className="text-xl font-semibold text-white flex items-center gap-2">
                            <Target className="h-5 w-5 text-[#D4AF37]" />
                            {activeMode === "sourcing" ? "Verified Suppliers Found" : "Qualified Buyers Found"}
                            <span className="text-sm font-normal text-slate-400 ml-2">(Top Matches)</span>
                        </h3>
                    </div>

                    <div className="grid lg:grid-cols-2 gap-6">

                        {/* Result Card 1 */}
                        <Card className="bg-black/40 backdrop-blur-xl border border-white/10 hover:border-[#D4AF37]/50 transition-all duration-300 group overflow-hidden relative">
                            {/* Glow Effect */}
                            <div className="absolute top-0 right-0 w-64 h-64 bg-[#D4AF37]/5 rounded-full blur-3xl -mr-20 -mt-20 transition-opacity opacity-0 group-hover:opacity-100"></div>

                            <CardContent className="p-6 relative z-10">
                                <div className="flex justify-between items-start mb-6">
                                    <div className="flex gap-4">
                                        <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-slate-800 to-slate-900 border border-white/10 flex items-center justify-center font-bold text-2xl text-white shadow-inner">
                                            A
                                        </div>
                                        <div>
                                            <h4 className="font-bold text-xl text-white group-hover:text-[#D4AF37] transition-colors">
                                                {activeMode === "sourcing" ? "AgroExport Russia LLC" : "Al Maya Group Supermarkets"}
                                            </h4>
                                            <p className="text-sm text-slate-400 mt-1 flex items-center gap-2">
                                                <Globe className="w-3 h-3 text-[#D4AF37]" />
                                                {activeMode === "sourcing" ? "Novorossiysk, RU" : "Dubai, UAE"}
                                            </p>
                                        </div>
                                    </div>
                                    <div className="flex flex-col items-end">
                                        <span className="text-[10px] uppercase tracking-widest text-slate-500 mb-1">Match Score</span>
                                        <div className="text-xl font-bold text-[#D4AF37] flex items-center gap-1">
                                            98.5% <Cpu className="w-4 h-4 opacity-50" />
                                        </div>
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-4 mb-6">
                                    <div className="bg-white/5 border border-white/5 rounded-lg p-3">
                                        <div className="text-xs text-slate-500 uppercase tracking-wider mb-1">
                                            {activeMode === "sourcing" ? "Est. FOB Price" : "Import Volume"}
                                        </div>
                                        <div className="text-sm font-semibold text-white">
                                            {activeMode === "sourcing" ? "$210 - $225 / MT" : "High (> 50 Containers/yr)"}
                                        </div>
                                    </div>
                                    <div className="bg-white/5 border border-white/5 rounded-lg p-3">
                                        <div className="text-xs text-slate-500 uppercase tracking-wider mb-1">
                                            {activeMode === "sourcing" ? "Supply Capacity" : "Buyer Segment"}
                                        </div>
                                        <div className="text-sm font-semibold text-white">
                                            {activeMode === "sourcing" ? "50,000 MT / Month" : "Premium Retail Chain"}
                                        </div>
                                    </div>
                                </div>

                                <div className="flex items-center gap-3">
                                    <Button className="flex-1 bg-[#D4AF37] text-black hover:bg-white transition-colors h-11 font-bold">
                                        {activeMode === "sourcing" ? "Draft Auto-RFQ" : "Push to CRM & Pitch"}
                                    </Button>
                                    <Button variant="outline" className="bg-transparent border-white/20 text-white hover:bg-white/10 h-11 px-4">
                                        <ChevronDown className="w-5 h-5" />
                                    </Button>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Result Card 2 */}
                        <Card className="bg-black/40 backdrop-blur-xl border border-white/10 hover:border-[#D4AF37]/50 transition-all duration-300 group overflow-hidden relative">
                            <CardContent className="p-6 relative z-10">
                                <div className="flex justify-between items-start mb-6">
                                    <div className="flex gap-4">
                                        <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-slate-800 to-slate-900 border border-white/10 flex items-center justify-center font-bold text-2xl text-white shadow-inner">
                                            C
                                        </div>
                                        <div>
                                            <h4 className="font-bold text-xl text-white group-hover:text-[#D4AF37] transition-colors">
                                                {activeMode === "sourcing" ? "Caspian Grain Holdco" : "Carrefour Regional Dist."}
                                            </h4>
                                            <p className="text-sm text-slate-400 mt-1 flex items-center gap-2">
                                                <Globe className="w-3 h-3 text-[#D4AF37]" />
                                                {activeMode === "sourcing" ? "Astrakhan, RU" : "Riyadh, KSA"}
                                            </p>
                                        </div>
                                    </div>
                                    <div className="flex flex-col items-end">
                                        <span className="text-[10px] uppercase tracking-widest text-slate-500 mb-1">Match Score</span>
                                        <div className="text-xl font-bold text-white flex items-center gap-1">
                                            92.0% <Cpu className="w-4 h-4 opacity-50" />
                                        </div>
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-4 mb-6">
                                    <div className="bg-white/5 border border-white/5 rounded-lg p-3">
                                        <div className="text-xs text-slate-500 uppercase tracking-wider mb-1">
                                            {activeMode === "sourcing" ? "Est. FOB Price" : "Import Volume"}
                                        </div>
                                        <div className="text-sm font-semibold text-white">
                                            {activeMode === "sourcing" ? "$218 - $230 / MT" : "Massive (> 200 Cont/yr)"}
                                        </div>
                                    </div>
                                    <div className="bg-white/5 border border-white/5 rounded-lg p-3">
                                        <div className="text-xs text-slate-500 uppercase tracking-wider mb-1">
                                            {activeMode === "sourcing" ? "Risk Flag" : "Key Insight"}
                                        </div>
                                        <div className="text-sm font-medium text-amber-400 flex items-center gap-1">
                                            {activeMode === "sourcing" ? "Port Congestion Risk" : <><CheckCircle2 className="w-3 h-3" /> Fast Payer (DSO: 14d)</>}
                                        </div>
                                    </div>
                                </div>

                                <div className="flex items-center gap-3">
                                    <Button className="flex-1 bg-[#D4AF37] text-black hover:bg-white transition-colors h-11 font-bold">
                                        {activeMode === "sourcing" ? "Draft Auto-RFQ" : "Push to CRM & Pitch"}
                                    </Button>
                                    <Button variant="outline" className="bg-transparent border-white/20 text-white hover:bg-white/10 h-11 px-4">
                                        <ChevronDown className="w-5 h-5" />
                                    </Button>
                                </div>
                            </CardContent>
                        </Card>

                    </div>
                </div>
            )}
        </div>
    );
}
