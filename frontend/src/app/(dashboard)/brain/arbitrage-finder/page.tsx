"use client";

import { RegionalArbitrageTab } from "@/components/brain/RegionalArbitrageTab";
import { Radar } from "lucide-react";

export default function ArbitrageFinderPage() {
    return (
        <div className="max-w-5xl mx-auto space-y-6">
            <div>
                <h2 className="text-3xl font-bold tracking-tight text-slate-900 flex items-center gap-3">
                    <div className="bg-violet-100 p-2 rounded-xl">
                        <Radar className="h-6 w-6 text-violet-600" />
                    </div>
                    Regional Arbitrage Finder
                </h2>
                <p className="text-muted-foreground mt-1">
                    AI-powered scanner to detect price gaps across neighboring markets and find profitable trade opportunities.
                </p>
            </div>

            <RegionalArbitrageTab />
        </div>
    );
}
