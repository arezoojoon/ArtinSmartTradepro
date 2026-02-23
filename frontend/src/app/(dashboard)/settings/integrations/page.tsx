"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Plug, MessageCircle, Mail, Globe, Webhook, Key } from "lucide-react";

const INTEGRATIONS = [
    {
        name: "WhatsApp (WAHA)",
        description: "Connect your WhatsApp Business for omnichannel messaging",
        icon: MessageCircle,
        status: "connected",
        category: "messaging",
    },
    {
        name: "Email (SMTP/IMAP)",
        description: "Send and receive emails directly from CRM",
        icon: Mail,
        status: "not_configured",
        category: "messaging",
    },
    {
        name: "Trade Data API Keys",
        description: "Connect your own API keys for UN Comtrade, TradeMap, etc.",
        icon: Key,
        status: "not_configured",
        category: "data",
    },
    {
        name: "Webhooks",
        description: "Send real-time events to external services (Zapier, Make)",
        icon: Webhook,
        status: "not_configured",
        category: "automation",
    },
    {
        name: "Custom Domain",
        description: "Map your domain for white-label experience",
        icon: Globe,
        status: "enterprise_only",
        category: "whitelabel",
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
                                >
                                    {int.status === "connected" ? "Manage" : "Configure"}
                                </Button>
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>
        </div>
    );
}
