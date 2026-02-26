"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { CreditCard, DollarSign, Clock, CheckCircle2, AlertTriangle, Loader2, Receipt, ArrowUpRight, Wallet } from "lucide-react";
import api from "@/lib/api";

interface Transaction {
    id: string;
    type: string;
    amount: number;
    description: string;
    created_at: string;
    status?: string;
}

export default function PaymentPage() {
    const [wallet, setWallet] = useState<{ balance: number; currency: string } | null>(null);
    const [transactions, setTransactions] = useState<Transaction[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const load = async () => {
            try {
                const [wRes, tRes] = await Promise.allSettled([
                    api.get("/billing/wallet"),
                    api.get("/billing/transactions"),
                ]);
                if (wRes.status === "fulfilled") setWallet(wRes.value.data);
                if (tRes.status === "fulfilled") setTransactions(Array.isArray(tRes.value.data) ? tRes.value.data : []);
            } catch {}
            finally { setLoading(false); }
        };
        load();
    }, []);

    const totalSpent = transactions.filter(t => t.type === "deduction" || t.amount < 0).reduce((s, t) => s + Math.abs(t.amount), 0);
    const totalAdded = transactions.filter(t => t.type === "topup" || t.type === "refund" || t.amount > 0).reduce((s, t) => s + Math.abs(t.amount), 0);

    return (
        <div className="space-y-6 p-4 md:p-8 max-w-[1200px] mx-auto">
            <div>
                <h1 className="text-2xl font-bold flex items-center gap-2 text-white">
                    <CreditCard className="h-6 w-6 text-[#f5a623]" /> Payments
                </h1>
                <p className="text-white/50 text-sm">Track wallet balance, transactions, and billing</p>
            </div>

            {loading ? (
                <div className="flex justify-center py-16"><Loader2 className="h-6 w-6 animate-spin text-white/40" /></div>
            ) : (
                <>
                    {/* KPI Cards */}
                    <div className="grid gap-4 sm:grid-cols-3">
                        <Card className="bg-[#0e1e33] border-[#1e3a5f]">
                            <CardContent className="p-5">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-white/50 text-xs font-medium uppercase">Wallet Balance</p>
                                        <p className="text-2xl font-bold text-white mt-1">${wallet?.balance?.toLocaleString() ?? "0"}</p>
                                    </div>
                                    <Wallet className="h-8 w-8 text-[#f5a623]/60" />
                                </div>
                            </CardContent>
                        </Card>
                        <Card className="bg-[#0e1e33] border-[#1e3a5f]">
                            <CardContent className="p-5">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-white/50 text-xs font-medium uppercase">Total Credits Added</p>
                                        <p className="text-2xl font-bold text-emerald-400 mt-1">+${totalAdded.toLocaleString()}</p>
                                    </div>
                                    <ArrowUpRight className="h-8 w-8 text-emerald-400/40" />
                                </div>
                            </CardContent>
                        </Card>
                        <Card className="bg-[#0e1e33] border-[#1e3a5f]">
                            <CardContent className="p-5">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-white/50 text-xs font-medium uppercase">Total Spent</p>
                                        <p className="text-2xl font-bold text-rose-400 mt-1">-${totalSpent.toLocaleString()}</p>
                                    </div>
                                    <Receipt className="h-8 w-8 text-rose-400/40" />
                                </div>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Transactions */}
                    <Card className="bg-[#0e1e33] border-[#1e3a5f]">
                        <CardHeader>
                            <CardTitle className="text-white text-lg flex items-center gap-2">
                                <Clock className="h-5 w-5 text-[#f5a623]" /> Transaction History
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            {transactions.length === 0 ? (
                                <p className="text-white/40 text-sm text-center py-8">No transactions yet</p>
                            ) : (
                                <div className="divide-y divide-white/5">
                                    {transactions.slice(0, 30).map(tx => (
                                        <div key={tx.id} className="flex items-center justify-between py-3">
                                            <div className="flex items-center gap-3">
                                                <div className={`p-2 rounded-lg ${tx.amount > 0 || tx.type === "topup" || tx.type === "refund" ? "bg-emerald-500/10" : "bg-rose-500/10"}`}>
                                                    {tx.amount > 0 || tx.type === "topup" || tx.type === "refund"
                                                        ? <ArrowUpRight className="h-4 w-4 text-emerald-400" />
                                                        : <Receipt className="h-4 w-4 text-rose-400" />}
                                                </div>
                                                <div>
                                                    <p className="text-white text-sm font-medium">{tx.description || tx.type}</p>
                                                    <p className="text-white/30 text-xs">{new Date(tx.created_at).toLocaleDateString()} {new Date(tx.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</p>
                                                </div>
                                            </div>
                                            <span className={`font-mono font-bold text-sm ${tx.amount > 0 || tx.type === "topup" || tx.type === "refund" ? "text-emerald-400" : "text-rose-400"}`}>
                                                {tx.amount > 0 ? "+" : ""}{tx.amount < 0 ? "-" : ""}${Math.abs(tx.amount).toLocaleString()}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </>
            )}
        </div>
    );
}
