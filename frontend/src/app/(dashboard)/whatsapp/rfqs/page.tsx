"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { MessageSquare, Plus, Send, X, Loader2, Clock, CheckCircle2, Phone, FileText, Users } from "lucide-react";
import api from "@/lib/api";

interface RFQ {
    id: string;
    supplier_name: string;
    supplier_phone: string;
    product: string;
    quantity: string;
    status: string;
    sent_at?: string;
    replied_at?: string;
    message?: string;
}

export default function WhatsAppRFQsPage() {
    const [rfqs, setRfqs] = useState<RFQ[]>([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [form, setForm] = useState({ supplier_name: "", supplier_phone: "", product: "", quantity: "", notes: "" });
    const [saving, setSaving] = useState(false);

    const fetchRFQs = async () => {
        try {
            const res = await api.get("/whatsapp/rfqs");
            setRfqs(Array.isArray(res.data) ? res.data : []);
        } catch { setRfqs([]); }
        finally { setLoading(false); }
    };

    useEffect(() => { fetchRFQs(); }, []);

    const handleSend = async () => {
        if (!form.supplier_name || !form.supplier_phone || !form.product) return;
        setSaving(true);
        try {
            await api.post("/whatsapp/rfqs", {
                supplier_name: form.supplier_name,
                supplier_phone: form.supplier_phone,
                product: form.product,
                quantity: form.quantity,
                notes: form.notes || undefined,
            });
            setShowModal(false);
            setForm({ supplier_name: "", supplier_phone: "", product: "", quantity: "", notes: "" });
            fetchRFQs();
        } catch (e) { console.error("Failed to send RFQ", e); }
        finally { setSaving(false); }
    };

    const statusBadge = (status: string) => {
        switch (status) {
            case "sent": return <Badge className="bg-blue-500/20 text-blue-400 text-[10px]"><Send className="h-3 w-3 mr-1" />Sent</Badge>;
            case "replied": return <Badge className="bg-emerald-500/20 text-emerald-400 text-[10px]"><CheckCircle2 className="h-3 w-3 mr-1" />Replied</Badge>;
            case "expired": return <Badge className="bg-rose-500/20 text-rose-400 text-[10px]"><Clock className="h-3 w-3 mr-1" />Expired</Badge>;
            default: return <Badge className="bg-amber-500/20 text-amber-400 text-[10px]"><Clock className="h-3 w-3 mr-1" />Pending</Badge>;
        }
    };

    const pending = rfqs.filter(r => r.status === "pending" || r.status === "sent").length;
    const replied = rfqs.filter(r => r.status === "replied").length;

    return (
        <div className="space-y-6 p-4 md:p-8 max-w-[1200px] mx-auto">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold flex items-center gap-2 text-white">
                        <MessageSquare className="h-6 w-6 text-green-400" /> WhatsApp RFQs
                    </h1>
                    <p className="text-white/50 text-sm">Send and track RFQs via WhatsApp</p>
                </div>
                <Button onClick={() => setShowModal(true)} className="bg-green-600 text-white hover:bg-green-700">
                    <Send className="h-4 w-4 mr-2" /> New RFQ
                </Button>
            </div>

            {/* Stats */}
            <div className="grid gap-4 sm:grid-cols-3">
                <Card className="bg-[#0e1e33] border-[#1e3a5f]"><CardContent className="p-4 flex items-center justify-between">
                    <div><p className="text-white/50 text-xs uppercase">Total RFQs</p><p className="text-xl font-bold text-white mt-1">{rfqs.length}</p></div>
                    <FileText className="h-7 w-7 text-blue-400/40" />
                </CardContent></Card>
                <Card className="bg-[#0e1e33] border-[#1e3a5f]"><CardContent className="p-4 flex items-center justify-between">
                    <div><p className="text-white/50 text-xs uppercase">Awaiting Reply</p><p className="text-xl font-bold text-amber-400 mt-1">{pending}</p></div>
                    <Clock className="h-7 w-7 text-amber-400/40" />
                </CardContent></Card>
                <Card className="bg-[#0e1e33] border-[#1e3a5f]"><CardContent className="p-4 flex items-center justify-between">
                    <div><p className="text-white/50 text-xs uppercase">Replied</p><p className="text-xl font-bold text-emerald-400 mt-1">{replied}</p></div>
                    <CheckCircle2 className="h-7 w-7 text-emerald-400/40" />
                </CardContent></Card>
            </div>

            {/* RFQ List */}
            <Card className="bg-[#0e1e33] border-[#1e3a5f]">
                <CardHeader><CardTitle className="text-white text-lg">RFQ History</CardTitle></CardHeader>
                <CardContent>
                    {loading ? (
                        <div className="flex justify-center py-12"><Loader2 className="h-5 w-5 animate-spin text-white/40" /></div>
                    ) : rfqs.length === 0 ? (
                        <div className="text-center py-12">
                            <MessageSquare className="h-12 w-12 mx-auto mb-3 text-white/10" />
                            <p className="text-white/40 text-sm">No RFQs sent yet</p>
                            <Button onClick={() => setShowModal(true)} variant="link" className="text-green-400 mt-2">Send your first RFQ</Button>
                        </div>
                    ) : (
                        <div className="divide-y divide-white/5">
                            {rfqs.map(rfq => (
                                <div key={rfq.id} className="py-4 flex items-center justify-between">
                                    <div className="flex items-center gap-4">
                                        <div className="p-2 bg-green-500/10 rounded-lg"><Phone className="h-4 w-4 text-green-400" /></div>
                                        <div>
                                            <p className="text-white font-medium text-sm">{rfq.supplier_name}</p>
                                            <p className="text-white/40 text-xs">{rfq.product} — Qty: {rfq.quantity}</p>
                                            <p className="text-white/30 text-xs mt-0.5">{rfq.supplier_phone}</p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-3">
                                        {rfq.sent_at && <span className="text-white/30 text-xs">{new Date(rfq.sent_at).toLocaleDateString()}</span>}
                                        {statusBadge(rfq.status)}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Modal */}
            {showModal && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50" onClick={() => setShowModal(false)}>
                    <div className="bg-[#0e1e33] border border-[#1e3a5f] rounded-xl p-6 w-full max-w-md space-y-4" onClick={e => e.stopPropagation()}>
                        <div className="flex items-center justify-between">
                            <h3 className="text-white font-bold text-lg">Send RFQ via WhatsApp</h3>
                            <button onClick={() => setShowModal(false)}><X className="h-5 w-5 text-white/40" /></button>
                        </div>
                        <div className="space-y-3">
                            <Input placeholder="Supplier Name *" value={form.supplier_name} onChange={e => setForm(p => ({ ...p, supplier_name: e.target.value }))} className="bg-white/5 border-white/10 text-white" />
                            <Input placeholder="Phone Number * (e.g. +971...)" value={form.supplier_phone} onChange={e => setForm(p => ({ ...p, supplier_phone: e.target.value }))} className="bg-white/5 border-white/10 text-white" />
                            <Input placeholder="Product / Item *" value={form.product} onChange={e => setForm(p => ({ ...p, product: e.target.value }))} className="bg-white/5 border-white/10 text-white" />
                            <Input placeholder="Quantity" value={form.quantity} onChange={e => setForm(p => ({ ...p, quantity: e.target.value }))} className="bg-white/5 border-white/10 text-white" />
                            <Input placeholder="Additional Notes" value={form.notes} onChange={e => setForm(p => ({ ...p, notes: e.target.value }))} className="bg-white/5 border-white/10 text-white" />
                        </div>
                        <Button onClick={handleSend} disabled={saving || !form.supplier_name || !form.supplier_phone || !form.product} className="w-full bg-green-600 text-white hover:bg-green-700">
                            {saving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Send className="h-4 w-4 mr-2" />} Send RFQ
                        </Button>
                    </div>
                </div>
            )}
        </div>
    );
}
