"use client";

import { useState, useEffect } from "react";
import { Search, Loader2, Play, Users, MapPin, Globe, CheckCircle, UploadCloud } from "lucide-react";
import api from "@/lib/api";
import { toast } from "@/components/ui/use-toast";

export default function HunterDashboard() {
    const [keyword, setKeyword] = useState("");
    const [location, setLocation] = useState("");
    const [sources, setSources] = useState(["google_maps"]);
    const [loading, setLoading] = useState(false);
    const [activeJobId, setActiveJobId] = useState<string | null>(null);
    const [jobStatus, setJobStatus] = useState<any>(null);
    const [results, setResults] = useState<any[]>([]);

    useEffect(() => {
        let interval: NodeJS.Timeout;
        if (activeJobId && (!jobStatus || jobStatus.job_status !== "completed")) {
            interval = setInterval(fetchJobStatus, 3000);
        }
        return () => clearInterval(interval);
    }, [activeJobId, jobStatus]);

    useEffect(() => {
        if (jobStatus?.job_status === "completed") {
            fetchResults();
        }
    }, [jobStatus]);

    const startHunt = async () => {
        if (!keyword || !location) return;
        setLoading(true);
        try {
            const { data } = await api.post("/hunter/start", { keyword, location, sources });
            setActiveJobId(data.job_id);
            setJobStatus({ job_status: "pending", leads_found: 0 });
            setResults([]);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const fetchJobStatus = async () => {
        if (!activeJobId) return;
        try {
            const { data } = await api.get(`/hunter/status/${activeJobId}`);
            setJobStatus(data);
        } catch (err) {
            console.error(err);
        }
    };

    const fetchResults = async () => {
        if (!activeJobId) return;
        try {
            const { data } = await api.get(`/hunter/results/${activeJobId}`);
            setResults(data);
        } catch (err) {
            console.error(err);
        }
    };

    const importToCRM = async (resultId: string) => {
        try {
            await api.post("/hunter/import-to-crm", { result_id: resultId });
            toast({ title: "Lead Imported", description: "Lead has been imported to CRM successfully" });
        } catch (err) {
            console.error(err);
        }
    };

    const toggleSource = (source: string) => {
        if (sources.includes(source)) {
            setSources(sources.filter(s => s !== source));
        } else {
            setSources([...sources, source]);
        }
    };

    return (
        <div className="p-6 max-w-7xl mx-auto">
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-3xl font-bold text-white flex items-center gap-3">
                        <Search className="h-8 w-8 text-[#f5a623]" />
                        Lead Hunter
                    </h1>
                    <p className="text-navy-300 mt-2 text-lg">AI-powered B2B lead generation engine</p>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Configuration Panel */}
                <div className="bg-[#0e1e33] border border-navy-700/50 rounded-2xl p-6 shadow-2xl lg:col-span-1">
                    <h2 className="text-xl font-semibold text-white mb-6">Execution Config</h2>

                    <div className="space-y-6">
                        <div>
                            <label className="block text-sm font-medium text-navy-300 mb-2">Search Keyword (Niche/Product)</label>
                            <div className="relative">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-navy-400" />
                                <input
                                    type="text"
                                    value={keyword}
                                    onChange={(e) => setKeyword(e.target.value)}
                                    placeholder="e.g. 'Coffee Importers' or 'Real Estate Agents'"
                                    className="w-full pl-10 pr-4 py-3 bg-navy-950 border border-navy-700 rounded-xl text-white focus:border-gold-400 focus:outline-none focus:ring-1 focus:ring-gold-400 transition-all font-medium"
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-navy-300 mb-2">Location Target</label>
                            <div className="relative">
                                <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-navy-400" />
                                <input
                                    type="text"
                                    value={location}
                                    onChange={(e) => setLocation(e.target.value)}
                                    placeholder="e.g. 'Dubai, UAE' or 'Berlin'"
                                    className="w-full pl-10 pr-4 py-3 bg-navy-950 border border-navy-700 rounded-xl text-white focus:border-gold-400 focus:outline-none focus:ring-1 focus:ring-gold-400 transition-all"
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-navy-300 mb-3">Intelligence Sources</label>
                            <div className="space-y-3">
                                {[
                                    { id: "google_maps", label: "Google Maps" },
                                    { id: "linkedin", label: "LinkedIn Data" },
                                    { id: "un_comtrade", label: "UN Comtrade (Importers)" }
                                ].map(src => (
                                    <label key={src.id} className="flex items-center gap-3 p-3 rounded-xl border border-navy-700 bg-navy-950 hover:border-gold-400/50 cursor-pointer transition-colors">
                                        <input
                                            type="checkbox"
                                            checked={sources.includes(src.id)}
                                            onChange={() => toggleSource(src.id)}
                                            className="w-5 h-5 rounded border-navy-600 text-gold-500 focus:ring-gold-500 bg-navy-800"
                                        />
                                        <span className="text-white text-sm font-medium">{src.label}</span>
                                    </label>
                                ))}
                            </div>
                        </div>

                        <button
                            onClick={startHunt}
                            disabled={loading || !keyword || !location || !!(activeJobId && jobStatus?.job_status !== "completed")}
                            className="w-full py-4 bg-gradient-to-r from-gold-500 to-gold-400 hover:from-gold-400 hover:to-gold-300 text-navy-950 font-bold rounded-xl shadow-[0_0_20px_rgba(250,204,21,0.2)] hover:shadow-[0_0_30px_rgba(250,204,21,0.4)] disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2 text-lg"
                        >
                            {loading ? <Loader2 className="h-6 w-6 animate-spin" /> : <Play className="h-6 w-6 fill-current" />}
                            Execute Hunt
                        </button>
                    </div>
                </div>

                {/* Results Panel */}
                <div className="lg:col-span-2 space-y-6">
                    {/* Status Tracker */}
                    {activeJobId && (
                        <div className="bg-[#0e1e33] border border-navy-700/50 rounded-2xl p-6 shadow-xl flex items-center justify-between">
                            <div className="flex items-center gap-4">
                                {jobStatus?.job_status === "completed" ? (
                                    <div className="bg-green-500/20 p-3 rounded-full text-green-400">
                                        <CheckCircle className="h-8 w-8" />
                                    </div>
                                ) : (
                                    <div className="relative h-14 w-14 flex items-center justify-center">
                                        <div className="absolute inset-0 rounded-full border-4 border-[#1e3a5f]"></div>
                                        <div className="absolute inset-0 rounded-full border-4 border-t-gold-400 animate-spin"></div>
                                        <Search className="h-6 w-6 text-[#f5a623] animate-pulse" />
                                    </div>
                                )}
                                <div>
                                    <h3 className="text-xl font-bold text-white capitalize flex items-center gap-2">
                                        Status: {jobStatus?.job_status || "Initializing"}
                                        {jobStatus?.job_status === "completed" && <span className="text-sm font-normal text-green-400 bg-green-400/10 px-2 py-0.5 rounded-md">100% Complete</span>}
                                    </h3>
                                    <p className="text-navy-300 mt-1 flex items-center gap-2">
                                        <Users className="h-4 w-4" />
                                        {jobStatus?.leads_found || 0} Targets Identified
                                    </p>
                                </div>
                            </div>
                            <div className="text-right">
                                <p className="text-sm text-navy-400 font-mono">Process ID</p>
                                <p className="text-xs text-navy-500 font-mono mt-1">{activeJobId.split("-")[0]}</p>
                            </div>
                        </div>
                    )}

                    {/* Leads Table */}
                    <div className="bg-[#0e1e33] border border-navy-700/50 rounded-2xl shadow-xl overflow-hidden min-h-[400px]">
                        <div className="bg-navy-950 px-6 py-4 border-b border-[#1e3a5f] flex justify-between items-center">
                            <h3 className="text-lg font-bold text-white">Extracted Leads</h3>
                            <span className="text-sm text-navy-400">{results.length} results</span>
                        </div>

                        {results.length === 0 ? (
                            <div className="flex flex-col items-center justify-center h-full min-h-[300px] text-navy-500 space-y-4">
                                <Globe className="h-16 w-16 opacity-20" />
                                <p className="text-lg">Waiting for hunt execution...</p>
                            </div>
                        ) : (
                            <div className="overflow-x-auto">
                                <table className="w-full text-left text-sm whitespace-nowrap">
                                    <thead className="text-navy-400 bg-[#0e1e33]/50">
                                        <tr>
                                            <th className="px-6 py-4 font-semibold text-xs tracking-wider uppercase">Business Name</th>
                                            <th className="px-6 py-4 font-semibold text-xs tracking-wider uppercase">Contact Info</th>
                                            <th className="px-6 py-4 font-semibold text-xs tracking-wider uppercase">Website</th>
                                            <th className="px-6 py-4 font-semibold text-xs tracking-wider uppercase">Source</th>
                                            <th className="px-6 py-4 font-semibold text-xs tracking-wider uppercase text-right">Action</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-navy-800/50">
                                        {results.map((r, idx) => (
                                            <tr key={idx} className="hover:bg-navy-800/30 transition-colors group">
                                                <td className="px-6 py-4 font-medium text-white">{r.raw_data?.title || "Unknown"}</td>
                                                <td className="px-6 py-4 text-navy-300">
                                                    {r.raw_data?.phone ? <span className="block text-gold-200">{r.raw_data.phone}</span> : ""}
                                                    {r.raw_data?.email ? <span className="block">{r.raw_data.email}</span> : ""}
                                                    {!r.raw_data?.phone && !r.raw_data?.email && "N/A"}
                                                </td>
                                                <td className="px-6 py-4 text-navy-400">
                                                    {r.raw_data?.website ? (
                                                        <a href={r.raw_data.website} target="_blank" rel="noreferrer" className="text-blue-400 hover:text-blue-300 hover:underline">
                                                            Visit Site
                                                        </a>
                                                    ) : "N/A"}
                                                </td>
                                                <td className="px-6 py-4">
                                                    <span className="px-3 py-1 bg-navy-800 border border-navy-700 rounded-full text-xs text-navy-300">
                                                        {r.source}
                                                    </span>
                                                </td>
                                                <td className="px-6 py-4 text-right">
                                                    <button
                                                        onClick={() => importToCRM(r.id)}
                                                        className="px-4 py-2 bg-navy-800 hover:bg-gold-500 hover:text-navy-950 text-navy-300 rounded-lg text-xs font-semibold flex items-center gap-2 transition-all ml-auto opacity-70 group-hover:opacity-100"
                                                    >
                                                        <UploadCloud className="h-4 w-4" /> Import CRM
                                                    </button>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
