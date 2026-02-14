"use client";
import React, { useEffect, useState } from "react";
import api from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { CheckCircle2, AlertTriangle, CreditCard, Receipt } from "lucide-react";
import { Badge } from "@/components/ui/badge";

interface Subscription {
    status: string;
    plan: string;
    current_period_end: string;
    cancel_at_period_end: boolean;
}

interface Invoice {
    id: string;
    amount: number;
    status: string;
    created_at: string;
}

export default function BillingSettingsPage() {
    const [sub, setSub] = useState<Subscription | null>(null);
    const [invoices, setInvoices] = useState<Invoice[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchBilling = async () => {
            try {
                const subRes = await api.get("/billing/subscription");
                setSub(subRes.data);

                const invRes = await api.get("/billing/invoices");
                setInvoices(invRes.data);
            } catch (err) {
                console.error("Failed to load billing", err);
            } finally {
                setLoading(false);
            }
        };
        fetchBilling();
    }, []);

    const handleCheckout = async (plan: string) => {
        try {
            const res = await api.post("/billing/checkout-session", { plan_name: plan });
            window.location.href = res.data.url;
        } catch (err) {
            console.error(err);
        }
    };

    if (loading) return <div className="p-8 text-white">Loading billing details...</div>;

    return (
        <div className="space-y-6">
            <h1 className="text-3xl font-bold text-white">Billing & Plans</h1>

            <div className="grid gap-6 md:grid-cols-2">
                {/* Subscription Status */}
                <Card className="bg-navy-900 border-navy-700 text-white">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <CreditCard className="h-5 w-5 text-gold-400" />
                            Current Plan
                        </CardTitle>
                        <CardDescription>Manage your subscription.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-6">
                        <div className="p-6 bg-navy-950 rounded-lg border border-navy-800 text-center">
                            <h3 className="text-2xl font-bold text-white mb-2">{sub?.plan || "Trial"}</h3>
                            <div className="flex justify-center gap-2 mb-4">
                                <Badge variant={sub?.status === 'active' ? 'default' : 'secondary'} className="uppercase">
                                    {sub?.status}
                                </Badge>
                            </div>

                            {sub?.current_period_end && (
                                <p className="text-sm text-gray-400">
                                    Renews on {new Date(sub.current_period_end).toLocaleDateString()}
                                </p>
                            )}
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <Button variant="outline" onClick={() => handleCheckout("professional")} className="w-full border-navy-600 text-gray-300 hover:text-white hover:bg-navy-800">
                                Upgrade to Pro
                            </Button>
                            <Button variant="default" onClick={() => handleCheckout("enterprise")} className="w-full bg-gold-500 text-navy-900 hover:bg-gold-600">
                                Upgrade to Enterprise
                            </Button>
                        </div>
                    </CardContent>
                </Card>

                {/* Invoices */}
                <Card className="bg-navy-900 border-navy-700 text-white">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Receipt className="h-5 w-5 text-blue-400" />
                            Use History
                        </CardTitle>
                        <CardDescription>Recent invoices and payments.</CardDescription>
                    </CardHeader>
                    <CardContent>
                        {invoices.length === 0 ? (
                            <div className="text-center py-8 text-gray-500 text-sm">
                                <p>No invoices yet.</p>
                            </div>
                        ) : (
                            <ul className="space-y-4">
                                {invoices.map((inv) => (
                                    <li key={inv.id} className="flex justify-between items-center border-b border-navy-800 pb-2">
                                        <div>
                                            <p className="font-medium text-white">${inv.amount}</p>
                                            <p className="text-xs text-gray-400">{new Date(inv.created_at).toLocaleDateString()}</p>
                                        </div>
                                        <Badge variant="outline" className="text-green-400 border-green-900 bg-green-900/20">
                                            {inv.status}
                                        </Badge>
                                    </li>
                                ))}
                            </ul>
                        )}
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
