"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import api from "@/lib/api";
import {
    Ship, Package, AlertTriangle, MapPin, Clock, Plus, Search,
    Camera, Loader2, CheckCircle2, Truck, ArrowRight, X,
    ChevronDown, ChevronUp, Eye, ScanLine, Zap, BarChart3,
    Timer, TrendingUp, BoxIcon, FileText,
} from "lucide-react";

/* ─── Types ──────────────────────────────────────────────────────── */
interface ShipmentData {
    id: string;
    shipment_number: string;
    order_id?: string;
    origin: Record<string, string>;
    destination: Record<string, string>;
    status: string;
    goods_description?: string;
    total_weight_kg?: number;
    total_packages?: number;
    incoterms?: string;
    customer_name?: string;
    customer_phone?: string;
    ai_extracted?: boolean;
    estimated_delivery?: string;
    actual_delivery?: string;
    notification_sent?: boolean;
    created_at?: string;
    events?: EventData[];
    packages?: PackageData[];
}

interface EventData {
    id: string;
    event_type: string;
    actor?: string;
    notes?: string;
    location_name?: string;
    latitude?: number;
    longitude?: number;
    timestamp: string;
}

interface PackageData {
    id: string;
    barcode?: string;
    weight_kg?: number;
    contents?: string;
}

interface StatsData {
    total: number;
    in_transit: number;
    delivered: number;
    delayed: number;
    pending: number;
    on_time_delivery_pct: number;
    status_breakdown: Record<string, number>;
}

/* ─── Status config ──────────────────────────────────────────────── */
const STATUS_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
    created:           { label: "Created",           color: "text-gray-400",    bg: "bg-gray-400/10" },
    picked:            { label: "Picked",            color: "text-blue-400",    bg: "bg-blue-400/10" },
    assigned:          { label: "Assigned",          color: "text-indigo-400",  bg: "bg-indigo-400/10" },
    pickup_confirmed:  { label: "Pickup Confirmed",  color: "text-cyan-400",    bg: "bg-cyan-400/10" },
    in_transit:        { label: "In Transit",        color: "text-blue-400",    bg: "bg-blue-400/10" },
    at_hub:            { label: "At Hub",            color: "text-amber-400",   bg: "bg-amber-400/10" },
    out_for_delivery:  { label: "Out for Delivery",  color: "text-purple-400",  bg: "bg-purple-400/10" },
    delivery_attempt:  { label: "Delivery Attempt",  color: "text-orange-400",  bg: "bg-orange-400/10" },
    delivered:         { label: "Delivered",          color: "text-emerald-400", bg: "bg-emerald-400/10" },
    failed_delivery:   { label: "Failed",            color: "text-rose-400",    bg: "bg-rose-400/10" },
    returned:          { label: "Returned",          color: "text-rose-300",    bg: "bg-rose-300/10" },
    damaged:           { label: "Damaged",           color: "text-red-400",     bg: "bg-red-400/10" },
    cancelled:         { label: "Cancelled",         color: "text-gray-500",    bg: "bg-gray-500/10" },
};

const getStatus = (s: string) => STATUS_CONFIG[s] || { label: s, color: "text-gray-400", bg: "bg-gray-400/10" };

/* ═══════════════════════════════════════════════════════════════════ */
/*  MAIN PAGE                                                         */
/* ═══════════════════════════════════════════════════════════════════ */
export default function ShipmentsPage() {
    const [stats, setStats] = useState<StatsData | null>(null);
    const [shipments, setShipments] = useState<ShipmentData[]>([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState("");
    const [filterStatus, setFilterStatus] = useState("");
    const [selectedShipment, setSelectedShipment] = useState<ShipmentData | null>(null);
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [showScanModal, setShowScanModal] = useState(false);

    const loadData = useCallback(async () => {
        try {
            const [statsRes, shipmentsRes] = await Promise.allSettled([
                api.get("/logistics/stats"),
                api.get(`/logistics/shipments?limit=100${filterStatus ? `&status=${filterStatus}` : ""}${search ? `&search=${search}` : ""}`),
            ]);
            if (statsRes.status === "fulfilled") setStats(statsRes.value.data);
            if (shipmentsRes.status === "fulfilled") setShipments(shipmentsRes.value.data.shipments || []);
        } catch (e) {
            console.error("Failed to load logistics data:", e);
        } finally {
            setLoading(false);
        }
    }, [filterStatus, search]);

    useEffect(() => { loadData(); }, [loadData]);

    return (
        <div className="p-4 md:p-8 space-y-6 text-white min-h-screen">
            {/* Header */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h1 className="text-2xl font-bold flex items-center gap-2">
                        <Truck className="h-6 w-6 text-[#f5a623]" /> Smart Logistics
                    </h1>
                    <p className="text-white/60 text-sm">
                        AI-powered shipment tracking — scan documents, zero manual entry
                    </p>
                </div>
                <div className="flex gap-2">
                    <Button
                        onClick={() => setShowScanModal(true)}
                        className="bg-gradient-to-r from-[#f5a623] to-amber-600 text-black font-semibold hover:brightness-110 gap-2"
                    >
                        <ScanLine className="h-4 w-4" /> Smart Scan
                    </Button>
                    <Button
                        onClick={() => setShowCreateModal(true)}
                        variant="outline"
                        className="border-[#1e3a5f] text-white hover:bg-[#12253f] gap-2"
                    >
                        <Plus className="h-4 w-4" /> Manual Entry
                    </Button>
                </div>
            </div>

            {/* KPI Cards */}
            <div className="grid gap-4 grid-cols-2 md:grid-cols-5">
                {[
                    { label: "Total", value: stats?.total ?? 0, icon: BoxIcon, color: "text-white" },
                    { label: "In Transit", value: stats?.in_transit ?? 0, icon: Truck, color: "text-blue-400" },
                    { label: "Delivered", value: stats?.delivered ?? 0, icon: CheckCircle2, color: "text-emerald-400" },
                    { label: "Delayed / Damaged", value: stats?.delayed ?? 0, icon: AlertTriangle, color: "text-rose-400" },
                    { label: "On-Time %", value: `${stats?.on_time_delivery_pct ?? 0}%`, icon: TrendingUp, color: "text-[#f5a623]" },
                ].map((kpi) => (
                    <Card key={kpi.label} className="bg-[#0e1e33] border-[#1e3a5f]">
                        <CardContent className="p-4 flex items-center gap-3">
                            <div className="p-2 rounded-lg bg-[#12253f]">
                                <kpi.icon className={`h-5 w-5 ${kpi.color}`} />
                            </div>
                            <div>
                                <div className="text-xl font-bold text-white">{kpi.value}</div>
                                <div className="text-[10px] text-white/50 uppercase tracking-wider">{kpi.label}</div>
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>

            {/* Filters */}
            <div className="flex flex-col md:flex-row gap-3">
                <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-white/40" />
                    <input
                        type="text"
                        placeholder="Search shipments..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        className="w-full bg-[#0e1e33] border border-[#1e3a5f] rounded-lg pl-10 pr-4 py-2.5 text-sm text-white placeholder:text-white/30 focus:outline-none focus:border-[#f5a623]/50"
                    />
                </div>
                <select
                    value={filterStatus}
                    onChange={(e) => setFilterStatus(e.target.value)}
                    className="bg-[#0e1e33] border border-[#1e3a5f] rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-[#f5a623]/50"
                >
                    <option value="">All Statuses</option>
                    {Object.entries(STATUS_CONFIG).map(([k, v]) => (
                        <option key={k} value={k}>{v.label}</option>
                    ))}
                </select>
            </div>

            {/* Shipments List */}
            {loading ? (
                <div className="flex justify-center py-20">
                    <Loader2 className="h-8 w-8 animate-spin text-[#f5a623]" />
                </div>
            ) : shipments.length === 0 ? (
                <EmptyState onScan={() => setShowScanModal(true)} onCreate={() => setShowCreateModal(true)} />
            ) : (
                <div className="space-y-3">
                    {shipments.map((s) => (
                        <ShipmentRow
                            key={s.id}
                            shipment={s}
                            onSelect={() => setSelectedShipment(s)}
                        />
                    ))}
                </div>
            )}

            {/* Modals */}
            {showScanModal && (
                <SmartScanModal
                    onClose={() => setShowScanModal(false)}
                    onSuccess={() => { setShowScanModal(false); loadData(); }}
                />
            )}
            {showCreateModal && (
                <CreateShipmentModal
                    onClose={() => setShowCreateModal(false)}
                    onSuccess={() => { setShowCreateModal(false); loadData(); }}
                />
            )}
            {selectedShipment && (
                <ShipmentDetailModal
                    shipmentId={selectedShipment.id}
                    onClose={() => setSelectedShipment(null)}
                />
            )}
        </div>
    );
}

/* ═══════════════════════════════════════════════════════════════════ */
/*  EMPTY STATE                                                       */
/* ═══════════════════════════════════════════════════════════════════ */
function EmptyState({ onScan, onCreate }: { onScan: () => void; onCreate: () => void }) {
    return (
        <Card className="bg-[#0e1e33] border-[#1e3a5f]">
            <CardContent className="p-12 flex flex-col items-center justify-center text-center">
                <div className="relative mb-6">
                    <Truck className="h-20 w-20 text-[#1e3a5f]" />
                    <div className="absolute -bottom-1 -right-1 bg-[#f5a623] rounded-full p-1.5">
                        <Zap className="h-4 w-4 text-black" />
                    </div>
                </div>
                <h3 className="text-xl font-bold text-white mb-2">Smart Logistics</h3>
                <p className="text-white/50 max-w-md mb-6">
                    Scan a Bill of Lading, packing list, or delivery receipt — AI extracts
                    all data automatically. No typing needed.
                </p>
                <div className="flex gap-3">
                    <Button
                        onClick={onScan}
                        className="bg-gradient-to-r from-[#f5a623] to-amber-600 text-black font-semibold hover:brightness-110 gap-2"
                    >
                        <Camera className="h-4 w-4" /> Scan Document
                    </Button>
                    <Button onClick={onCreate} variant="outline" className="border-[#1e3a5f] text-white hover:bg-[#12253f] gap-2">
                        <Plus className="h-4 w-4" /> Create Manually
                    </Button>
                </div>
                {/* Feature highlights */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8 w-full max-w-2xl">
                    {[
                        { icon: ScanLine, title: "AI Document Scan", desc: "Photo of BL or packing list — auto-extracted" },
                        { icon: Clock, title: "Live Timeline", desc: "Track every event from factory to delivery" },
                        { icon: BarChart3, title: "KPIs & Alerts", desc: "On-time %, transit time, damage rate" },
                    ].map((f) => (
                        <div key={f.title} className="flex items-start gap-3 text-left p-3 rounded-lg bg-[#12253f]/50">
                            <f.icon className="h-5 w-5 text-[#f5a623] shrink-0 mt-0.5" />
                            <div>
                                <div className="text-sm font-semibold text-white">{f.title}</div>
                                <div className="text-xs text-white/40">{f.desc}</div>
                            </div>
                        </div>
                    ))}
                </div>
            </CardContent>
        </Card>
    );
}

/* ═══════════════════════════════════════════════════════════════════ */
/*  SHIPMENT ROW                                                      */
/* ═══════════════════════════════════════════════════════════════════ */
function ShipmentRow({ shipment, onSelect }: { shipment: ShipmentData; onSelect: () => void }) {
    const st = getStatus(shipment.status);
    const origin = shipment.origin;
    const dest = shipment.destination;
    const originLabel = [origin?.city, origin?.country].filter(Boolean).join(", ") || "—";
    const destLabel = [dest?.city, dest?.country].filter(Boolean).join(", ") || "—";

    return (
        <Card
            className="bg-[#0e1e33] border-[#1e3a5f] hover:border-[#f5a623]/30 transition-colors cursor-pointer"
            onClick={onSelect}
        >
            <CardContent className="p-4">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
                    <div className="flex items-center gap-4 flex-1 min-w-0">
                        <div className={`p-2 rounded-lg ${st.bg}`}>
                            <Truck className={`h-5 w-5 ${st.color}`} />
                        </div>
                        <div className="min-w-0">
                            <div className="flex items-center gap-2">
                                <span className="font-semibold text-white text-sm">{shipment.shipment_number}</span>
                                {shipment.ai_extracted && (
                                    <Badge className="bg-[#f5a623]/20 text-[#f5a623] border-[#f5a623]/30 text-[10px] px-1.5 py-0">
                                        AI
                                    </Badge>
                                )}
                            </div>
                            <div className="text-xs text-white/50 truncate">
                                {shipment.goods_description || "No description"}
                            </div>
                        </div>
                    </div>

                    <div className="flex items-center gap-2 text-xs text-white/60 shrink-0">
                        <MapPin className="h-3 w-3" />
                        <span>{originLabel}</span>
                        <ArrowRight className="h-3 w-3 text-[#f5a623]" />
                        <span>{destLabel}</span>
                    </div>

                    <div className="flex items-center gap-3 shrink-0">
                        {shipment.total_packages ? (
                            <span className="text-xs text-white/40">{shipment.total_packages} pkg</span>
                        ) : null}
                        {shipment.total_weight_kg ? (
                            <span className="text-xs text-white/40">{shipment.total_weight_kg} kg</span>
                        ) : null}
                        <Badge className={`${st.bg} ${st.color} border-transparent text-[10px]`}>
                            {st.label}
                        </Badge>
                        <Eye className="h-4 w-4 text-white/30" />
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}

/* ═══════════════════════════════════════════════════════════════════ */
/*  SMART SCAN MODAL                                                  */
/* ═══════════════════════════════════════════════════════════════════ */
function SmartScanModal({ onClose, onSuccess }: { onClose: () => void; onSuccess: () => void }) {
    const [file, setFile] = useState<File | null>(null);
    const [preview, setPreview] = useState<string | null>(null);
    const [processing, setProcessing] = useState(false);
    const [result, setResult] = useState<any>(null);
    const [error, setError] = useState("");
    const fileRef = useRef<HTMLInputElement>(null);

    const handleFile = (f: File) => {
        setFile(f);
        setError("");
        setResult(null);
        const reader = new FileReader();
        reader.onloadend = () => setPreview(reader.result as string);
        reader.readAsDataURL(f);
    };

    const handleExtract = async () => {
        if (!file) return;
        setProcessing(true);
        setError("");
        try {
            const formData = new FormData();
            formData.append("file", file);
            formData.append("auto_create", "true");

            const token = localStorage.getItem("token");
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/logistics/smart-extract`, {
                method: "POST",
                headers: { Authorization: `Bearer ${token}` },
                body: formData,
            });
            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || `Server error ${res.status}`);
            }
            const data = await res.json();
            setResult(data);
        } catch (e: any) {
            setError(e.message || "AI extraction failed");
        } finally {
            setProcessing(false);
        }
    };

    return (
        <ModalOverlay onClose={onClose}>
            <div className="bg-[#0a1628] border border-[#1e3a5f] rounded-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto p-6 space-y-5">
                <div className="flex justify-between items-center">
                    <h2 className="text-lg font-bold text-white flex items-center gap-2">
                        <ScanLine className="h-5 w-5 text-[#f5a623]" /> Smart Document Scan
                    </h2>
                    <button onClick={onClose} className="text-white/40 hover:text-white"><X className="h-5 w-5" /></button>
                </div>

                <p className="text-sm text-white/50">
                    Upload a photo of a Bill of Lading, Packing List, or Delivery Receipt.
                    AI will extract all data and create the shipment automatically.
                </p>

                {/* Upload area */}
                {!file ? (
                    <div
                        onClick={() => fileRef.current?.click()}
                        className="border-2 border-dashed border-[#1e3a5f] hover:border-[#f5a623]/50 rounded-xl p-10 flex flex-col items-center gap-3 cursor-pointer transition-colors"
                    >
                        <Camera className="h-10 w-10 text-[#f5a623]" />
                        <span className="text-sm text-white/60">Tap to take photo or upload image</span>
                        <span className="text-xs text-white/30">JPEG, PNG, WebP, PDF — up to 10MB</span>
                    </div>
                ) : (
                    <div className="relative">
                        {preview && (
                            <img src={preview} alt="Document" className="w-full rounded-xl border border-[#1e3a5f] max-h-60 object-contain bg-black" />
                        )}
                        <button
                            onClick={() => { setFile(null); setPreview(null); setResult(null); }}
                            className="absolute top-2 right-2 bg-black/70 rounded-full p-1"
                        >
                            <X className="h-4 w-4 text-white" />
                        </button>
                    </div>
                )}
                <input
                    ref={fileRef}
                    type="file"
                    accept="image/*,application/pdf"
                    capture="environment"
                    className="hidden"
                    onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
                />

                {error && (
                    <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-sm text-red-400">{error}</div>
                )}

                {/* Result */}
                {result && (
                    <div className="space-y-3">
                        <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-4">
                            <div className="flex items-center gap-2 mb-2">
                                <CheckCircle2 className="h-5 w-5 text-emerald-400" />
                                <span className="text-sm font-semibold text-emerald-400">Data Extracted & Shipment Created</span>
                            </div>
                            {result.shipment && (
                                <div className="text-xs text-white/60 space-y-1">
                                    <div><strong className="text-white/80">Shipment:</strong> {result.shipment.shipment_number}</div>
                                    <div><strong className="text-white/80">Status:</strong> {result.shipment.status}</div>
                                    {result.shipment.goods_description && (
                                        <div><strong className="text-white/80">Goods:</strong> {result.shipment.goods_description}</div>
                                    )}
                                    {result.shipment.customer_name && (
                                        <div><strong className="text-white/80">Customer:</strong> {result.shipment.customer_name}</div>
                                    )}
                                </div>
                            )}
                        </div>
                        {result.extracted && (
                            <details className="text-xs">
                                <summary className="text-white/40 cursor-pointer hover:text-white/60">Raw AI output</summary>
                                <pre className="mt-2 bg-[#12253f] rounded-lg p-3 text-white/60 overflow-auto max-h-40">
                                    {JSON.stringify(result.extracted, null, 2)}
                                </pre>
                            </details>
                        )}
                        <Button onClick={onSuccess} className="w-full bg-emerald-600 hover:bg-emerald-700 text-white">
                            Done
                        </Button>
                    </div>
                )}

                {/* Extract button */}
                {file && !result && (
                    <Button
                        onClick={handleExtract}
                        disabled={processing}
                        className="w-full bg-gradient-to-r from-[#f5a623] to-amber-600 text-black font-semibold hover:brightness-110 gap-2"
                    >
                        {processing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Zap className="h-4 w-4" />}
                        {processing ? "AI is analyzing..." : "Extract Data with AI"}
                    </Button>
                )}
            </div>
        </ModalOverlay>
    );
}

/* ═══════════════════════════════════════════════════════════════════ */
/*  CREATE SHIPMENT MODAL                                             */
/* ═══════════════════════════════════════════════════════════════════ */
function CreateShipmentModal({ onClose, onSuccess }: { onClose: () => void; onSuccess: () => void }) {
    const [form, setForm] = useState({
        shipment_number: "",
        goods_description: "",
        origin_city: "", origin_country: "",
        dest_city: "", dest_country: "",
        total_weight_kg: "",
        incoterms: "",
        customer_name: "", customer_phone: "",
    });
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState("");

    const set = (k: string, v: string) => setForm((p) => ({ ...p, [k]: v }));

    const handleSubmit = async () => {
        setSaving(true);
        setError("");
        try {
            await api.post("/logistics/shipments", {
                shipment_number: form.shipment_number || undefined,
                goods_description: form.goods_description || undefined,
                origin: { city: form.origin_city, country: form.origin_country },
                destination: { city: form.dest_city, country: form.dest_country },
                total_weight_kg: form.total_weight_kg ? parseFloat(form.total_weight_kg) : undefined,
                incoterms: form.incoterms || undefined,
                customer_name: form.customer_name || undefined,
                customer_phone: form.customer_phone || undefined,
            });
            onSuccess();
        } catch (e: any) {
            setError(e.data?.detail || "Failed to create shipment");
        } finally {
            setSaving(false);
        }
    };

    const inputCls = "w-full bg-[#12253f] border border-[#1e3a5f] rounded-lg px-3 py-2 text-sm text-white placeholder:text-white/30 focus:outline-none focus:border-[#f5a623]/50";

    return (
        <ModalOverlay onClose={onClose}>
            <div className="bg-[#0a1628] border border-[#1e3a5f] rounded-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto p-6 space-y-4">
                <div className="flex justify-between items-center">
                    <h2 className="text-lg font-bold text-white flex items-center gap-2">
                        <Plus className="h-5 w-5 text-[#f5a623]" /> New Shipment
                    </h2>
                    <button onClick={onClose} className="text-white/40 hover:text-white"><X className="h-5 w-5" /></button>
                </div>

                <div className="space-y-3">
                    <input placeholder="Shipment Number (auto if empty)" value={form.shipment_number} onChange={(e) => set("shipment_number", e.target.value)} className={inputCls} />
                    <input placeholder="Goods Description" value={form.goods_description} onChange={(e) => set("goods_description", e.target.value)} className={inputCls} />
                    <div className="grid grid-cols-2 gap-3">
                        <input placeholder="Origin City" value={form.origin_city} onChange={(e) => set("origin_city", e.target.value)} className={inputCls} />
                        <input placeholder="Origin Country" value={form.origin_country} onChange={(e) => set("origin_country", e.target.value)} className={inputCls} />
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                        <input placeholder="Destination City" value={form.dest_city} onChange={(e) => set("dest_city", e.target.value)} className={inputCls} />
                        <input placeholder="Destination Country" value={form.dest_country} onChange={(e) => set("dest_country", e.target.value)} className={inputCls} />
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                        <input placeholder="Weight (kg)" value={form.total_weight_kg} onChange={(e) => set("total_weight_kg", e.target.value)} className={inputCls} type="number" />
                        <select value={form.incoterms} onChange={(e) => set("incoterms", e.target.value)} className={inputCls}>
                            <option value="">Incoterms</option>
                            {["EXW","FCA","FAS","FOB","CFR","CIF","CPT","CIP","DAP","DPU","DDP"].map(t => <option key={t}>{t}</option>)}
                        </select>
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                        <input placeholder="Customer Name" value={form.customer_name} onChange={(e) => set("customer_name", e.target.value)} className={inputCls} />
                        <input placeholder="Customer Phone" value={form.customer_phone} onChange={(e) => set("customer_phone", e.target.value)} className={inputCls} />
                    </div>
                </div>

                {error && <div className="text-sm text-red-400 bg-red-500/10 rounded-lg p-3">{error}</div>}

                <Button onClick={handleSubmit} disabled={saving} className="w-full bg-[#f5a623] text-black font-semibold hover:brightness-110">
                    {saving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                    Create Shipment
                </Button>
            </div>
        </ModalOverlay>
    );
}

/* ═══════════════════════════════════════════════════════════════════ */
/*  SHIPMENT DETAIL MODAL with TIMELINE                              */
/* ═══════════════════════════════════════════════════════════════════ */
function ShipmentDetailModal({ shipmentId, onClose }: { shipmentId: string; onClose: () => void }) {
    const [data, setData] = useState<ShipmentData | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        (async () => {
            try {
                const res = await api.get(`/logistics/shipments/${shipmentId}`);
                setData(res.data);
            } catch (e) {
                console.error(e);
            } finally {
                setLoading(false);
            }
        })();
    }, [shipmentId]);

    if (loading) return (
        <ModalOverlay onClose={onClose}>
            <div className="flex justify-center py-20"><Loader2 className="h-8 w-8 animate-spin text-[#f5a623]" /></div>
        </ModalOverlay>
    );
    if (!data) return null;

    const st = getStatus(data.status);
    const originLabel = [data.origin?.city, data.origin?.country].filter(Boolean).join(", ") || "—";
    const destLabel = [data.destination?.city, data.destination?.country].filter(Boolean).join(", ") || "—";

    return (
        <ModalOverlay onClose={onClose}>
            <div className="bg-[#0a1628] border border-[#1e3a5f] rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto p-6 space-y-5">
                {/* Header */}
                <div className="flex justify-between items-start">
                    <div>
                        <div className="flex items-center gap-2">
                            <h2 className="text-lg font-bold text-white">{data.shipment_number}</h2>
                            <Badge className={`${st.bg} ${st.color} border-transparent text-[10px]`}>{st.label}</Badge>
                            {data.ai_extracted && (
                                <Badge className="bg-[#f5a623]/20 text-[#f5a623] border-[#f5a623]/30 text-[10px] px-1.5 py-0">AI Extracted</Badge>
                            )}
                        </div>
                        <p className="text-sm text-white/50 mt-1">{data.goods_description || "No description"}</p>
                    </div>
                    <button onClick={onClose} className="text-white/40 hover:text-white"><X className="h-5 w-5" /></button>
                </div>

                {/* Info grid */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                    <InfoCell label="Origin" value={originLabel} />
                    <InfoCell label="Destination" value={destLabel} />
                    <InfoCell label="Weight" value={data.total_weight_kg ? `${data.total_weight_kg} kg` : "—"} />
                    <InfoCell label="Packages" value={data.total_packages ? `${data.total_packages}` : "—"} />
                    <InfoCell label="Incoterms" value={data.incoterms || "—"} />
                    <InfoCell label="Customer" value={data.customer_name || "—"} />
                    <InfoCell label="Phone" value={data.customer_phone || "—"} />
                    <InfoCell label="Notified" value={data.notification_sent ? "Yes" : "No"} />
                </div>

                {/* Packages */}
                {data.packages && data.packages.length > 0 && (
                    <div>
                        <h3 className="text-sm font-semibold text-white/70 mb-2 flex items-center gap-1">
                            <Package className="h-4 w-4" /> Packages ({data.packages.length})
                        </h3>
                        <div className="space-y-1">
                            {data.packages.map((p) => (
                                <div key={p.id} className="flex items-center gap-3 bg-[#12253f]/50 rounded-lg px-3 py-2 text-xs text-white/60">
                                    <Package className="h-3 w-3 text-white/30" />
                                    <span>{p.contents || "Package"}</span>
                                    {p.weight_kg && <span className="text-white/40">{p.weight_kg} kg</span>}
                                    {p.barcode && <span className="text-white/30 font-mono">{p.barcode}</span>}
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Timeline */}
                <div>
                    <h3 className="text-sm font-semibold text-white/70 mb-3 flex items-center gap-1">
                        <Clock className="h-4 w-4" /> Timeline
                    </h3>
                    {data.events && data.events.length > 0 ? (
                        <div className="relative pl-6 border-l border-[#1e3a5f] space-y-4">
                            {data.events.map((ev, i) => {
                                const evSt = getStatus(ev.event_type);
                                return (
                                    <div key={ev.id} className="relative">
                                        <div className={`absolute -left-[29px] w-3 h-3 rounded-full border-2 border-[#0a1628] ${i === 0 ? "bg-[#f5a623]" : "bg-[#1e3a5f]"}`} />
                                        <div className="bg-[#12253f]/30 rounded-lg p-3">
                                            <div className="flex justify-between items-center">
                                                <span className={`text-xs font-semibold ${evSt.color}`}>{evSt.label}</span>
                                                <span className="text-[10px] text-white/30">
                                                    {ev.timestamp ? new Date(ev.timestamp).toLocaleString() : "—"}
                                                </span>
                                            </div>
                                            {ev.notes && <p className="text-xs text-white/50 mt-1">{ev.notes}</p>}
                                            {ev.actor && <p className="text-[10px] text-white/30 mt-1">Actor: {ev.actor}</p>}
                                            {ev.location_name && <p className="text-[10px] text-white/30">Location: {ev.location_name}</p>}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    ) : (
                        <p className="text-xs text-white/30">No events recorded yet</p>
                    )}
                </div>
            </div>
        </ModalOverlay>
    );
}

/* ─── Small helpers ──────────────────────────────────────────────── */
function InfoCell({ label, value }: { label: string; value: string }) {
    return (
        <div className="bg-[#12253f]/30 rounded-lg p-2.5">
            <div className="text-[10px] text-white/40 uppercase tracking-wider">{label}</div>
            <div className="text-sm text-white font-medium truncate">{value}</div>
        </div>
    );
}

function ModalOverlay({ onClose, children }: { onClose: () => void; children: React.ReactNode }) {
    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4" onClick={onClose}>
            <div onClick={(e) => e.stopPropagation()}>{children}</div>
        </div>
    );
}
