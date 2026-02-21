"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
    Link2, Copy, ExternalLink, Plus, Loader2
} from "lucide-react";

interface DeepLink {
    ref: string;
    tenant_id: string;
    url?: string;
    label?: string;
    is_active: boolean;
    expires_at?: string;
    created_at: string;
}

export default function DeepLinksPage() {
    const [links, setLinks] = useState<DeepLink[]>([]);
    const [loading, setLoading] = useState(true);
    const [newRef, setNewRef] = useState("");
    const [newLabel, setNewLabel] = useState("");
    const [generating, setGenerating] = useState(false);

    // Load existing links on mount
    useEffect(() => {
        loadLinks();
    }, []);

    const loadLinks = async () => {
        try {
            const res = await api.get("/waha/deeplinks");
            setLinks(res.data || []);
        } catch (e) {
            console.error("Failed to load deeplinks:", e);
        } finally {
            setLoading(false);
        }
    };

    const generateLink = async () => {
        if (!newRef.trim()) return;
        setGenerating(true);
        try {
            const res = await api.post(`/waha/deeplink?ref=${encodeURIComponent(newRef)}&tenant_id=${links[0]?.tenant_id || ""}&label=${encodeURIComponent(newLabel)}`);
            await loadLinks(); // Reload from server
            setNewRef("");
            setNewLabel("");
        } catch (e: any) {
            if (e?.data?.detail) {
                alert(e.data.detail);
            } else {
                alert("Failed to create link");
            }
        }
        setGenerating(false);
    };

    const copyToClipboard = (text: string) => {
        navigator.clipboard.writeText(text);
    };

    const getWhatsAppUrl = (ref: string) => {
        // Construct the wa.me link (phone number comes from backend settings)
        return `https://wa.me/?text=start%20${ref}`;
    };

    return (
        <div className="p-8 min-h-screen text-white">
            <div className="mb-8">
                <h1 className="text-3xl font-bold flex items-center gap-2">
                    <Link2 className="h-8 w-8 text-cyan-400" />
                    Deep Links
                </h1>
                <p className="text-gray-400">لینک‌های واتساپ برای هر تنت — فقط از طریق این لینک‌ها ربات فعال می‌شود</p>
            </div>

            {/* Generator */}
            <Card className="bg-navy-900 border-navy-800 mb-8">
                <CardHeader>
                    <CardTitle className="text-white">ساخت لینک جدید</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="flex gap-4">
                        <Input
                            placeholder="کد رفرنس (مثلاً gulfood2026, linkedin_ad)"
                            value={newRef}
                            className="bg-navy-950 border-navy-700 flex-1"
                            onChange={e => setNewRef(e.target.value)}
                            onKeyDown={e => e.key === "Enter" && generateLink()}
                        />
                        <Input
                            placeholder="برچسب (اختیاری)"
                            value={newLabel}
                            className="bg-navy-950 border-navy-700 w-48"
                            onChange={e => setNewLabel(e.target.value)}
                        />
                        <Button onClick={generateLink} disabled={generating || !newRef.trim()}
                            className="bg-cyan-600 hover:bg-cyan-500">
                            {generating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4 mr-2" />}
                            ساختن
                        </Button>
                    </div>
                </CardContent>
            </Card>

            {/* Links List */}
            {loading ? (
                <div className="flex justify-center py-16">
                    <Loader2 className="h-8 w-8 animate-spin text-cyan-400" />
                </div>
            ) : links.length === 0 ? (
                <Card className="bg-navy-900 border-navy-800">
                    <CardContent className="py-16 text-center">
                        <Link2 className="h-16 w-16 mx-auto mb-4 text-gray-700" />
                        <p className="text-gray-500">هنوز لینکی ساخته نشده. با ساخت تنت جدید، لینک تأسیس خودکار ایجاد می‌شود.</p>
                    </CardContent>
                </Card>
            ) : (
                <div className="space-y-4">
                    {links.map((link, i) => {
                        const url = link.url || getWhatsAppUrl(link.ref);
                        return (
                            <Card key={link.ref + i} className="bg-navy-900 border-navy-800">
                                <CardContent className="pt-4">
                                    <div className="flex justify-between items-start">
                                        <div className="flex-1">
                                            <div className="flex items-center gap-2 mb-2">
                                                <Badge className="bg-cyan-900/60 text-cyan-300">
                                                    ref: {link.ref}
                                                </Badge>
                                                {link.label && (
                                                    <Badge variant="outline" className="text-gray-400 text-xs">
                                                        {link.label}
                                                    </Badge>
                                                )}
                                                <Badge variant="outline" className={link.is_active ? "text-green-400 border-green-800" : "text-red-400 border-red-800"}>
                                                    {link.is_active ? "فعال" : "غیرفعال"}
                                                </Badge>
                                            </div>
                                            <div className="bg-navy-950 rounded-lg p-3 overflow-hidden">
                                                <code className="text-emerald-400 text-sm break-all">
                                                    {url}
                                                </code>
                                            </div>
                                            <p className="text-xs text-gray-600 mt-2">
                                                ساخته شده: {new Date(link.created_at).toLocaleDateString("fa-IR")}
                                                {link.expires_at && ` — انقضا: ${new Date(link.expires_at).toLocaleDateString("fa-IR")}`}
                                            </p>
                                        </div>
                                        <div className="flex gap-2 ml-4">
                                            <Button variant="outline" size="sm"
                                                className="border-navy-700 text-gray-400 hover:text-white"
                                                onClick={() => copyToClipboard(url)}>
                                                <Copy className="h-4 w-4" />
                                            </Button>
                                            <Button variant="outline" size="sm"
                                                className="border-navy-700 text-gray-400 hover:text-white"
                                                onClick={() => window.open(url, '_blank')}>
                                                <ExternalLink className="h-4 w-4" />
                                            </Button>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
