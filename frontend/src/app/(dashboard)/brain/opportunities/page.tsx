"use client";

import { Card, CardContent } from "@/components/ui/card";
import { TrendingUp } from "lucide-react";

export default function OpportunitiesPage() {
    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold flex items-center gap-2">
                    <TrendingUp className="h-8 w-8 text-emerald-400" />
                    Arbitrage Opportunities
                </h1>
                <p className="text-gray-400 mt-1">AI-identified trade opportunities with margin analysis</p>
            </div>
            <Card className="bg-[#0e1e33] border-[#1e3a5f]">
                <CardContent className="py-16 text-center">
                    <TrendingUp className="h-16 w-16 mx-auto mb-4 text-gray-700" />
                    <p className="text-gray-500">Arbitrage Engine — Coming Soon</p>
                    <p className="text-xs text-gray-600 mt-2">Discover buy/sell opportunities across markets with confidence scores.</p>
                </CardContent>
            </Card>
        </div>
    );
}
