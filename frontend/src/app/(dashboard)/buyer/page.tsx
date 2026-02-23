"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Globe, ShieldAlert, Calculator } from "lucide-react";

import BrainFeed from "@/components/dashboard/BrainFeed";

export default function BuyerDashboard() {
    return (
        <div className="space-y-6">
            <h1 className="text-3xl font-bold text-white">Buyer Control Tower</h1>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Global Sourcing Map Widget */}
                <Card className="bg-[#0e1e33] border-[#1e3a5f]">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-gray-200">
                            Global Sourcing Map
                        </CardTitle>
                        <Globe className="h-4 w-4 text-[#f5a623]" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white">3 Active Regions</div>
                        <p className="text-xs text-gray-400">Top: China, Turkey, Brazil</p>
                        <div className="h-32 mt-4 bg-navy-950 rounded border border-[#1e3a5f] flex items-center justify-center text-gray-500 text-xs">
                            [Interactive Map Placeholder]
                        </div>
                    </CardContent>
                </Card>

                {/* Supplier Risk Heatmap Widget */}
                <Card className="bg-[#0e1e33] border-[#1e3a5f]">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-gray-200">
                            Supplier Risk
                        </CardTitle>
                        <ShieldAlert className="h-4 w-4 text-red-400" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white">Low Risk</div>
                        <p className="text-xs text-green-400">All suppliers verified</p>
                        <div className="h-32 mt-4 bg-navy-950 rounded border border-[#1e3a5f] flex items-center justify-center text-gray-500 text-xs">
                            [Risk Matrix Placeholder]
                        </div>
                    </CardContent>
                </Card>

                {/* Landed Cost Widget */}
                <Card className="bg-[#0e1e33] border-[#1e3a5f]">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-gray-200">
                            Avg Landed Cost
                        </CardTitle>
                        <Calculator className="h-4 w-4 text-blue-400" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white">$4.20 / unit</div>
                        <p className="text-xs text-gray-400">+2% vs last month (Freight)</p>
                        <div className="h-32 mt-4 bg-navy-950 rounded border border-[#1e3a5f] flex items-center justify-center text-gray-500 text-xs">
                            [Cost Breakdown Chart]
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Proactive Opportunities Stream */}
            <div className="mt-8">
                <BrainFeed mode="buyer" />
            </div>
        </div>
    );
}
