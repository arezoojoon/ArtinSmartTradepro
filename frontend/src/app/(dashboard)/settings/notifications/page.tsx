"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Bell, MessageCircle, Mail, AlertTriangle, TrendingUp, Users } from "lucide-react";

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
    return (
        <div className="p-4 md:p-8 space-y-8 max-w-4xl text-white">
            <div>
                <h1 className="text-2xl font-bold flex items-center gap-2">
                    <Bell className="h-6 w-6 text-[#f5a623]" /> Notification Settings
                </h1>
                <p className="text-white/60">Configure how and when you receive alerts.</p>
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
                                <input type="checkbox" defaultChecked={ch.enabled} className="sr-only peer" />
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
                                <input type="checkbox" defaultChecked={rule.enabled} className="sr-only peer" />
                                <div className="w-11 h-6 bg-navy-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-gold-500"></div>
                            </label>
                        </div>
                    ))}
                </CardContent>
            </Card>
        </div>
    );
}
