"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Users, TrendingUp, Scale, Loader2 } from "lucide-react";
import api from "@/lib/api";
import BrainFeed from "@/components/dashboard/BrainFeed";

export default function SellerDashboard() {
    const [data, setData] = useState<any>(null);
    const [contacts, setContacts] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [dashRes, contactRes] = await Promise.all([
                    api.get("/dashboard/main"),
                    api.get("/crm/contacts?skip=0&limit=5")
                ]);
                setData(dashRes.data);
                setContacts(contactRes.data?.items || contactRes.data || []);
            } catch (e) {
                console.error("Seller dashboard fetch failed:", e);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    const kpi = data?.kpi_summary || {};
    const margins = data?.margin_overview || [];
    const pipeline = data?.pipeline_summary || [];

    if (loading) return (
        <div className="flex items-center justify-center p-12 text-slate-400">
            <Loader2 className="h-6 w-6 animate-spin mr-2" /> Loading Seller Dashboard...
        </div>
    );

    return (
        <div className="space-y-6">
            <h1 className="text-3xl font-bold text-white">Seller Control Tower</h1>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <Card className="bg-[#0e1e33] border-[#1e3a5f]">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-gray-200">
                            Active Leads
                        </CardTitle>
                        <Users className="h-4 w-4 text-[#f5a623]" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white">{kpi.active_leads ?? 0} Qualified</div>
                        <p className="text-xs text-gray-400">From Hunter lead generation</p>
                        {contacts.length > 0 && (
                            <div className="mt-3 space-y-1">
                                {contacts.slice(0, 3).map((c: any, i: number) => (
                                    <div key={i} className="flex justify-between text-xs">
                                        <span className="text-gray-400">{c.first_name} {c.last_name || ""}</span>
                                        <span className="text-white">{c.email || c.phone || ""}</span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </CardContent>
                </Card>

                <Card className="bg-[#0e1e33] border-[#1e3a5f]">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-gray-200">
                            Pipeline Stages
                        </CardTitle>
                        <TrendingUp className="h-4 w-4 text-green-400" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white">
                            {pipeline.reduce((s: number, p: any) => s + p.count, 0)} Deals
                        </div>
                        <p className="text-xs text-gray-400">Across {pipeline.length} stages</p>
                        {pipeline.length > 0 && (
                            <div className="mt-3 space-y-1">
                                {pipeline.map((s: any, i: number) => (
                                    <div key={i} className="flex justify-between text-xs">
                                        <span className="text-gray-400">{s.name}</span>
                                        <span className="text-white">{s.count} ({s.percentage?.toFixed(0)}%)</span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </CardContent>
                </Card>

                <Card className="bg-[#0e1e33] border-[#1e3a5f]">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-gray-200">
                            Margin Overview
                        </CardTitle>
                        <Scale className="h-4 w-4 text-[#D4AF37]" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white">
                            {kpi.weighted_margin ? `${kpi.weighted_margin.toFixed(1)}%` : "N/A"}
                        </div>
                        <p className="text-xs text-gray-400">Average estimated margin</p>
                        {margins.length > 0 && (
                            <div className="mt-3 space-y-1">
                                {margins.slice(0, 3).map((m: any, i: number) => (
                                    <div key={i} className="flex justify-between text-xs">
                                        <span className="text-gray-400">{m.product_key}</span>
                                        <span className="text-[#D4AF37]">{m.estimated_margin_pct?.toFixed(1)}%</span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>

            <div className="mt-8">
                <BrainFeed mode="seller" />
            </div>
        </div>
    );
}
