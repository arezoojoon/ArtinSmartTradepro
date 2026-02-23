"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Users } from "lucide-react";

export default function CompetitorsPage() {
    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold flex items-center gap-2">
                    <Users className="h-8 w-8 text-orange-400" />
                    Competitor Analysis
                </h1>
                <p className="text-gray-400 mt-1">Track competitor activity and market positioning</p>
            </div>
            <Card className="bg-[#0e1e33] border-[#1e3a5f]">
                <CardContent className="py-16 text-center">
                    <Users className="h-16 w-16 mx-auto mb-4 text-gray-700" />
                    <p className="text-gray-500">Competitor Analysis — Coming Soon</p>
                    <p className="text-xs text-gray-600 mt-2">Compare competitor density, pricing, and market share.</p>
                </CardContent>
            </Card>
        </div>
    );
}
