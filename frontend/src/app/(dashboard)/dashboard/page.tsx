"use client";

import { useEffect, useState } from "react";
import MoneyCard from "@/components/dashboard/MoneyCard";
import RecentLeads from "@/components/dashboard/RecentLeads";
import QuickActions from "@/components/dashboard/QuickActions";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { Skeleton } from "@/components/ui/skeleton";
import Link from "next/link";
import { Send, Search, Wallet, DollarSign, TrendingUp } from "lucide-react";

export default function DashboardPage() {
    const [stats, setStats] = useState({
        potentialRevenue: 0,
        hotLeads: 0,
        walletBalance: 0,
        totalLeads: 0
    });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchStats = async () => {
            try {
                // In a real app, these would be separate atomic calls or a specialized dashboard endpoint
                const [walletRes, leadsRes] = await Promise.all([
                    api.get("/billing/wallet"),
                    api.get("/leads/stats")
                ]);

                setStats({
                    potentialRevenue: leadsRes.data.potential_revenue || 0,
                    hotLeads: leadsRes.data.hot_leads || 0,
                    walletBalance: walletRes.data.balance || 0,
                    totalLeads: leadsRes.data.total_leads || 0
                });
            } catch (error) {
                console.error("Failed to fetch dashboard stats", error);
                // Fallback for demo if API fails
                setStats({ potentialRevenue: 0, hotLeads: 0, walletBalance: 0, totalLeads: 0 });
            } finally {
                setLoading(false);
            }
        };

        fetchStats();
    }, []);

    if (loading) {
        return <div className="p-8 space-y-4">
            <Skeleton className="h-12 w-1/3" />
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Skeleton className="h-32" /><Skeleton className="h-32" /><Skeleton className="h-32" /><Skeleton className="h-32" />
            </div>
        </div>;
    }

    return (
        <div className="flex-1 space-y-4 p-8 pt-6">
            <div className="flex items-center justify-between space-y-2">
                <h2 className="text-3xl font-bold tracking-tight text-white">Dashboard</h2>
                <div className="flex items-center space-x-2">
                    <Button asChild className="bg-gold-500 text-navy-900 font-bold hover:bg-gold-600">
                        <Link href="/wallet">
                            <Wallet className="mr-2 h-4 w-4" /> Top Up Wallet
                        </Link>
                    </Button>
                </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                <MoneyCard value={stats.potentialRevenue} title="Potential Revenue" icon={DollarSign} trend="+20.1% from last month" />
                <MoneyCard value={stats.hotLeads} title="Hot Leads to Close" icon={TrendingUp} trend="+12 since yesterday" isCount />
                <MoneyCard value={stats.walletBalance} title="Wallet Balance" icon={Wallet} trend="Credits available" isCurrency />
            </div>

            {/* Empty State / Call to Action - MVP Vital */}
            {stats.totalLeads === 0 ? (
                <div className="rounded-lg border-2 border-dashed border-navy-700 p-12 text-center bg-navy-900/50">
                    <h3 className="mt-2 text-xl font-bold text-white">Your Pipeline is Empty</h3>
                    <p className="mt-1 text-sm text-gray-400">Start by finding leads or importing your existing list.</p>
                    <div className="mt-6 flex justify-center gap-4">
                        <Button asChild size="lg" className="bg-blue-600 hover:bg-blue-700">
                            <Link href="/hunter">
                                <Search className="mr-2 h-4 w-4" /> Launch Lead Hunter
                            </Link>
                        </Button>
                        <Button asChild variant="outline" size="lg" className="border-navy-600 hover:bg-navy-800 text-white">
                            <Link href="/leads/import">
                                Import CSV
                            </Link>
                        </Button>
                    </div>
                </div>
            ) : (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
                    <RecentLeads className="col-span-4" />
                    <QuickActions className="col-span-3" />
                </div>
            )}
        </div>
    );
}
