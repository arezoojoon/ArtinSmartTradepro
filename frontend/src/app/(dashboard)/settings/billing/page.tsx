"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { api } from "@/lib/api";
import { formatCurrency, cn } from "@/lib/utils";
import { CreditCard, History, CheckCircle2, XCircle, Loader2, Sparkles, Zap, ShieldCheck } from "lucide-react";

interface ProvisioningStatus {
    overall: "pending" | "running" | "ready" | "failed" | "partial";
    waha: "pending" | "running" | "ready" | "failed";
    crm: "pending" | "running" | "ready" | "failed";
    telegram: "pending" | "running" | "ready" | "failed";
    resources: {
        waha_session_name?: string;
        qr_ref?: string;
        telegram_deeplink?: string;
    };
    last_error?: string;
}

interface Transaction {
    id: string;
    amount: number;
    type: "credit" | "debit";
    description: string;
    status: string;
    created_at: string;
}

const PLANS = [
    {
        code: "professional",
        name: "Professional Plan",
        price: 299,
        description: "Perfect for growing lead generation and WhatsApp sales.",
        features: ["Hunter lead scraper", "WhatsApp bot (basic)", "CRM access"],
        icon: Zap,
        color: "text-blue-400"
    },
    {
        code: "enterprise",
        name: "Enterprise Plan",
        price: 999,
        description: "Full Trade Intelligence OS for global commerce scale.",
        features: ["Everything in Pro", "AI Brain (Risk/Cultural)", "Omnichannel automation", "Market pulse tools"],
        icon: Sparkles,
        color: "text-[#f5a623]",
        highlight: true
    }
];

function WalletContent() {
    const [balance, setBalance] = useState(0);
    const [transactions, setTransactions] = useState<Transaction[]>([]);
    const [loading, setLoading] = useState(true);
    const [verifying, setVerifying] = useState(false);
    const [provStatus, setProvStatus] = useState<ProvisioningStatus | null>(null);
    const searchParams = useSearchParams();
    const router = useRouter();
    const [statusMessage, setStatusMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

    const sessionId = searchParams.get("session_id");

    const fetchWalletData = async () => {
        try {
            const { data } = await api.get("/billing/wallet");
            setBalance(data.balance);
            setTransactions(data.transactions);
        } catch (error) {
            console.error("Failed to fetch wallet", error);
        } finally {
            setLoading(false);
        }
    };

    const pollProvisioningStatus = async (sId: string) => {
        setVerifying(true);
        let attempts = 0;
        const maxAttempts = 30; // 90 seconds (3s interval)

        const interval = setInterval(async () => {
            attempts++;
            try {
                const { data } = await api.get(`/billing/checkout-session?session_id=${sId}`);
                setProvStatus(data.provisioning);

                if (data.subscription_status === "active" && data.provisioning.overall === "ready") {
                    clearInterval(interval);
                    setVerifying(false);
                    setStatusMessage({ type: "success", text: "Successfully upgraded and provisioned! Your bots are ready." });
                    fetchWalletData();
                } else if (attempts >= maxAttempts) {
                    clearInterval(interval);
                    setVerifying(false);
                    setStatusMessage({ type: "success", text: "Subscription active. Provisioning is still running in background." });
                }
            } catch (error) {
                console.error("Verification error:", error);
                if (attempts >= 10) { // Give it some time to show up in DB
                    clearInterval(interval);
                    setVerifying(false);
                    setStatusMessage({ type: "error", text: "Subscription verification delayed. Please check your dashboard in a few minutes." });
                }
            }
        }, 3000);
    };

    const handleUpgrade = async (planCode: string) => {
        try {
            const { data } = await api.post("/stripe/create-checkout", {
                plan_name: planCode,
                billing_cycle: "monthly",
            });
            if (data.checkout_url) {
                window.location.href = data.checkout_url;
            } else {
                alert("Failed to create checkout session");
            }
        } catch (error) {
            console.error("Stripe checkout error:", error);
            alert("Failed to initiate payment. Please try again.");
        }
    };

    useEffect(() => {
        fetchWalletData();
        if (sessionId) {
            pollProvisioningStatus(sessionId);
            // Clean URL but keep session_id for the polling function reference
            // router.replace("/wallet", { scroll: false });
        }

        if (searchParams.get("canceled")) {
            setStatusMessage({ type: "error", text: "Payment was canceled. No charges were made." });
        }
    }, [sessionId]);

    if (verifying) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-8 p-6 text-center">
                <div className="relative">
                    <div className="h-24 w-24 rounded-full border-t-2 border-b-2 border-[#f5a623] animate-spin"></div>
                    <ShieldCheck className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-10 w-10 text-[#f5a623]" />
                </div>
                <div className="space-y-2">
                    <h2 className="text-2xl font-bold text-white">Verifying Performance & Tools...</h2>
                    <p className="text-gray-400 max-w-md">We are authorizing your payment and spinning up your AI infrastructure.</p>
                </div>

                {provStatus && (
                    <Card className="w-full max-w-md bg-[#0e1e33] border-[#1e3a5f] text-left">
                        <CardHeader className="pb-2">
                            <CardTitle className="text-sm uppercase tracking-wider text-gray-400">Initialization Progress</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="flex items-center justify-between">
                                <span className="text-sm text-gray-300">WhatsApp Engine (WAHA)</span>
                                <StatusBadge status={provStatus.waha} />
                            </div>
                            {provStatus.resources?.qr_ref && provStatus.waha !== "ready" && (
                                <div className="p-3 bg-white keep-white rounded-lg inline-block mx-auto">
                                    {/* In a real app, this would be a QR component. We show the ref/link for now. */}
                                    <p className="text-[10px] text-gray-500 mb-1">Scan to Connect:</p>
                                    <img src={provStatus.resources.qr_ref} alt="WhatsApp QR" className="h-32 w-32" />
                                </div>
                            )}
                            <div className="flex items-center justify-between">
                                <span className="text-sm text-gray-300">CRM Pipelines & Roles</span>
                                <StatusBadge status={provStatus.crm} />
                            </div>
                            <div className="flex items-center justify-between">
                                <span className="text-sm text-gray-300">Managed Telegram Bot</span>
                                <StatusBadge status={provStatus.telegram || "ready"} />
                            </div>
                            {provStatus.resources?.telegram_deeplink && (
                                <div className="mt-2">
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        className="w-full text-xs border-[#1e3a5f] hover:bg-[#1e3a5f]"
                                        onClick={() => window.open(provStatus.resources.telegram_deeplink, '_blank')}
                                    >
                                        Open Telegram Bot
                                    </Button>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                )}
            </div>
        );
    }

    return (
        <div className="space-y-8 p-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-white">Billing & Subscription</h1>
                    <p className="text-gray-400">Manage your plan and view transaction history.</p>
                </div>
                <div className="p-4 rounded-2xl bg-[#12253f] border border-[#1e3a5f] flex items-center gap-4">
                    <div className="h-10 w-10 rounded-full bg-[#f5a623]/10 flex items-center justify-center">
                        <CreditCard className="h-5 w-5 text-[#f5a623]" />
                    </div>
                    <div>
                        <p className="text-xs text-gray-400 font-medium">AVAILABLE BALANCE</p>
                        <p className="text-xl font-bold text-white leading-tight">{formatCurrency(balance)}</p>
                    </div>
                </div>
            </div>

            {statusMessage && (
                <div className={cn(
                    "flex items-center gap-3 p-4 rounded-xl border animate-in fade-in slide-in-from-top-2",
                    statusMessage.type === "success"
                        ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
                        : "bg-red-500/10 border-red-500/30 text-red-400"
                )}>
                    {statusMessage.type === "success" ? <CheckCircle2 className="h-5 w-5" /> : <XCircle className="h-5 w-5" />}
                    <span className="text-sm font-medium">{statusMessage.text}</span>
                    <button onClick={() => setStatusMessage(null)} className="ml-auto text-xs opacity-60 hover:opacity-100 p-1">Dismiss</button>
                </div>
            )}

            <div className="grid gap-6 md:grid-cols-2">
                {PLANS.map((plan) => (
                    <Card key={plan.code} className={cn(
                        "relative bg-[#0e1e33] border-[#1e3a5f] text-white flex flex-col transition-all hover:border-[#f5a623]/50 overflow-hidden",
                        plan.highlight && "ring-1 ring-[#f5a623]/30"
                    )}>
                        {plan.highlight && (
                            <div className="absolute top-0 right-0">
                                <div className="bg-[#f5a623] text-navy-900 text-[10px] font-bold px-3 py-1 rounded-bl-lg uppercase">
                                    Recommended
                                </div>
                            </div>
                        )}
                        <CardHeader>
                            <div className="flex items-center gap-3 mb-2">
                                <div className={cn("p-2 rounded-lg bg-[#12253f]", plan.color)}>
                                    <plan.icon className="h-5 w-5" />
                                </div>
                                <CardTitle>{plan.name}</CardTitle>
                            </div>
                            <CardDescription className="text-gray-400 min-h-[40px]">{plan.description}</CardDescription>
                            <div className="mt-4 flex items-baseline gap-1">
                                <span className="text-4xl font-bold text-white">${plan.price}</span>
                                <span className="text-gray-400">/month</span>
                            </div>
                        </CardHeader>
                        <CardContent className="flex-1">
                            <ul className="space-y-3">
                                {plan.features.map(feature => (
                                    <li key={feature} className="flex items-center gap-2 text-sm text-gray-300">
                                        <CheckCircle2 className="h-4 w-4 text-[#f5a623] shrink-0" />
                                        <span>{feature}</span>
                                    </li>
                                ))}
                            </ul>
                        </CardContent>
                        <CardFooter>
                            <Button
                                onClick={() => handleUpgrade(plan.code)}
                                className={cn(
                                    "w-full font-bold",
                                    plan.highlight
                                        ? "bg-[#f5a623] hover:bg-[#e0951a] text-navy-900"
                                        : "bg-navy-800 hover:bg-navy-700 text-white border border-[#1e3a5f]"
                                )}
                            >
                                {plan.highlight ? "Upgrade Now" : "Get Started"}
                            </Button>
                        </CardFooter>
                    </Card>
                ))}
            </div>

            <Card className="bg-[#0e1e33] border-[#1e3a5f] text-white">
                <CardHeader>
                    <div className="flex items-center justify-between">
                        <CardTitle className="flex items-center text-xl">
                            <History className="mr-3 h-5 w-5 text-[#f5a623]" />
                            Transaction History
                        </CardTitle>
                        <Badge variant="outline" className="border-[#1e3a5f] text-gray-400 font-normal">
                            Last 30 Days
                        </Badge>
                    </div>
                </CardHeader>
                <CardContent>
                    <ScrollArea className="h-[350px] pr-4">
                        <div className="space-y-3">
                            {transactions.length === 0 ? (
                                <div className="text-center py-16">
                                    <div className="h-12 w-12 bg-[#12253f] rounded-full flex items-center justify-center mx-auto mb-4">
                                        <History className="h-6 w-6 text-gray-600" />
                                    </div>
                                    <p className="text-gray-500 font-medium">No transactions recorded yet.</p>
                                </div>
                            ) : (
                                transactions.map((tx) => (
                                    <div key={tx.id} className="flex items-center justify-between p-4 rounded-xl bg-[#12253f]/50 border border-[#1e3a5f] hover:border-[#f5a623]/20 transition-all">
                                        <div className="flex items-center space-x-4">
                                            <div className={cn("p-2.5 rounded-xl", tx.type === 'credit' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-[#0a1628] text-gray-400')}>
                                                <History className="h-5 w-5" />
                                            </div>
                                            <div>
                                                <p className="font-semibold text-white">{tx.description}</p>
                                                <p className="text-xs text-gray-500">{new Date(tx.created_at).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })}</p>
                                            </div>
                                        </div>
                                        <div className={cn("text-lg font-bold font-mono", tx.type === 'credit' ? 'text-[#f5a623]' : 'text-white')}>
                                            {tx.type === 'credit' ? '+' : '-'}{formatCurrency(tx.amount)}
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </ScrollArea>
                </CardContent>
            </Card>
        </div>
    );
}

function StatusBadge({ status }: { status?: string }) {
    if (!status) return null;

    switch (status) {
        case "ready":
            return <Badge className="bg-emerald-500/20 text-emerald-400 border-none px-2 rounded-md">Ready</Badge>;
        case "running":
            return (
                <div className="flex items-center gap-2 text-[#f5a623]">
                    <Loader2 className="h-3 w-3 animate-spin" />
                    <span className="text-xs font-medium">Running...</span>
                </div>
            );
        case "failed":
            return <Badge className="bg-red-500/20 text-red-400 border-none px-2 rounded-md">Failed</Badge>;
        default:
            return <Badge className="bg-navy-700 text-gray-500 border-none px-2 rounded-md">Pending</Badge>;
    }
}

export default function WalletPage() {
    return (
        <Suspense fallback={<div className="flex items-center justify-center min-h-[50vh] text-white">
            <Loader2 className="h-8 w-8 animate-spin text-[#f5a623]" />
        </div>}>
            <WalletContent />
        </Suspense>
    );
}
