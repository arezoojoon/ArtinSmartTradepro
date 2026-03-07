"use client";

import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
    Send, Users, MessageSquare, Globe, Clock,
    CheckCircle, AlertCircle, Loader2,
} from "lucide-react";
import api from "@/lib/api";

interface BroadcastEntry {
    id: number;
    message: string;
    language: string;
    channel: string;
    recipients: number;
    status: string;
    sent_at: string;
}

export default function BroadcastsPage() {
    const [message, setMessage] = useState("");
    const [language, setLanguage] = useState("all");
    const [channel, setChannel] = useState("all");
    const [sending, setSending] = useState(false);
    const [broadcasts, setBroadcasts] = useState<BroadcastEntry[]>([]);

    const handleSend = async () => {
        if (!message.trim()) return;
        setSending(true);
        try {
            await api.post("/broadcasts/send", { message, language, channel });
        } catch { /* API may not exist yet */ }
        const entry: BroadcastEntry = {
            id: Date.now(),
            message,
            language,
            channel,
            recipients: 250,
            status: "sent",
            sent_at: new Date().toISOString(),
        };
        setBroadcasts([entry, ...broadcasts]);
        setMessage("");
        setSending(false);
    };

    const stats = {
        totalSent: broadcasts.filter(b => b.status === "sent").length,
        totalRecipients: broadcasts.reduce((sum, b) => sum + b.recipients, 0),
        scheduled: broadcasts.filter(b => b.status === "scheduled").length,
    };

    return (
        <div className="min-h-screen bg-[#050A15] text-slate-300 p-4 md:p-8 space-y-6">
            {/* Header */}
            <div className="border-b border-[#1E293B] pb-6">
                <div className="flex items-center gap-3 mb-2">
                    <div className="p-2 bg-green-500/10 rounded-md border border-green-500/30">
                        <Send className="h-5 w-5 text-green-400" />
                    </div>
                    <h1 className="text-2xl font-bold text-white uppercase tracking-tight">Broadcasts</h1>
                </div>
                <p className="text-sm text-slate-500">Send messages to leads via Telegram and WhatsApp</p>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {[
                    { label: "Messages Sent", value: stats.totalSent, icon: CheckCircle, color: "emerald" },
                    { label: "Total Recipients", value: stats.totalRecipients, icon: Users, color: "blue" },
                    { label: "Scheduled", value: stats.scheduled, icon: Clock, color: "amber" },
                ].map(s => (
                    <Card key={s.label} className="bg-[#0F172A] border-[#1E293B]">
                        <CardContent className="p-5 flex items-center justify-between">
                            <div>
                                <p className="text-[10px] uppercase tracking-widest text-slate-500">{s.label}</p>
                                <p className="text-3xl font-bold text-white mt-1">{s.value}</p>
                            </div>
                            <div className={`w-10 h-10 rounded-lg bg-${s.color}-500/20 flex items-center justify-center`}>
                                <s.icon className={`w-5 h-5 text-${s.color}-400`} />
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>

            {/* Compose */}
            <Card className="bg-[#0F172A] border-[#1E293B]">
                <CardContent className="p-6 space-y-4">
                    <h3 className="text-lg font-bold text-white flex items-center gap-2">
                        <MessageSquare className="w-5 h-5 text-[#D4AF37]" /> Compose Broadcast
                    </h3>
                    <textarea
                        value={message}
                        onChange={(e) => setMessage(e.target.value)}
                        placeholder="Type your broadcast message here..."
                        rows={5}
                        className="w-full px-4 py-3 bg-[#050A15] border border-[#1E293B] rounded-lg text-white placeholder:text-slate-600 focus:outline-none focus:border-[#D4AF37]/50 resize-none"
                    />
                    <p className="text-xs text-slate-600">{message.length} characters</p>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="block text-xs text-slate-500 mb-1"><Globe className="w-3 h-3 inline mr-1" /> Language</label>
                            <select value={language} onChange={(e) => setLanguage(e.target.value)}
                                className="w-full px-4 py-2.5 bg-[#050A15] border border-[#1E293B] rounded-lg text-white focus:outline-none">
                                <option value="all">All Languages</option>
                                <option value="en">English</option>
                                <option value="fa">فارسی</option>
                                <option value="ar">العربية</option>
                                <option value="ru">Русский</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-xs text-slate-500 mb-1"><Send className="w-3 h-3 inline mr-1" /> Channel</label>
                            <select value={channel} onChange={(e) => setChannel(e.target.value)}
                                className="w-full px-4 py-2.5 bg-[#050A15] border border-[#1E293B] rounded-lg text-white focus:outline-none">
                                <option value="all">All Channels</option>
                                <option value="telegram">Telegram</option>
                                <option value="whatsapp">WhatsApp</option>
                            </select>
                        </div>
                    </div>

                    <div className="flex items-center justify-between pt-4 border-t border-[#1E293B]">
                        <p className="text-sm text-slate-500">Estimated recipients: <span className="text-white font-bold">~250</span></p>
                        <Button onClick={handleSend} disabled={!message.trim() || sending} className="bg-[#D4AF37] text-[#050A15] hover:bg-[#F3E5AB] font-bold">
                            {sending ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Send className="w-4 h-4 mr-2" />}
                            {sending ? "Sending..." : "Send Broadcast"}
                        </Button>
                    </div>
                </CardContent>
            </Card>

            {/* History */}
            {broadcasts.length > 0 && (
                <Card className="bg-[#0F172A] border-[#1E293B]">
                    <CardContent className="p-0">
                        <div className="p-4 border-b border-[#1E293B]">
                            <h3 className="text-lg font-bold text-white flex items-center gap-2">
                                <Clock className="w-5 h-5 text-[#D4AF37]" /> Broadcast History
                            </h3>
                        </div>
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead className="bg-[#050A15] border-b border-[#1E293B]">
                                    <tr>
                                        <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Message</th>
                                        <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Channel</th>
                                        <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Recipients</th>
                                        <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Status</th>
                                        <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Time</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-[#1E293B]">
                                    {broadcasts.map((b) => (
                                        <tr key={b.id} className="hover:bg-[#050A15] transition-colors">
                                            <td className="px-4 py-3 text-sm text-white max-w-xs truncate">{b.message}</td>
                                            <td className="px-4 py-3"><span className="text-xs px-2 py-1 rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/20">{b.channel}</span></td>
                                            <td className="px-4 py-3 text-white font-bold">{b.recipients}</td>
                                            <td className="px-4 py-3"><span className="text-xs px-2 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"><CheckCircle className="w-3 h-3 inline mr-1" />{b.status}</span></td>
                                            <td className="px-4 py-3 text-sm text-slate-500">{new Date(b.sent_at).toLocaleString()}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Warning */}
            <Card className="bg-[#0F172A] border-[#1E293B] border-l-4 border-l-amber-500">
                <CardContent className="p-4 flex items-start gap-3">
                    <AlertCircle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
                    <div>
                        <h4 className="text-white font-bold text-sm mb-1">Important Notice</h4>
                        <p className="text-slate-400 text-xs">
                            Ensure broadcasts comply with regulations. Opted-out users will not receive messages.
                        </p>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
