"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
    QrCode, Download, Smartphone, MessageCircle,
    RefreshCw, AlertCircle, CheckCircle, Loader2, Copy,
} from "lucide-react";
import api from "@/lib/api";

export default function QRCapturePage() {
    const [loading, setLoading] = useState(true);
    const [telegramLink, setTelegramLink] = useState<string | null>(null);
    const [whatsappLink, setWhatsappLink] = useState<string | null>(null);
    const [telegramConfigured, setTelegramConfigured] = useState(false);
    const [whatsappConfigured, setWhatsappConfigured] = useState(false);
    const [botUsername, setBotUsername] = useState<string | null>(null);

    const fetchLinks = useCallback(async () => {
        setLoading(true);
        try {
            const [waRes, tgRes] = await Promise.allSettled([
                api.get("/qr/whatsapp-link"),
                api.get("/qr/telegram-link"),
            ]);
            if (waRes.status === "fulfilled" && waRes.value.data?.whatsapp_link) {
                setWhatsappLink(waRes.value.data.whatsapp_link);
                setWhatsappConfigured(true);
            }
            if (tgRes.status === "fulfilled" && tgRes.value.data?.telegram_link) {
                setTelegramLink(tgRes.value.data.telegram_link);
                setTelegramConfigured(true);
                setBotUsername(tgRes.value.data.bot_username);
            } else if (tgRes.status === "fulfilled" && tgRes.value.data?.configured) {
                setTelegramConfigured(true);
            }
        } catch (e) {
            console.error("QR fetch failed:", e);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { fetchLinks(); }, [fetchLinks]);

    const copyLink = (link: string, type: string) => {
        navigator.clipboard.writeText(link);
        alert(`${type} link copied!`);
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-[#050A15] flex items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-[#D4AF37]" />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-[#050A15] text-slate-300 p-4 md:p-8 space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between border-b border-[#1E293B] pb-6">
                <div>
                    <div className="flex items-center gap-3 mb-2">
                        <div className="p-2 bg-[#D4AF37]/10 rounded-md border border-[#D4AF37]/30">
                            <QrCode className="h-5 w-5 text-[#D4AF37]" />
                        </div>
                        <h1 className="text-2xl font-bold text-white uppercase tracking-tight">QR Capture</h1>
                    </div>
                    <p className="text-sm text-slate-500">Auto-generated QR codes for your exhibition booth</p>
                </div>
                <Button variant="outline" size="sm" onClick={fetchLinks} className="border-slate-700 text-slate-400">
                    <RefreshCw className="w-4 h-4 mr-2" /> Refresh
                </Button>
            </div>

            {/* Instructions */}
            <Card className="bg-[#0F172A] border-[#1E293B] border-l-4 border-l-[#D4AF37]">
                <CardContent className="p-5">
                    <h3 className="text-lg font-bold text-white mb-3 flex items-center gap-2">
                        <Smartphone className="w-5 h-5 text-[#D4AF37]" /> How to Use
                    </h3>
                    <ol className="space-y-2 text-sm text-slate-400 list-decimal list-inside">
                        <li>QR codes are generated from your bot configuration</li>
                        <li>Download and print them at high resolution (300+ DPI)</li>
                        <li>Display at your exhibition booth — recommend 10cm × 10cm minimum</li>
                        <li>Visitors scan to start chatting with your AI bot</li>
                    </ol>
                </CardContent>
            </Card>

            {/* QR Cards Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Telegram QR */}
                <Card className="bg-[#0F172A] border-[#1E293B]">
                    <CardContent className="p-6">
                        <div className="flex items-center gap-3 mb-4">
                            <div className="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center">
                                <MessageCircle className="w-5 h-5 text-blue-400" />
                            </div>
                            <div className="flex-1">
                                <h3 className="text-lg font-bold text-white">Telegram Bot</h3>
                                <p className="text-xs text-slate-500">Connect via Telegram</p>
                            </div>
                            {telegramConfigured ? <CheckCircle className="w-5 h-5 text-emerald-400" /> : <AlertCircle className="w-5 h-5 text-amber-400" />}
                        </div>

                        {telegramLink ? (
                            <>
                                <div className="mb-4 p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                                    <p className="text-blue-300 text-sm"><strong>Bot:</strong> @{botUsername}</p>
                                    <p className="text-blue-200/60 text-xs mt-1 break-all">{telegramLink}</p>
                                </div>
                                <div className="bg-white p-6 rounded-xl mb-4 flex items-center justify-center">
                                    <div className="w-48 h-48 bg-slate-100 rounded-lg flex items-center justify-center">
                                        <QrCode className="w-24 h-24 text-blue-500" />
                                    </div>
                                </div>
                                <div className="grid grid-cols-2 gap-3">
                                    <Button onClick={() => window.open(telegramLink, '_blank')} className="bg-[#D4AF37] text-[#050A15] hover:bg-[#F3E5AB] font-bold">
                                        <Download className="w-4 h-4 mr-2" /> Download
                                    </Button>
                                    <Button variant="outline" onClick={() => copyLink(telegramLink, "Telegram")} className="border-blue-500/30 text-blue-400 hover:bg-blue-500/10">
                                        <Copy className="w-4 h-4 mr-2" /> Copy Link
                                    </Button>
                                </div>
                            </>
                        ) : (
                            <div className="text-center p-8 bg-amber-500/5 border border-amber-500/20 rounded-lg">
                                <AlertCircle className="w-10 h-10 text-amber-400 mx-auto mb-3" />
                                <p className="text-amber-300 font-medium text-sm">Telegram Bot Not Configured</p>
                                <p className="text-slate-500 text-xs mt-1">Go to Settings → Bot Configuration to set up</p>
                            </div>
                        )}
                    </CardContent>
                </Card>

                {/* WhatsApp QR */}
                <Card className="bg-[#0F172A] border-[#1E293B]">
                    <CardContent className="p-6">
                        <div className="flex items-center gap-3 mb-4">
                            <div className="w-10 h-10 rounded-lg bg-green-500/20 flex items-center justify-center">
                                <MessageCircle className="w-5 h-5 text-green-400" />
                            </div>
                            <div className="flex-1">
                                <h3 className="text-lg font-bold text-white">WhatsApp Bot</h3>
                                <p className="text-xs text-slate-500">Connect via WhatsApp</p>
                            </div>
                            {whatsappConfigured ? <CheckCircle className="w-5 h-5 text-emerald-400" /> : <AlertCircle className="w-5 h-5 text-amber-400" />}
                        </div>

                        {whatsappLink ? (
                            <>
                                <div className="mb-4 p-3 bg-green-500/10 border border-green-500/20 rounded-lg">
                                    <p className="text-green-300 text-sm font-bold">WhatsApp Deep Link</p>
                                    <p className="text-green-200/60 text-xs mt-1 break-all">{whatsappLink}</p>
                                </div>
                                <div className="bg-white p-6 rounded-xl mb-4 flex items-center justify-center">
                                    <div className="w-48 h-48 bg-slate-100 rounded-lg flex items-center justify-center">
                                        <QrCode className="w-24 h-24 text-green-500" />
                                    </div>
                                </div>
                                <div className="grid grid-cols-2 gap-3">
                                    <Button onClick={() => window.open(whatsappLink, '_blank')} className="bg-[#D4AF37] text-[#050A15] hover:bg-[#F3E5AB] font-bold">
                                        <Download className="w-4 h-4 mr-2" /> Download
                                    </Button>
                                    <Button variant="outline" onClick={() => copyLink(whatsappLink, "WhatsApp")} className="border-green-500/30 text-green-400 hover:bg-green-500/10">
                                        <Copy className="w-4 h-4 mr-2" /> Copy Link
                                    </Button>
                                </div>
                            </>
                        ) : (
                            <div className="text-center p-8 bg-amber-500/5 border border-amber-500/20 rounded-lg">
                                <AlertCircle className="w-10 h-10 text-amber-400 mx-auto mb-3" />
                                <p className="text-amber-300 font-medium text-sm">WhatsApp Bot Not Configured</p>
                                <p className="text-slate-500 text-xs mt-1">Contact admin to set up WhatsApp integration</p>
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
