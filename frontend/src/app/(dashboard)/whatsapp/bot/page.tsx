"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
    Bot, Settings, Clock, Globe, Link, Shield, Zap, Save
} from "lucide-react";

export default function BotSettingsPage() {
    const [config, setConfig] = useState({
        waha_url: "http://localhost:3000",
        waha_session: "default",
        webhook_secret: "",
        phone_number: "",
        default_language: "en",
        working_hours_start: "09:00",
        working_hours_end: "18:00",
        auto_followup_hours: 24,
        booking_enabled: true,
        ai_analysis_enabled: true
    });
    const [sessions, setSessions] = useState<any[]>([]);
    const [saved, setSaved] = useState(false);

    useEffect(() => {
        api.get("/api/v1/waha/sessions")
            .then(res => setSessions(res.data))
            .catch(() => { });
    }, []);

    const handleSave = async () => {
        setSaved(true);
        setTimeout(() => setSaved(false), 2000);
    };

    return (
        <div className="p-8 bg-black min-h-screen text-white">
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-3xl font-bold flex items-center gap-2">
                        <Bot className="h-8 w-8 text-emerald-400" />
                        WhatsApp Bot Settings
                    </h1>
                    <p className="text-gray-400">Configure WAHA integration and bot behavior</p>
                </div>
                <Button onClick={handleSave} className="bg-emerald-600 hover:bg-emerald-500">
                    <Save className="h-4 w-4 mr-2" />
                    {saved ? "✓ Saved" : "Save Settings"}
                </Button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* WAHA Connection */}
                <Card className="bg-navy-900 border-navy-800">
                    <CardHeader>
                        <CardTitle className="text-white flex items-center gap-2">
                            <Link className="h-5 w-5 text-blue-400" />
                            WAHA Connection
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div>
                            <label className="text-sm text-gray-400">WAHA API URL</label>
                            <Input value={config.waha_url} className="bg-navy-950 border-navy-700 mt-1"
                                onChange={e => setConfig({ ...config, waha_url: e.target.value })} />
                        </div>
                        <div>
                            <label className="text-sm text-gray-400">Session Name</label>
                            <Input value={config.waha_session} className="bg-navy-950 border-navy-700 mt-1"
                                onChange={e => setConfig({ ...config, waha_session: e.target.value })} />
                        </div>
                        <div>
                            <label className="text-sm text-gray-400">Webhook Secret Token</label>
                            <Input type="password" value={config.webhook_secret} className="bg-navy-950 border-navy-700 mt-1"
                                placeholder="Secret for verifying incoming webhooks"
                                onChange={e => setConfig({ ...config, webhook_secret: e.target.value })} />
                        </div>
                        <div>
                            <label className="text-sm text-gray-400">WhatsApp Phone Number</label>
                            <Input value={config.phone_number} className="bg-navy-950 border-navy-700 mt-1"
                                placeholder="+971XXXXXXXXX"
                                onChange={e => setConfig({ ...config, phone_number: e.target.value })} />
                        </div>
                        <div className="p-3 bg-navy-950 rounded-lg text-sm">
                            <p className="text-gray-500">Webhook URL (set this in WAHA):</p>
                            <code className="text-emerald-400 text-xs break-all">
                                {typeof window !== 'undefined' ? window.location.origin : ''}/api/v1/waha/webhook
                            </code>
                        </div>
                    </CardContent>
                </Card>

                {/* Bot Behavior */}
                <Card className="bg-navy-900 border-navy-800">
                    <CardHeader>
                        <CardTitle className="text-white flex items-center gap-2">
                            <Settings className="h-5 w-5 text-gold-500" />
                            Bot Behavior
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div>
                            <label className="text-sm text-gray-400">Default Language</label>
                            <select className="w-full bg-navy-950 border border-navy-700 rounded-md p-2 text-white mt-1"
                                value={config.default_language}
                                onChange={e => setConfig({ ...config, default_language: e.target.value })}>
                                <option value="en">English</option>
                                <option value="ar">العربية</option>
                                <option value="fa">فارسی</option>
                                <option value="fr">Français</option>
                            </select>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="text-sm text-gray-400">Working Hours Start</label>
                                <Input type="time" value={config.working_hours_start}
                                    className="bg-navy-950 border-navy-700 mt-1"
                                    onChange={e => setConfig({ ...config, working_hours_start: e.target.value })} />
                            </div>
                            <div>
                                <label className="text-sm text-gray-400">Working Hours End</label>
                                <Input type="time" value={config.working_hours_end}
                                    className="bg-navy-950 border-navy-700 mt-1"
                                    onChange={e => setConfig({ ...config, working_hours_end: e.target.value })} />
                            </div>
                        </div>
                        <div>
                            <label className="text-sm text-gray-400">Auto Follow-up After (hours)</label>
                            <Input type="number" value={config.auto_followup_hours}
                                className="bg-navy-950 border-navy-700 mt-1"
                                onChange={e => setConfig({ ...config, auto_followup_hours: parseInt(e.target.value) })} />
                        </div>
                        <div className="flex gap-4">
                            <label className="flex items-center gap-2 cursor-pointer">
                                <input type="checkbox" checked={config.booking_enabled}
                                    className="accent-emerald-500"
                                    onChange={e => setConfig({ ...config, booking_enabled: e.target.checked })} />
                                <span className="text-sm text-gray-300">📅 Booking</span>
                            </label>
                            <label className="flex items-center gap-2 cursor-pointer">
                                <input type="checkbox" checked={config.ai_analysis_enabled}
                                    className="accent-emerald-500"
                                    onChange={e => setConfig({ ...config, ai_analysis_enabled: e.target.checked })} />
                                <span className="text-sm text-gray-300">🤖 AI Analysis</span>
                            </label>
                        </div>
                    </CardContent>
                </Card>

                {/* Active Sessions */}
                <Card className="bg-navy-900 border-navy-800 lg:col-span-2">
                    <CardHeader>
                        <CardTitle className="text-white flex items-center gap-2">
                            <Zap className="h-5 w-5 text-yellow-400" />
                            Active Bot Sessions ({sessions.length})
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        {sessions.length === 0 ? (
                            <p className="text-gray-500 text-center py-8">No active bot sessions.</p>
                        ) : (
                            <div className="overflow-x-auto">
                                <table className="w-full text-sm">
                                    <thead>
                                        <tr className="border-b border-navy-700 text-gray-400">
                                            <th className="py-2 text-left">Phone</th>
                                            <th className="py-2 text-left">Name</th>
                                            <th className="py-2 text-left">Language</th>
                                            <th className="py-2 text-left">Mode</th>
                                            <th className="py-2 text-left">State</th>
                                            <th className="py-2 text-left">Deep Link</th>
                                            <th className="py-2 text-left">Last Active</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {sessions.map((s: any) => (
                                            <tr key={s.id} className="border-b border-navy-800 text-gray-300">
                                                <td className="py-2 font-mono">{s.phone}</td>
                                                <td className="py-2">{s.name || "—"}</td>
                                                <td className="py-2">
                                                    <Badge variant="outline" className="text-xs">
                                                        {s.language?.toUpperCase()}
                                                    </Badge>
                                                </td>
                                                <td className="py-2">
                                                    <Badge className={s.mode === "buyer"
                                                        ? "bg-blue-900/60 text-blue-300"
                                                        : "bg-orange-900/60 text-orange-300"}>
                                                        {s.mode || "—"}
                                                    </Badge>
                                                </td>
                                                <td className="py-2">
                                                    <Badge variant="outline" className="text-emerald-400 border-emerald-800">
                                                        {s.state}
                                                    </Badge>
                                                </td>
                                                <td className="py-2">{s.via_deeplink ? "✅" : "❌"}</td>
                                                <td className="py-2 text-gray-500">{s.last_active ? new Date(s.last_active).toLocaleString() : "—"}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
