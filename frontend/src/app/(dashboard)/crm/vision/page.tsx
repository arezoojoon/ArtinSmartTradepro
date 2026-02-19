"use client";

import { useState, useEffect, useRef } from "react";
import { Upload, Eye, CreditCard, Building2, User, Phone, Mail, Globe, Linkedin, MapPin, CheckCircle, AlertTriangle, Zap, Shield, XCircle, TrendingUp } from "lucide-react";
import { BASE_URL } from "@/lib/api";

interface ScanResult {
    job_id: string;
    status: string;
    card_id?: string;
    extracted_name?: string;
    extracted_company?: string;
    extracted_position?: string;
    extracted_phone?: string;
    extracted_email?: string;
    extracted_website?: string;
    extracted_linkedin?: string;
    extracted_address?: string;
    confidence_name?: number;
    confidence_company?: number;
    confidence_phone?: number;
    confidence_email?: number;
    confidence_overall?: number;
    error_message?: string;
}

function ConfidenceBadge({ value }: { value: number }) {
    const pct = Math.round(value * 100);
    const color = pct >= 80 ? "text-green-400 bg-green-400/10" : pct >= 50 ? "text-yellow-400 bg-yellow-400/10" : "text-red-400 bg-red-400/10";
    return <span className={`px-2 py-0.5 rounded-full text-xs font-mono ${color}`}>{pct}%</span>;
}

export default function VisionIntelligencePage() {
    const [file, setFile] = useState<File | null>(null);
    const [preview, setPreview] = useState<string | null>(null);
    const [scanning, setScanning] = useState(false);
    const [result, setResult] = useState<ScanResult | null>(null);
    const [cards, setCards] = useState([]);
    const [dragOver, setDragOver] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [creating, setCreating] = useState(false);
    const [created, setCreated] = useState(false);
    const pollingRef = useRef<NodeJS.Timeout | null>(null);

    // Editable contact fields
    const [editName, setEditName] = useState("");
    const [editCompany, setEditCompany] = useState("");
    const [editPosition, setEditPosition] = useState("");
    const [editPhone, setEditPhone] = useState("");
    const [editEmail, setEditEmail] = useState("");
    const [editLinkedin, setEditLinkedin] = useState("");

    useEffect(() => {
        fetchCards();
        return () => { if (pollingRef.current) clearInterval(pollingRef.current); };
    }, []);

    const fetchCards = async () => {
        try {
            const token = localStorage.getItem("access_token");
            const res = await fetch(`${BASE_URL}/crm/ai/vision/cards`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            if (res.ok) setCards(await res.json());
        } catch (err) { console.error(err); }
    };

    const pollStatus = (jobId: string) => {
        pollingRef.current = setInterval(async () => {
            try {
                const token = localStorage.getItem("access_token");
                const res = await fetch(`${BASE_URL}/crm/ai/vision/status/${jobId}`, {
                    headers: { Authorization: `Bearer ${token}` }
                });
                if (!res.ok) return;
                const data: ScanResult = await res.json();

                if (data.status === "completed") {
                    clearInterval(pollingRef.current!);
                    pollingRef.current = null;
                    setScanning(false);
                    setResult(data);
                    // Pre-fill editable fields
                    const nameParts = (data.extracted_name || "").split(" ");
                    setEditName(data.extracted_name || "");
                    setEditCompany(data.extracted_company || "");
                    setEditPosition(data.extracted_position || "");
                    setEditPhone(data.extracted_phone || "");
                    setEditEmail(data.extracted_email || "");
                    setEditLinkedin(data.extracted_linkedin || "");
                    fetchCards();
                } else if (data.status === "failed") {
                    clearInterval(pollingRef.current!);
                    pollingRef.current = null;
                    setScanning(false);
                    setError(data.error_message || "Scan failed. Credits refunded.");
                }
            } catch (err) { console.error(err); }
        }, 3000);
    };

    const handleScan = async () => {
        if (!file) return;
        setScanning(true);
        setResult(null);
        setError(null);
        setCreated(false);

        try {
            const token = localStorage.getItem("access_token");
            const formData = new FormData();
            formData.append("file", file);

            const res = await fetch(`${BASE_URL}/crm/ai/vision/scan`, {
                method: "POST",
                headers: { Authorization: `Bearer ${token}` },
                body: formData
            });

            if (res.ok) {
                const data = await res.json();
                if (data.status === "duplicate") {
                    setScanning(false);
                    setError("This image was already scanned. No additional charges.");
                    return;
                }
                pollStatus(data.job_id);
            } else {
                const err = await res.json();
                setError(err.detail || "Upload failed");
                setScanning(false);
            }
        } catch (err) {
            console.error(err);
            setError("Failed to upload image");
            setScanning(false);
        }
    };

    const handleConfirm = async () => {
        if (!result?.card_id) return;
        setCreating(true);

        try {
            const token = localStorage.getItem("access_token");
            const nameParts = editName.split(" ");
            const firstName = nameParts[0] || "Unknown";
            const lastName = nameParts.slice(1).join(" ") || undefined;

            const res = await fetch(`${BASE_URL}/crm/ai/vision/confirm/${result.card_id}`, {
                method: "POST",
                headers: {
                    Authorization: `Bearer ${token}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    first_name: firstName,
                    last_name: lastName,
                    company_name: editCompany || undefined,
                    position: editPosition || undefined,
                    phone: editPhone || undefined,
                    email: editEmail || undefined,
                    linkedin_url: editLinkedin || undefined,
                })
            });

            if (res.ok) {
                setCreated(true);
                fetchCards();
            } else {
                const err = await res.json();
                setError(err.detail || "Failed to create contact");
            }
        } catch (err) {
            console.error(err);
            setError("Failed to create contact");
        } finally {
            setCreating(false);
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setDragOver(false);
        const dropped = e.dataTransfer.files[0];
        if (dropped && dropped.type.startsWith("image/")) {
            setFile(dropped);
            setPreview(URL.createObjectURL(dropped));
        }
    };

    const handleFileSelect = (f: File) => {
        setFile(f);
        setPreview(URL.createObjectURL(f));
    };

    return (
        <div className="p-6 max-w-7xl mx-auto">
            {/* Header */}
            <div className="mb-8">
                <div className="flex items-center gap-3 mb-2">
                    <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center">
                        <Eye className="h-5 w-5 text-white" />
                    </div>
                    <div>
                        <h1 className="text-2xl font-bold text-white">Vision Intelligence</h1>
                        <p className="text-sm text-navy-400">Scan business cards → AI extracts contacts with confidence scores</p>
                    </div>
                </div>
                <div className="flex items-center gap-4 mt-3 text-xs text-navy-500">
                    <span className="flex items-center gap-1"><Zap className="h-3 w-3" /> 3 credits/scan</span>
                    <span className="flex items-center gap-1"><Shield className="h-3 w-3" /> 30/day limit</span>
                    <span className="flex items-center gap-1"><Eye className="h-3 w-3" /> Gemini 2.0 Pro</span>
                </div>
            </div>

            {/* Error */}
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
                        className={`border-2 border-dashed rounded-xl p-8 text-center transition-all cursor-pointer ${dragOver ? 'border-emerald-400 bg-emerald-400/5' : 'border-navy-700 hover:border-navy-500 bg-navy-900/50'}`}
                        onClick={() => document.getElementById("image-input")?.click()}
                    >
                        <input id="image-input" type="file" accept="image/*" className="hidden"
                            onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])} />

                        {preview ? (
                            <div className="space-y-4">
                                <img src={preview} alt="Preview" className="mx-auto max-h-48 rounded-lg shadow-lg" />
                                <p className="text-white font-semibold">{file?.name}</p>
                                <div className="flex items-center justify-center gap-4">
                                    <span className="text-sm text-navy-400">
                                        {file && (file.size / 1024 / 1024).toFixed(2)} MB
                                    </span>
                                    <button onClick={(e) => { e.stopPropagation(); handleScan(); }}
                                        disabled={scanning}
                                        className="px-6 py-2 bg-gradient-to-r from-emerald-500 to-teal-600 text-white rounded-lg font-semibold hover:opacity-90 transition-opacity disabled:opacity-50 flex items-center gap-2">
                                        {scanning ? (
                                            <><div className="h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div> Scanning...</>
                                        ) : (
                                            <><Eye className="h-4 w-4" /> Scan (3 credits)</>
                                        )}
                                    </button>
                                </div>
                            </div>
                        ) : (
                            <>
                                <Upload className={`h-12 w-12 mx-auto mb-4 ${dragOver ? 'text-emerald-400' : 'text-navy-500'}`} />
                                <p className="text-white font-semibold mb-2">Drop a business card image</p>
                                <p className="text-xs text-navy-500">JPEG, PNG, WebP, HEIC • Max 5MB</p>
                            </>
                        )}
                    </div>

                    {/* Recent Scans */}
                    <div className="bg-navy-900 border border-navy-800 rounded-xl p-6">
                        <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
                            <CreditCard className="h-4 w-4 text-emerald-400" /> Recent Scans
                        </h3>
                        {cards.length === 0 ? (
                            <p className="text-navy-500 text-sm text-center py-4">No scans yet</p>
                        ) : (
                            <div className="space-y-2 max-h-64 overflow-y-auto">
                                {cards.map((card: any) => (
                                    <div key={card.id} className="flex items-center justify-between p-3 bg-navy-950 rounded-lg">
                                        <div className="flex items-center gap-3">
                                            <CreditCard className="h-4 w-4 text-navy-400" />
                                            <div>
                                                <p className="text-white text-sm">{card.extracted_name || card.file_name || "Unnamed"}</p>
                                                <p className="text-navy-500 text-xs">{card.extracted_company}</p>
                                            </div>
                                        </div>
                                        {card.contact_created_id ? (
                                            <CheckCircle className="h-4 w-4 text-green-400" />
                                        ) : (
                                            <span className="text-xs text-navy-500">Pending</span>
                                        )}
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                {/* Results Panel */}
                <div>
                    {!result && !scanning && (
                        <div className="bg-navy-900 border border-navy-800 rounded-xl p-12 text-center">
                            <Eye className="h-16 w-16 mx-auto text-navy-700 mb-4" />
                            <h3 className="text-white font-semibold mb-2">Scan a Business Card</h3>
                            <p className="text-navy-500 text-sm">Upload an image to extract contact information.</p>
                        </div>
                    )}

                    {scanning && (
                        <div className="bg-navy-900 border border-navy-800 rounded-xl p-12 text-center">
                            <div className="h-16 w-16 mx-auto border-4 border-emerald-500 border-t-transparent rounded-full animate-spin mb-4"></div>
                            <h3 className="text-white font-semibold mb-2">Scanning with Gemini Vision...</h3>
                            <p className="text-navy-500 text-sm">Extracting name, company, phone, email & more</p>
                            <p className="text-navy-600 text-xs mt-3">Polling every 3s • Typical: 3–6 seconds</p>
                        </div>
                    )}

                    {result && !created && (
                        <div className="space-y-4">
                            {/* Overall Confidence */}
                            <div className="bg-gradient-to-r from-emerald-500/10 to-teal-600/10 border border-emerald-500/20 rounded-xl p-5">
                                <div className="flex items-center justify-between mb-3">
                                    <h4 className="text-white font-semibold flex items-center gap-2">
                                        <TrendingUp className="h-4 w-4 text-emerald-400" /> Overall Confidence
                                    </h4>
                                    <ConfidenceBadge value={result.confidence_overall || 0} />
                                </div>
                                <div className="w-full bg-navy-800 rounded-full h-2">
                                    <div className="h-2 rounded-full bg-gradient-to-r from-emerald-500 to-teal-400 transition-all"
                                        style={{ width: `${(result.confidence_overall || 0) * 100}%` }}></div>
                                </div>
                            </div>

                            {/* Editable Fields */}
                            <div className="bg-navy-900 border border-navy-800 rounded-xl p-5 space-y-4">
                                <h4 className="text-white font-semibold mb-1">Extracted Contact — Review & Edit</h4>
                                <p className="text-navy-500 text-xs mb-3">Edit any field before creating the contact.</p>

                                <div className="space-y-3">
                                    {/* Name */}
                                    <div className="flex items-center gap-3">
                                        <User className="h-4 w-4 text-navy-400 shrink-0" />
                                        <input value={editName} onChange={(e) => setEditName(e.target.value)}
                                            placeholder="Full Name"
                                            className="flex-1 bg-navy-950 border border-navy-700 rounded-lg px-3 py-2 text-white text-sm focus:border-emerald-500 outline-none" />
                                        <ConfidenceBadge value={result.confidence_name || 0} />
                                    </div>

                                    {/* Company */}
                                    <div className="flex items-center gap-3">
                                        <Building2 className="h-4 w-4 text-navy-400 shrink-0" />
                                        <input value={editCompany} onChange={(e) => setEditCompany(e.target.value)}
                                            placeholder="Company"
                                            className="flex-1 bg-navy-950 border border-navy-700 rounded-lg px-3 py-2 text-white text-sm focus:border-emerald-500 outline-none" />
                                        <ConfidenceBadge value={result.confidence_company || 0} />
                                    </div>

                                    {/* Position */}
                                    <div className="flex items-center gap-3">
                                        <CreditCard className="h-4 w-4 text-navy-400 shrink-0" />
                                        <input value={editPosition} onChange={(e) => setEditPosition(e.target.value)}
                                            placeholder="Position / Title"
                                            className="flex-1 bg-navy-950 border border-navy-700 rounded-lg px-3 py-2 text-white text-sm focus:border-emerald-500 outline-none" />
                                    </div>

                                    {/* Phone */}
                                    <div className="flex items-center gap-3">
                                        <Phone className="h-4 w-4 text-navy-400 shrink-0" />
                                        <input value={editPhone} onChange={(e) => setEditPhone(e.target.value)}
                                            placeholder="Phone"
                                            className="flex-1 bg-navy-950 border border-navy-700 rounded-lg px-3 py-2 text-white text-sm focus:border-emerald-500 outline-none" />
                                        <ConfidenceBadge value={result.confidence_phone || 0} />
                                    </div>

                                    {/* Email */}
                                    <div className="flex items-center gap-3">
                                        <Mail className="h-4 w-4 text-navy-400 shrink-0" />
                                        <input value={editEmail} onChange={(e) => setEditEmail(e.target.value)}
                                            placeholder="Email"
                                            className="flex-1 bg-navy-950 border border-navy-700 rounded-lg px-3 py-2 text-white text-sm focus:border-emerald-500 outline-none" />
                                        <ConfidenceBadge value={result.confidence_email || 0} />
                                    </div>

                                    {/* LinkedIn */}
                                    <div className="flex items-center gap-3">
                                        <Linkedin className="h-4 w-4 text-navy-400 shrink-0" />
                                        <input value={editLinkedin} onChange={(e) => setEditLinkedin(e.target.value)}
                                            placeholder="LinkedIn URL"
                                            className="flex-1 bg-navy-950 border border-navy-700 rounded-lg px-3 py-2 text-white text-sm focus:border-emerald-500 outline-none" />
                                    </div>

                                    {/* Website */}
                                    {result.extracted_website && (
                                        <div className="flex items-center gap-3">
                                            <Globe className="h-4 w-4 text-navy-400 shrink-0" />
                                            <span className="text-sm text-navy-300">{result.extracted_website}</span>
                                        </div>
                                    )}

                                    {/* Address */}
                                    {result.extracted_address && (
                                        <div className="flex items-center gap-3">
                                            <MapPin className="h-4 w-4 text-navy-400 shrink-0" />
                                            <span className="text-sm text-navy-300">{result.extracted_address}</span>
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* Create Contact CTA */}
                            <button onClick={handleConfirm} disabled={creating || !editName}
                                className="w-full py-3 bg-gradient-to-r from-emerald-500 to-teal-600 text-white rounded-xl font-semibold hover:opacity-90 transition-opacity disabled:opacity-50 flex items-center justify-center gap-2">
                                {creating ? (
                                    <><div className="h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div> Creating...</>
                                ) : (
                                    <><CheckCircle className="h-5 w-5" /> Create CRM Contact</>
                                )}
                            </button>

                            <p className="text-xs text-navy-600 text-center flex items-center justify-center gap-1">
                                <Shield className="h-3 w-3" /> Contact created only after your confirmation. Nothing auto-applied.
                            </p>
                        </div>
                    )}

                    {created && (
                        <div className="bg-gradient-to-r from-emerald-500/10 to-teal-600/10 border border-emerald-500/20 rounded-xl p-8 text-center">
                            <CheckCircle className="h-16 w-16 mx-auto text-emerald-400 mb-4" />
                            <h3 className="text-white font-semibold text-lg mb-2">Contact Created!</h3>
                            <p className="text-navy-400 text-sm mb-4">
                                {editName} has been added to your CRM{editCompany ? ` at ${editCompany}` : ""}.
                            </p>
                            <button onClick={() => { setResult(null); setCreated(false); setFile(null); setPreview(null); }}
                                className="px-6 py-2 bg-navy-800 text-white rounded-lg hover:bg-navy-700 transition-colors">
                                Scan Another Card
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
