"use client";

import { LandedCostTab } from "@/components/brain/LandedCostTab";
import { Calculator } from "lucide-react";

export default function LandedCostPage() {
    return (
        <div className="max-w-5xl mx-auto space-y-6">
            <div>
                <h2 className="text-3xl font-bold tracking-tight text-slate-900 flex items-center gap-3">
                    <div className="bg-emerald-100 p-2 rounded-xl">
                        <Calculator className="h-6 w-6 text-emerald-600" />
                    </div>
                    Landed Cost Calculator
                </h2>
                <p className="text-muted-foreground mt-1">
                    Calculate the full cost of importing/exporting goods — freight, tariffs, insurance, warehousing, and final profit analysis.
                </p>
            </div>

            <LandedCostTab />
        </div>
    );
}
