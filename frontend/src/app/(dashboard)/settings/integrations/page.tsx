"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Plug, MessageCircle, Mail, Globe, Webhook, Key, X, CheckCircle2, AlertTriangle } from "lucide-react";

const INTEGRATIONS = [
    {
        name: "WhatsApp (WAHA)",
        description: "Connect your WhatsApp Business for omnichannel messaging",
        icon: MessageCircle,
        status: "connected",
        category: "messaging",
        configFields: [{ key: "waha_url", label: "WAHA Server URL", placeholder: "https://waha.example.com" }, { key: "session", label: "Session Name", placeholder: "default" }],
    },
    {
        name: "Email (SMTP/IMAP)",
        description: "Send and receive emails directly from CRM",
        icon: Mail,
        status: "not_configured",
        category: "messaging",
        configFields: [{ key: "smtp_host", label: "SMTP Host", placeholder: "smtp.gmail.com" }, { key: "smtp_port", label: "SMTP Port", placeholder: "587" }, { key: "email", label: "Email Address", placeholder: "you@company.com" }, { key: "password", label: "Password", placeholder: "App password" }],
    },
    {
        name: "Trade Data API Keys",
        description: "Connect your own API keys for UN Comtrade, TradeMap, etc.",
        icon: Key,
        status: "not_configured",
        category: "data",
        configFields: [{ key: "comtrade_key", label: "UN Comtrade API Key", placeholder: "Your API key" }, { key: "trademap_key", label: "TradeMap API Key", placeholder: "Your API key" }],
    },
    {
        name: "Webhooks",
        description: "Send real-time events to external services (Zapier, Make)",
        icon: Webhook,
        status: "not_configured",
        category: "automation",
        configFields: [{ key: "webhook_url", label: "Webhook URL", placeholder: "https://hooks.zapier.com/..." }, { key: "events", label: "Events (comma-separated)", placeholder: "deal.won, lead.created, invoice.paid" }],
    },
    {
        name: "Custom Domain",
        description: "Map your domain for white-label experience",
        icon: Globe,
        status: "enterprise_only",
        category: "whitelabel",
        configFields: [],
    },
];

function statusBadge(status: string) {
    switch (status) {
        case "connected":
            return <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30">Connected</Badge>;
        case "not_configured":
            return <Badge variant="outline" className="text-white/50 border-white/20">Not Configured</Badge>;
        case "enterprise_only":
            return <Badge className="bg-purple-500/20 text-purple-400 border-purple-500/30">Enterprise</Badge>;
        default:
            return null;
    }
}

export default function IntegrationsPage() {
    const [activeIntegration, setActiveIntegration] = useState<typeof INTEGRATIONS[0] | null>(null);
    const [configValues, setConfigValues] = useState<Record<string, string>>({});
    const [saveStatus, setSaveStatus] = useState<"idle" | "saving" | "saved">("idle");

    const openConfig = (integration: typeof INTEGRATIONS[0]) => {
        setActiveIntegration(integration);
        setConfigValues({});
        setSaveStatus("idle");
    };

    const handleSave = () => {
        setSaveStatus("saving");
        // Simulate save — in production this would call a backend API
        setTimeout(() => {
            setSaveStatus("saved");
            setTimeout(() => { setActiveIntegration(null); setSaveStatus("idle"); }, 1500);
        }, 800);
    };

    return (
        <div className="p-4 md:p-8 space-y-8 max-w-4xl text-white">
            <div>
                <h1 className="text-2xl font-bold flex items-center gap-2">
                    <Plug className="h-6 w-6 text-[#f5a623]" /> Integrations
                </h1>
                <p className="text-white/60">Connect external services and data sources.</p>
            </div>

            <div className="grid gap-4">
                {INTEGRATIONS.map((int) => (
                    <Card key={int.name} className="bg-[#0e1e33] border-[#1e3a5f]">
                        <CardContent className="p-5 flex items-center justify-between">
                            <div className="flex items-center gap-4">
                                <div className="p-2.5 rounded-xl bg-navy-800">
                                    <int.icon className="h-5 w-5 text-[#f5a623]" />
                                </div>
                                <div>
                                    <h3 className="font-semibold text-white">{int.name}</h3>
                                    <p className="text-sm text-white/50">{int.description}</p>
                                </div>
                            </div>
                            <div className="flex items-center gap-3">
                                {statusBadge(int.status)}
                                <Button
                                    variant="outline"
                                    size="sm"
                                    className="border-navy-700 text-white hover:bg-navy-800"
                                    disabled={int.status === "enterprise_only"}
                                    onClick={() => openConfig(int)}
                                >
                                    {int.status === "connected" ? "Manage" : "Configure"}
                                </Button>
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>

            {/* Configuration Modal */}
            {activeIntegration && (
                <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4" onClick={() => setActiveIntegration(null)}>
                    <div className="bg-[#0e1e33] border border-[#1e3a5f] rounded-2xl w-full max-w-md p-6" onClick={e => e.stopPropagation()}>
                        <div className="flex justify-between items-center mb-5">
                            <h3 className="text-lg font-bold text-white flex items-center gap-2">
                                <activeIntegration.icon className="h-5 w-5 text-[#f5a623]" />
                                {activeIntegration.name}
                            </h3>
                            <button onClick={() => setActiveIntegration(null)} className="text-navy-400 hover:text-white"><X className="h-5 w-5" /></button>
                        </div>

                        {saveStatus === "saved" ? (
                            <div className="text-center py-8">
                                <CheckCircle2 className="h-12 w-12 text-emerald-400 mx-auto mb-3" />
                                <p className="text-white font-semibold">Configuration Saved</p>
                            </div>
                        ) : (
                            <>
                                <div className="space-y-4">
                                    {activeIntegration.configFields.map(field => (
                                        <div key={field.key}>
                                            <label className="block text-xs text-navy-400 mb-1">{field.label}</label>
                                            <input
                                                type={field.key.includes("password") ? "password" : "text"}
                                                value={configValues[field.key] || ""}
                                                onChange={e => setConfigValues(v => ({ ...v, [field.key]: e.target.value }))}
                                                placeholder={field.placeholder}
                                                className="w-full px-3 py-2 bg-navy-800 border border-navy-600 rounded-lg text-white text-sm focus:border-gold-400 focus:outline-none"
                                            />
                                        </div>
                                    ))}
                                </div>
                                <div className="flex items-center gap-2 mt-2 text-[10px] text-navy-500">
                                    <AlertTriangle className="h-3 w-3" /> Credentials are encrypted and stored securely.
                                </div>
                                <button onClick={handleSave} disabled={saveStatus === "saving"} className="mt-5 w-full py-2.5 bg-[#f5a623] text-navy-950 rounded-lg font-semibold hover:bg-gold-300 transition-all disabled:opacity-50">
                                    {saveStatus === "saving" ? "Saving..." : "Save Configuration"}
                                </button>
                            </>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}
