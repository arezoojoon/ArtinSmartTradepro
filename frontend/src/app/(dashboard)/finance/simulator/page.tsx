"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Calculator } from "lucide-react";

export default function FinanceSimulatorPage() {
    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold flex items-center gap-2">
                    <Calculator className="h-8 w-8 text-blue-400" />
                    Finance Simulator
                </h1>
                <p className="text-gray-400 mt-1">Simulate trade scenarios and margin projections</p>
            </div>
            <Card className="bg-[#0e1e33] border-[#1e3a5f]">
                <CardContent className="py-16 text-center">
                    <Calculator className="h-16 w-16 mx-auto mb-4 text-gray-700" />
                    <p className="text-gray-500">Finance Simulator — Coming Soon</p>
                    <p className="text-xs text-gray-600 mt-2">Cash flow forecasting, DSO trends, and margin analysis.</p>
                </CardContent>
            </Card>
        </div>
    );
}
