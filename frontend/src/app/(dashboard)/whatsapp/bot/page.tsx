"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Bot, RefreshCw, Lock, Unlock } from "lucide-react";

export default function BotSessionsPage() {
    const [sessions, setSessions] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchSessions = async () => {
        setLoading(true);
        try {
            const userData = JSON.parse(localStorage.getItem("user") || "{}");
            const tenantId = userData.tenant_id || "";
            const res = await api.get(`/api/v1/waha/sessions?tenant_id=${tenantId}`);
            setSessions(res.data || []);
        } catch (e) {
            console.error("Failed to load sessions:", e);
        }
        setLoading(false);
    };

    useEffect(() => { fetchSessions(); }, []);

    const toggleLock = async (sessionId: string, isLocked: boolean) => {
        try {
            const action = isLocked ? "unlock" : "lock";
            await api.post(`/api/v1/waha/sessions/${sessionId}/${action}`);
            fetchSessions();
        } catch (e) {
            console.error("Failed to toggle lock:", e);
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold flex items-center gap-2">
                        <Bot className="h-8 w-8 text-green-400" />
                        Bot Sessions
                    </h1>
                    <p className="text-gray-400 mt-1">Monitor active WhatsApp bot conversations</p>
                </div>
                <Button variant="outline" className="border-navy-700" onClick={fetchSessions}>
                    <RefreshCw className="h-4 w-4 mr-2" /> Refresh
                </Button>
            </div>

            {loading ? (
                <div className="text-center py-16 text-gray-500">Loading sessions...</div>
            ) : sessions.length === 0 ? (
                <Card className="bg-[#0e1e33] border-[#1e3a5f]">
                    <CardContent className="py-16 text-center">
                        <Bot className="h-16 w-16 mx-auto mb-4 text-gray-700" />
                        <p className="text-gray-500">No active bot sessions.</p>
                        <p className="text-xs text-gray-600 mt-2">
                            Sessions are created when users interact with the bot via deep links.
                        </p>
                    </CardContent>
                </Card>
            ) : (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {sessions.map((s: any) => (
                        <Card key={s.id} className="bg-[#0e1e33] border-[#1e3a5f]">
                            <CardContent className="pt-4">
                                <div className="flex items-center justify-between mb-3">
                                    <span className="font-semibold text-white">{s.name || s.phone}</span>
                                    <Badge className={s.locked_for_human ? "bg-red-900/50 text-red-400" : "bg-green-900/50 text-green-400"}>
                                        {s.locked_for_human ? "🔒 Human" : "🤖 Bot"}
                                    </Badge>
                                </div>
                                <div className="text-xs text-gray-400 space-y-1">
                                    <p>📱 {s.phone}</p>
                                    <p>🔗 Ref: {s.deeplink_ref || "—"}</p>
                                    <p>🌐 Lang: {s.language || "en"}</p>
                                    <p>📊 State: {s.state}</p>
                                    <p>🤖 AI Calls: {s.ai_calls_today || 0}</p>
                                </div>
                                <div className="mt-3 pt-3 border-t border-navy-700">
                                    <Button
                                        size="sm"
                                        variant="outline"
                                        className="w-full border-navy-700"
                                        onClick={() => toggleLock(s.id, s.locked_for_human)}
                                    >
                                        {s.locked_for_human ? (
                                            <><Unlock className="h-3 w-3 mr-1" /> Release to Bot</>
                                        ) : (
                                            <><Lock className="h-3 w-3 mr-1" /> Take Over (Human)</>
                                        )}
                                    </Button>
                                </div>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            )}
        </div>
    );
}
