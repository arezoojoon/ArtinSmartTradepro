"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Bell, MessageCircle, Mail, AlertTriangle, TrendingUp, Users, CheckCircle2, Loader2 } from "lucide-react";
import api from "@/lib/api";

const NOTIFICATION_CHANNELS = [
    { id: "push", label: "Push Notifications (PWA)", icon: Bell, enabled: true },
    { id: "whatsapp", label: "WhatsApp Alerts", icon: MessageCircle, enabled: false },
    { id: "email", label: "Email Digest", icon: Mail, enabled: true },
];

const ALERT_RULES = [
    { id: "risk_high", label: "High-Severity Risk Alerts", severity: "high", enabled: true },
    { id: "risk_medium", label: "Medium-Severity Risk Alerts", severity: "medium", enabled: true },
    { id: "risk_low", label: "Low-Severity Risk Alerts", severity: "low", enabled: false },
    { id: "lead_new", label: "New Lead Notifications", severity: "info", enabled: true },
    { id: "deal_stage", label: "Deal Stage Changes", severity: "info", enabled: true },
    { id: "invoice_overdue", label: "Overdue Invoice Alerts", severity: "high", enabled: true },
    { id: "market_shock", label: "Market Shock Signals", severity: "medium", enabled: true },
];

const STORAGE_KEY = "artin_notification_settings";

function loadSettings(): Record<string, boolean> {
    if (typeof window === "undefined") return {};
    try {
        const raw = localStorage.getItem(STORAGE_KEY);
        if (raw) return JSON.parse(raw);
    } catch {}
    // Defaults
    const defaults: Record<string, boolean> = {};
    NOTIFICATION_CHANNELS.forEach(c => { defaults[c.id] = c.enabled; });
    ALERT_RULES.forEach(r => { defaults[r.id] = r.enabled; });
    return defaults;
}

function severityBadge(severity: string) {
    switch (severity) {
        case "high":
            return <Badge className="bg-rose-500/20 text-rose-400 border-rose-500/30 text-xs">High</Badge>;
        case "medium":
            return <Badge className="bg-amber-500/20 text-amber-400 border-amber-500/30 text-xs">Medium</Badge>;
        case "low":
            return <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/30 text-xs">Low</Badge>;
        default:
            return <Badge variant="outline" className="text-white/50 border-white/20 text-xs">Info</Badge>;
    }
}

export default function NotificationsPage() {
    const [settings, setSettings] = useState<Record<string, boolean>>({});
    const [dirty, setDirty] = useState(false);
    const [saved, setSaved] = useState(false);
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        const load = async () => {
            try {
                const res = await api.get("/settings/notifications");
                if (res.data?.settings && Object.keys(res.data.settings).length > 0) {
                    setSettings(res.data.settings);
                    return;
                }
            } catch {}
            setSettings(loadSettings());
        };
        load();
    }, []);

    const toggle = (id: string) => {
        setSettings(prev => ({ ...prev, [id]: !prev[id] }));
        setDirty(true);
        setSaved(false);
    };

    const saveSettings = async () => {
        setSaving(true);
        try {
            await api.put("/settings/notifications", { settings });
            localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
            setDirty(false);
            setSaved(true);
            setTimeout(() => setSaved(false), 2000);
        } catch (e) {
            console.error("Failed to save notification settings", e);
            localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
            setDirty(false);
            setSaved(true);
            setTimeout(() => setSaved(false), 2000);
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="p-4 md:p-8 space-y-8 max-w-4xl text-white">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold flex items-center gap-2">
                        <Bell className="h-6 w-6 text-[#f5a623]" /> Notification Settings
                    </h1>
                    <p className="text-white/60">Configure how and when you receive alerts.</p>
                </div>
                <div className="flex items-center gap-3">
                    {saved && <span className="text-emerald-400 text-sm flex items-center gap-1"><CheckCircle2 className="h-4 w-4" /> Saved</span>}
                    <button onClick={saveSettings} disabled={!dirty || saving} className="px-5 py-2 bg-[#f5a623] text-navy-950 rounded-lg font-semibold hover:bg-gold-300 transition-all disabled:opacity-40 text-sm flex items-center gap-2">
                        {saving ? <><Loader2 className="h-4 w-4 animate-spin" /> Saving...</> : "Save Changes"}
                    </button>
                </div>
            </div>

            {/* Channels */}
            <Card className="bg-[#0e1e33] border-[#1e3a5f]">
                <CardHeader>
                    <CardTitle className="text-white">Notification Channels</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                    {NOTIFICATION_CHANNELS.map((ch) => (
                        <div key={ch.id} className="flex items-center justify-between p-3 bg-navy-950 rounded-lg border border-[#1e3a5f]">
                            <div className="flex items-center gap-3">
                                <ch.icon className="h-5 w-5 text-[#f5a623]" />
                                <span className="font-medium text-white">{ch.label}</span>
                            </div>
                            <label className="relative inline-flex items-center cursor-pointer">
                                <input type="checkbox" checked={settings[ch.id] ?? ch.enabled} onChange={() => toggle(ch.id)} className="sr-only peer" />
                                <div className="w-11 h-6 bg-navy-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-gold-500"></div>
                            </label>
                        </div>
                    ))}
                </CardContent>
            </Card>

            {/* Alert Rules */}
            <Card className="bg-[#0e1e33] border-[#1e3a5f]">
                <CardHeader>
                    <CardTitle className="text-white flex items-center gap-2">
                        <AlertTriangle className="h-5 w-5 text-[#f5a623]" /> Alert Rules
                    </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                    {ALERT_RULES.map((rule) => (
                        <div key={rule.id} className="flex items-center justify-between p-3 bg-navy-950 rounded-lg border border-[#1e3a5f]">
                            <div className="flex items-center gap-3">
                                <span className="font-medium text-white text-sm">{rule.label}</span>
                                {severityBadge(rule.severity)}
                            </div>
                            <label className="relative inline-flex items-center cursor-pointer">
                                <input type="checkbox" checked={settings[rule.id] ?? rule.enabled} onChange={() => toggle(rule.id)} className="sr-only peer" />
                                <div className="w-11 h-6 bg-navy-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-gold-500"></div>
                            </label>
                        </div>
                    ))}
                </CardContent>
            </Card>
        </div>
    );
}
