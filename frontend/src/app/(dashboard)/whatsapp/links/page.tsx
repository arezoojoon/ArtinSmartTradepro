"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
    Link2, Copy, ExternalLink, Plus
} from "lucide-react";

export default function DeepLinksPage() {
    const [links, setLinks] = useState<any[]>([]);
    const [newRef, setNewRef] = useState("");
    const [generating, setGenerating] = useState(false);

    useEffect(() => {
        const fetchLinks = async () => {
            try {
                const userData = JSON.parse(localStorage.getItem("user") || "{}");
                const tenantId = userData.tenant_id || "";
                const res = await api.get(`/api/v1/waha/deeplinks?tenant_id=${tenantId}`);
                const formattedLinks = (res.data || []).map((item: any) => ({
                    id: item.ref,
                    ref: item.ref,
                    deeplink: item.url || `https://wa.me/?text=start%20${item.ref}`,
                    created_at: item.created_at
                }));
                setLinks(formattedLinks);
            } catch (e) {
                console.error("Failed to load links:", e);
            }
        };
        fetchLinks();
    }, []);

    const generateLink = async () => {
        if (!newRef.trim()) return;
        setGenerating(true);
        try {
            const userData = JSON.parse(localStorage.getItem("user") || "{}");
            const tenantId = userData.tenant_id || "";
            const res = await api.post(`/api/v1/waha/deeplink?ref=${encodeURIComponent(newRef)}&tenant_id=${tenantId}`);
            const newLink = {
                id: Date.now(),
                ref: res.data.ref,
                deeplink: res.data.url,
                created_at: new Date().toISOString()
            };
            setLinks(prev => [newLink, ...prev]);
            setNewRef("");
        } catch (e) {
            console.error("Failed to generate link:", e);
        }
        setGenerating(false);
    };

    const copyToClipboard = (text: string) => {
        navigator.clipboard.writeText(text);
    };

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold flex items-center gap-2">
                    <Link2 className="h-8 w-8 text-cyan-400" />
                    Deep Links
                </h1>
                <p className="text-gray-400 mt-1">Generate unique WhatsApp start links per campaign or channel</p>
            </div>

            {/* Generator */}
            <Card className="bg-navy-900 border-navy-800">
                <CardHeader>
                    <CardTitle>Generate New Link</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="flex gap-4">
                        <Input
                            placeholder="Reference code (e.g. gulfood2026, linkedin_ad)"
                            value={newRef}
                            className="bg-navy-950 border-navy-700 flex-1"
                            onChange={e => setNewRef(e.target.value)}
                            onKeyDown={e => e.key === "Enter" && generateLink()}
                        />
                        <Button onClick={generateLink} disabled={generating || !newRef.trim()}
                            className="bg-cyan-600 hover:bg-cyan-500">
                            <Plus className="h-4 w-4 mr-2" />
                            Generate
                        </Button>
                    </div>
                </CardContent>
            </Card>

            {/* Links List */}
            {links.length === 0 ? (
                <Card className="bg-navy-900 border-navy-800">
                    <CardContent className="py-16 text-center">
                        <Link2 className="h-16 w-16 mx-auto mb-4 text-gray-700" />
                        <p className="text-gray-500">No deep links generated yet. Create one above.</p>
                        <p className="text-xs text-gray-600 mt-2">
                            Each link tracks which campaign or channel brought the user to your bot.
                        </p>
                    </CardContent>
                </Card>
            ) : (
                <div className="space-y-4">
                    {links.map((link) => (
                        <Card key={link.id} className="bg-navy-900 border-navy-800">
                            <CardContent className="pt-4">
                                <div className="flex justify-between items-start">
                                    <div className="flex-1">
                                        <div className="flex items-center gap-2 mb-2">
                                            <Badge className="bg-cyan-900/60 text-cyan-300">
                                                ref: {link.ref}
                                            </Badge>
                                        </div>
                                        <div className="bg-navy-950 rounded-lg p-3 overflow-hidden">
                                            <code className="text-emerald-400 text-sm break-all">
                                                {link.deeplink}
                                            </code>
                                        </div>
                                    </div>
                                    <div className="flex gap-2 ml-4">
                                        <Button variant="outline" size="sm"
                                            className="border-navy-700 text-gray-400 hover:text-white"
                                            onClick={() => copyToClipboard(link.deeplink)}>
                                            <Copy className="h-4 w-4" />
                                        </Button>
                                        <Button variant="outline" size="sm"
                                            className="border-navy-700 text-gray-400 hover:text-white"
                                            onClick={() => window.open(link.deeplink, '_blank')}>
                                            <ExternalLink className="h-4 w-4" />
                                        </Button>
                                    </div>
                                </div>
                                <p className="text-xs text-gray-600 mt-2">
                                    Users who click this link will start the bot with tracking code &quot;{link.ref}&quot;
                                </p>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            )}
        </div>
    );
}
