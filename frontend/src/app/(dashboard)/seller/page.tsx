"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Users, TrendingUp, Crosshair } from "lucide-react";

import BrainFeed from "@/components/dashboard/BrainFeed";

export default function SellerDashboard() {
    return (
        <div className="space-y-6">
            <h1 className="text-3xl font-bold text-white">Seller Control Tower</h1>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Active Leads Funnel */}
                <Card className="bg-navy-900 border-navy-800">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-gray-200">
                            Active Leads
                        </CardTitle>
                        <Users className="h-4 w-4 text-gold-400" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white">124 Qualified</div>
                        <p className="text-xs text-gray-400">12 Hot (Need Action)</p>
                        <div className="h-32 mt-4 bg-navy-950 rounded border border-navy-800 flex items-center justify-center text-gray-500 text-xs">
                            [Funnel Chart Placeholder]
                        </div>
                    </CardContent>
                </Card>

                {/* Market Demand Ticker */}
                <Card className="bg-navy-900 border-navy-800">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-gray-200">
                            Market Demand
                        </CardTitle>
                        <TrendingUp className="h-4 w-4 text-green-400" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white">High (UAE)</div>
                        <p className="text-xs text-gray-400">Nutella demand +15% in Dubai</p>
                        <div className="h-32 mt-4 bg-navy-950 rounded border border-navy-800 flex items-center justify-center text-gray-500 text-xs">
                            [Demand Map Placeholder]
                        </div>
                    </CardContent>
                </Card>

                {/* Competitor Price Monitor */}
                <Card className="bg-navy-900 border-navy-800">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-gray-200">
                            Competitor Alert
                        </CardTitle>
                        <Crosshair className="h-4 w-4 text-red-400" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white">-5% Price Drop</div>
                        <p className="text-xs text-gray-400">Key competitor in Saudi Arabia</p>
                        <div className="h-32 mt-4 bg-navy-950 rounded border border-navy-800 flex items-center justify-center text-gray-500 text-xs">
                            [Price Trend Placeholder]
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Proactive Sales Intelligence */}
            <div className="mt-8">
                <BrainFeed mode="seller" />
            </div>
        </div>
    );
}
