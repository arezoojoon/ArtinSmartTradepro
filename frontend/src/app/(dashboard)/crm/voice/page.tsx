"use client";

import { useState, useEffect, useRef } from "react";
import { Upload, Mic, FileAudio, Brain, Clock, CheckCircle, AlertTriangle, TrendingUp, MessageSquare, Target, Zap, XCircle, CalendarPlus, ClipboardList, StickyNote, Shield } from "lucide-react";
import { BASE_URL } from "@/lib/api";

export default function VoiceIntelligencePage() {
    const [file, setFile] = useState<File | null>(null);
    const [analyzing, setAnalyzing] = useState(false);
    const [result, setResult] = useState<any>(null);
    const [recordings, setRecordings] = useState([]);
    const [dragOver, setDragOver] = useState(false);
    const [jobId, setJobId] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const pollingRef = useRef<NodeJS.Timeout | null>(null);

    useEffect(() => {
        fetchRecordings();
        return () => { if (pollingRef.current) clearInterval(pollingRef.current); };
    }, []);

    const fetchRecordings = async () => {
        try {
            const token = localStorage.getItem("access_token");
            const res = await fetch(`${BASE_URL}/crm/ai/voice/recordings`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (res.ok) setRecordings(await res.json());
        } catch (err) { console.error(err); }
    };

    const pollStatus = (jid: string) => {
        setJobId(jid);
        pollingRef.current = setInterval(async () => {
            try {
                const token = localStorage.getItem("access_token");
                const res = await fetch(`${BASE_URL}/crm/ai/voice/status/${jid}`, {
                    headers: { "Authorization": `Bearer ${token}` }
                });
                if (!res.ok) return;
                const data = await res.json();

                if (data.status === "completed") {
                    clearInterval(pollingRef.current!);
                    pollingRef.current = null;
                    setJobId(null);
                    setAnalyzing(false);
                    setResult(data);
                    fetchRecordings();
                } else if (data.status === "failed") {
                    clearInterval(pollingRef.current!);
                    pollingRef.current = null;
                    setJobId(null);
                    setAnalyzing(false);
                    setError(data.error_message || "Analysis failed. Credits refunded.");
                }
            } catch (err) { console.error(err); }
        }, 3000);
    };

    const handleAnalyze = async () => {
        if (!file) return;
        setAnalyzing(true);
        setResult(null);
        setError(null);

        try {
            const token = localStorage.getItem("access_token");
            const formData = new FormData();
            formData.append("file", file);

            const res = await fetch(`${BASE_URL}/crm/ai/voice/analyze`, {
                method: "POST",
                headers: { "Authorization": `Bearer ${token}` },
                body: formData
            });

            if (res.ok) {
                const data = await res.json();
                if (data.status === "duplicate") {
                    setAnalyzing(false);
                    setError("This audio was already analyzed. No additional charges applied.");
                    return;
                }
                pollStatus(data.job_id);
            } else {
                const err = await res.json();
                setError(err.detail || "Upload failed");
                setAnalyzing(false);
            }
        } catch (err) {
            console.error(err);
            setError("Failed to upload audio");
            setAnalyzing(false);
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setDragOver(false);
        const dropped = e.dataTransfer.files[0];
        if (dropped && dropped.type.startsWith("audio/")) setFile(dropped);
    };

    const getSentimentColor = (s: string) => {
        if (s === "POSITIVE") return "text-green-400 bg-green-400/10 border-green-400/20";
        if (s === "NEGATIVE") return "text-red-400 bg-red-400/10 border-red-400/20";
        return "text-blue-400 bg-blue-400/10 border-blue-400/20";
    };

    const getUrgencyColor = (u: string) => {
        if (u === "high") return "text-red-400 bg-red-400/10 border-red-400/20";
        if (u === "medium") return "text-yellow-400 bg-yellow-400/10 border-yellow-400/20";
        return "text-green-400 bg-green-400/10 border-green-400/20";
    };

    const getActionIcon = (type: string) => {
        if (type === "followup") return <CalendarPlus className="h-4 w-4 text-purple-400" />;
        if (type === "task") return <ClipboardList className="h-4 w-4 text-blue-400" />;
        return <StickyNote className="h-4 w-4 text-yellow-400" />;
    };

    return (
        <div className="p-6 max-w-7xl mx-auto">
            {/* Header */}
            <div className="mb-8">
                <div className="flex items-center gap-3 mb-2">
                    <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center">
                        <Brain className="h-5 w-5 text-white" />
                    </div>
                    <div>
                        <h1 className="text-2xl font-bold text-white">Voice Intelligence</h1>
                        <p className="text-sm text-navy-400">Upload sales calls → AI extracts insights, sentiment & action items</p>
                    </div>
                </div>
                <div className="flex items-center gap-4 mt-3 text-xs text-navy-500">
                    <span className="flex items-center gap-1"><Zap className="h-3 w-3" /> 5 credits/analysis</span>
                    <span className="flex items-center gap-1"><Shield className="h-3 w-3" /> 20/day limit</span>
                    <span className="flex items-center gap-1"><Brain className="h-3 w-3" /> Gemini 2.0 Pro</span>
                </div>
            </div>

            {/* Error Banner */}
            {error && (
                <div className="mb-6 p-4 bg-red-400/10 border border-red-400/20 rounded-xl flex items-center gap-3">
                    <XCircle className="h-5 w-5 text-red-400 shrink-0" />
                    <p className="text-red-400 text-sm">{error}</p>
                    <button onClick={() => setError(null)} className="ml-auto text-red-400 hover:text-red-300 text-xl leading-none">&times;</button>
                </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Upload Panel */}
                <div className="space-y-6">
                    <div
                        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                        onDragLeave={() => setDragOver(false)}
                        onDrop={handleDrop}
                        className={`border-2 border-dashed rounded-xl p-12 text-center transition-all cursor-pointer ${dragOver ? 'border-gold-400 bg-gold-400/5' : 'border-navy-700 hover:border-navy-500 bg-navy-900/50'}`}
                        onClick={() => document.getElementById("audio-input")?.click()}
                    >
                        <input id="audio-input" type="file" accept="audio/*" className="hidden"
                            onChange={(e) => e.target.files?.[0] && setFile(e.target.files[0])} />
                        <Upload className={`h-12 w-12 mx-auto mb-4 ${dragOver ? 'text-gold-400' : 'text-navy-500'}`} />
                        <p className="text-white font-semibold mb-2">
                            {file ? file.name : "Drop audio file here or click to browse"}
                        </p>
                        <p className="text-xs text-navy-500">WAV, MP3, M4A, OGG, WebM • Max 10MB</p>
                        {file && (
                            <div className="mt-4 flex items-center justify-center gap-4">
                                <span className="text-sm text-navy-400 flex items-center gap-1">
                                    <FileAudio className="h-4 w-4" /> {(file.size / 1024 / 1024).toFixed(2)} MB
                                </span>
                                <button onClick={(e) => { e.stopPropagation(); handleAnalyze(); }}
                                    disabled={analyzing}
                                    className="px-6 py-2 bg-gradient-to-r from-purple-500 to-indigo-600 text-white rounded-lg font-semibold hover:opacity-90 transition-opacity disabled:opacity-50 flex items-center gap-2">
                                    {analyzing ? (
                                        <><div className="h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div> Processing...</>
                                    ) : (
                                        <><Zap className="h-4 w-4" /> Analyze (5 credits)</>
                                    )}
                                </button>
                            </div>
                        )}
                    </div>

                    {/* Recent Recordings */}
                    <div className="bg-navy-900 border border-navy-800 rounded-xl p-6">
                        <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
                            <Mic className="h-4 w-4 text-purple-400" /> Recent Recordings
                        </h3>
                        {recordings.length === 0 ? (
                            <p className="text-navy-500 text-sm text-center py-4">No recordings yet</p>
                        ) : (
                            <div className="space-y-2 max-h-64 overflow-y-auto">
                                {recordings.map((rec: any) => (
                                    <div key={rec.id} className="flex items-center justify-between p-3 bg-navy-950 rounded-lg">
                                        <div className="flex items-center gap-3">
                                            <FileAudio className="h-4 w-4 text-navy-400" />
                                            <div>
                                                <p className="text-white text-sm">{rec.file_name || "Unnamed"}</p>
                                                <p className="text-navy-500 text-xs">{new Date(rec.created_at).toLocaleDateString()}</p>
                                            </div>
                                        </div>
                                        <span className="text-xs text-navy-500 font-mono">
                                            {rec.file_size_bytes ? `${(rec.file_size_bytes / 1024).toFixed(0)}KB` : "—"}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                {/* Results Panel */}
                <div>
                    {!result && !analyzing && (
                        <div className="bg-navy-900 border border-navy-800 rounded-xl p-12 text-center">
                            <Brain className="h-16 w-16 mx-auto text-navy-700 mb-4" />
                            <h3 className="text-white font-semibold mb-2">Upload & Analyze</h3>
                            <p className="text-navy-500 text-sm">Upload a sales call to see AI-powered insights.</p>
                        </div>
                    )}

                    {analyzing && (
                        <div className="bg-navy-900 border border-navy-800 rounded-xl p-12 text-center">
                            <div className="h-16 w-16 mx-auto border-4 border-purple-500 border-t-transparent rounded-full animate-spin mb-4"></div>
                            <h3 className="text-white font-semibold mb-2">Analyzing with Gemini 2.0 Pro...</h3>
                            <p className="text-navy-500 text-sm">Extracting transcript, sentiment & action items</p>
                            <p className="text-navy-600 text-xs mt-3">Polling every 3s • Typical: 8–12 seconds</p>
                        </div>
                    )}

                    {result && (
                        <div className="space-y-4">
                            {/* Metrics */}
                            <div className="grid grid-cols-3 gap-3">
                                <div className={`rounded-xl p-4 border ${getSentimentColor(result.sentiment)}`}>
                                    <p className="text-xs opacity-70 mb-1">Sentiment</p>
                                    <p className="font-bold text-lg">{result.sentiment}</p>
                                </div>
                                <div className={`rounded-xl p-4 border ${getUrgencyColor(result.urgency)}`}>
                                    <p className="text-xs opacity-70 mb-1">Urgency</p>
                                    <p className="font-bold text-lg capitalize">{result.urgency}</p>
                                </div>
                                <div className="rounded-xl p-4 border border-gold-400/20 text-gold-400 bg-gold-400/10">
                                    <p className="text-xs opacity-70 mb-1">Confidence</p>
                                    <p className="font-bold text-lg">{(result.confidence * 100).toFixed(0)}%</p>
                                </div>
                            </div>

                            {/* Intent */}
                            <div className="bg-navy-900 border border-navy-800 rounded-xl p-5">
                                <h4 className="text-white font-semibold mb-2 flex items-center gap-2">
                                    <Target className="h-4 w-4 text-purple-400" /> Intent
                                </h4>
                                <p className="text-navy-300">{result.intent}</p>
                            </div>

                            {/* Transcript */}
                            <div className="bg-navy-900 border border-navy-800 rounded-xl p-5">
                                <h4 className="text-white font-semibold mb-3 flex items-center gap-2">
                                    <MessageSquare className="h-4 w-4 text-blue-400" /> Transcript
                                </h4>
                                <div className="bg-navy-950 p-4 rounded-lg text-navy-300 text-sm leading-relaxed max-h-48 overflow-y-auto font-mono">
                                    {result.transcript}
                                </div>
                            </div>

                            {/* Suggested Actions */}
                            {result.suggested_actions?.length > 0 && (
                                <div className="bg-gradient-to-r from-purple-500/5 to-indigo-600/5 border border-purple-500/20 rounded-xl p-5">
                                    <h4 className="text-white font-semibold mb-3 flex items-center gap-2">
                                        <Zap className="h-4 w-4 text-purple-400" /> Suggested Actions
                                    </h4>
                                    <ul className="space-y-2">
                                        {result.suggested_actions.map((action: any, i: number) => (
                                            <li key={i} className="flex items-center justify-between p-3 bg-navy-900/80 rounded-lg">
                                                <div className="flex items-center gap-3">
                                                    {getActionIcon(action.type)}
                                                    <span className="text-sm text-navy-300">{action.label}</span>
                                                </div>
                                                <button className="px-3 py-1 text-xs bg-purple-500/20 text-purple-400 rounded-lg hover:bg-purple-500/30 transition-colors">
                                                    {action.type === "followup" ? "Schedule" : action.type === "task" ? "Create" : "Add"}
                                                </button>
                                            </li>
                                        ))}
                                    </ul>
                                    <p className="text-xs text-navy-600 mt-3 flex items-center gap-1">
                                        <Shield className="h-3 w-3" /> Actions require your confirmation. Nothing is auto-applied.
                                    </p>
                                </div>
                            )}

                            {/* Key Topics */}
                            {result.key_topics?.length > 0 && (
                                <div className="bg-navy-900 border border-navy-800 rounded-xl p-5">
                                    <h4 className="text-white font-semibold mb-3 flex items-center gap-2">
                                        <TrendingUp className="h-4 w-4 text-gold-400" /> Key Topics
                                    </h4>
                                    <div className="flex flex-wrap gap-2">
                                        {result.key_topics.map((topic: string, i: number) => (
                                            <span key={i} className="px-3 py-1 bg-navy-800 text-navy-300 rounded-full text-xs">{topic}</span>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Footer */}
                            <div className="flex items-center justify-between text-xs text-navy-500 px-1">
                                <span className="flex items-center gap-1">
                                    <Clock className="h-3 w-3" /> {result.processing_time?.toFixed(1)}s
                                </span>
                                <span className="flex items-center gap-1">
                                    <AlertTriangle className="h-3 w-3" /> {result.disclaimer}
                                </span>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
