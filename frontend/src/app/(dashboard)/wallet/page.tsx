"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import { CreditCard, ArrowUpRight, ArrowDownLeft, History, CheckCircle2, XCircle } from "lucide-react";

interface Transaction {
    id: string;
    amount: number;
    type: "credit" | "debit";
    description: string;
    status: string;
    created_at: string;
}

export default function WalletPage() {
    const [balance, setBalance] = useState(0);
    const [transactions, setTransactions] = useState<Transaction[]>([]);
    const [loading, setLoading] = useState(true);
    const [amount, setAmount] = useState("");
    const searchParams = useSearchParams();
    const [statusMessage, setStatusMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

    const fetchWallet = async () => {
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

    const handleTopUp = async () => {
        const numAmount = parseFloat(amount);
        if (!numAmount || numAmount < 5) {
            alert("Minimum top-up amount is 5 AED");
            return;
        }
        try {
            const { data } = await api.post("/stripe/create-checkout", {
                amount: numAmount,
                currency: "aed",
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
        fetchWallet();

        // Handle Stripe return
        const success = searchParams.get("success");
        const canceled = searchParams.get("canceled");
        if (success === "true") {
            setStatusMessage({ type: "success", text: "Payment successful! Your balance will be updated shortly." });
            // Refresh after a short delay to allow webhook processing
            setTimeout(() => fetchWallet(), 3000);
            // Clean URL
            window.history.replaceState({}, "", "/wallet");
        } else if (canceled === "true") {
            setStatusMessage({ type: "error", text: "Payment was canceled. No charges were made." });
            window.history.replaceState({}, "", "/wallet");
        }
    }, []);

    return (
        <div className="space-y-6 p-6">
            <h1 className="text-3xl font-bold tracking-tight text-white">Wallet & Billing</h1>

            {/* Stripe payment return banner */}
            {statusMessage && (
                <div className={`flex items-center gap-3 p-4 rounded-lg border ${statusMessage.type === "success"
                        ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
                        : "bg-red-500/10 border-red-500/30 text-red-400"
                    }`}>
                    {statusMessage.type === "success" ? <CheckCircle2 className="h-5 w-5" /> : <XCircle className="h-5 w-5" />}
                    <span className="text-sm font-medium">{statusMessage.text}</span>
                    <button onClick={() => setStatusMessage(null)} className="ml-auto text-xs opacity-60 hover:opacity-100">Dismiss</button>
                </div>
            )}

            <div className="grid gap-6 md:grid-cols-2">
                {/* Balance Card */}
                <Card className="bg-navy-800 border-navy-700 text-white">
                    <CardHeader>
                        <CardTitle>Current Balance</CardTitle>
                        <CardDescription className="text-gray-400">Available credits for trading actions</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="text-4xl font-bold text-gold-400 mb-4">
                            {formatCurrency(balance)}
                        </div>
                        <div className="flex space-x-4">
                            <div className="flex-1">
                                <Label htmlFor="amount">Top Up Amount (AED)</Label>
                                <Input
                                    id="amount"
                                    type="number"
                                    placeholder="Enter amount"
                                    value={amount}
                                    onChange={(e) => setAmount(e.target.value)}
                                    className="bg-navy-900 border-navy-600 text-white mt-2"
                                />
                            </div>
                            <Button
                                onClick={handleTopUp}
                                className="mt-8 bg-gold-500 hover:bg-gold-600 text-navy-900 font-bold"
                            >
                                <CreditCard className="mr-2 h-4 w-4" />
                                Add Funds
                            </Button>
                        </div>
                    </CardContent>
                </Card>

                {/* Quick Stats or Promo */}
                <Card className="bg-navy-800 border-navy-700 text-white flex flex-col justify-center items-center p-6 bg-gradient-to-br from-navy-800 to-navy-900">
                    <div className="text-center space-y-2">
                        <h3 className="text-xl font-bold text-gold-400">Pro Tip</h3>
                        <p className="text-gray-300">
                            Each lead scrape costs <strong>1 Credit</strong>.<br />
                            Each WhatsApp message costs <strong>0.5 Credits</strong>.
                        </p>
                        <Badge variant="outline" className="mt-4 border-gold-500 text-gold-400">
                            Enterprise Plan: 20% Discount
                        </Badge>
                    </div>
                </Card>
            </div>

            {/* Transactions History */}
            <Card className="bg-navy-900 border-navy-800 text-white">
                <CardHeader>
                    <div className="flex items-center justify-between">
                        <CardTitle className="flex items-center">
                            <History className="mr-2 h-5 w-5 text-gold-500" />
                            Transaction History
                        </CardTitle>
                        <Badge variant="secondary" className="bg-navy-700 text-gray-300">
                            Last 30 Days
                        </Badge>
                    </div>
                </CardHeader>
                <CardContent>
                    <ScrollArea className="h-[400px]">
                        <div className="space-y-4">
                            {transactions.length === 0 ? (
                                <div className="text-center py-10 text-gray-500">
                                    No transactions found.
                                </div>
                            ) : (
                                transactions.map((tx) => (
                                    <div key={tx.id} className="flex items-center justify-between p-4 rounded-lg bg-navy-800 border border-navy-700 hover:border-gold-500/30 transition-colors">
                                        <div className="flex items-center space-x-4">
                                            <div className={`p-2 rounded-full ${tx.type === 'credit' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                                                {tx.type === 'credit' ? <ArrowDownLeft className="h-5 w-5" /> : <ArrowUpRight className="h-5 w-5" />}
                                            </div>
                                            <div>
                                                <p className="font-medium text-white">{tx.description}</p>
                                                <p className="text-sm text-gray-400">{new Date(tx.created_at).toLocaleDateString()}</p>
                                            </div>
                                        </div>
                                        <div className={`font-bold ${tx.type === 'credit' ? 'text-green-400' : 'text-white'}`}>
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
