"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Globe, ShieldAlert, Calculator, Loader2, Building2, Users } from "lucide-react";
import api from "@/lib/api";
import BrainFeed from "@/components/dashboard/BrainFeed";

export default function BuyerDashboard() {
    const [data, setData] = useState<any>(null);
    const [companies, setCompanies] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [dashRes, compRes] = await Promise.all([
                    api.get("/dashboard/main"),
                    api.get("/crm/companies?skip=0&limit=100")
                ]);
                setData(dashRes.data);
                setCompanies(compRes.data?.items || compRes.data || []);
            } catch (e) {
                console.error("Buyer dashboard fetch failed:", e);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    const suppliers = data?.supplier_reliability || [];
    const avgReliability = data?.kpi_summary?.avg_reliability_score || 0;
    const riskLevel = avgReliability >= 80 ? "Low Risk" : avgReliability >= 50 ? "Medium Risk" : avgReliability > 0 ? "High Risk" : "No Data";
    const riskColor = avgReliability >= 80 ? "text-green-400" : avgReliability >= 50 ? "text-amber-400" : "text-red-400";

    // Count unique countries from companies
    const countries = [...new Set(companies.map((c: any) => c.country).filter(Boolean))];

    if (loading) return (
        <div className="flex items-center justify-center p-12 text-slate-400">
            <Loader2 className="h-6 w-6 animate-spin mr-2" /> Loading Buyer Dashboard...
        </div>
    );

    return (
        <div className="space-y-6">
            <h1 className="text-3xl font-bold text-white">Buyer Control Tower</h1>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <Card className="bg-[#0e1e33] border-[#1e3a5f]">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-gray-200">
                            CRM Companies
                        </CardTitle>
                        <Building2 className="h-4 w-4 text-[#f5a623]" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white">{companies.length} Companies</div>
                        <p className="text-xs text-gray-400">
                            {countries.length > 0 ? `Across ${countries.length} countries: ${countries.slice(0, 3).join(", ")}` : "No companies yet"}
                        </p>
                    </CardContent>
                </Card>

                <Card className="bg-[#0e1e33] border-[#1e3a5f]">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-gray-200">
                            Supplier Reliability
                        </CardTitle>
                        <ShieldAlert className="h-4 w-4 text-red-400" />
                    </CardHeader>
                    <CardContent>
                        <div className={`text-2xl font-bold text-white`}>{riskLevel}</div>
                        <p className={`text-xs ${riskColor}`}>
                            {avgReliability > 0 ? `Avg score: ${avgReliability}/100` : "Run Brain Risk Engine to assess"}
                        </p>
                        {suppliers.length > 0 && (
                            <div className="mt-3 space-y-1">
                                {suppliers.slice(0, 3).map((s: any, i: number) => (
                                    <div key={i} className="flex justify-between text-xs">
                                        <span className="text-gray-400">{s.supplier_name}</span>
                                        <span className={s.reliability_score >= 80 ? "text-green-400" : "text-amber-400"}>{s.reliability_score}%</span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </CardContent>
                </Card>

                <Card className="bg-[#0e1e33] border-[#1e3a5f]">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-gray-200">
                            Pipeline Value
                        </CardTitle>
                        <Calculator className="h-4 w-4 text-blue-400" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white">
                            ${((data?.kpi_summary?.total_pipeline_value || 0) / 1000).toFixed(0)}K
                        </div>
                        <p className="text-xs text-gray-400">From CRM Deals</p>
                        {(data?.pipeline_summary || []).length > 0 && (
                            <div className="mt-3 space-y-1">
                                {(data?.pipeline_summary || []).slice(0, 3).map((s: any, i: number) => (
                                    <div key={i} className="flex justify-between text-xs">
                                        <span className="text-gray-400">{s.name}</span>
                                        <span className="text-white">{s.count} deals</span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>

            <div className="mt-8">
                <BrainFeed mode="buyer" />
            </div>
        </div>
    );
}
