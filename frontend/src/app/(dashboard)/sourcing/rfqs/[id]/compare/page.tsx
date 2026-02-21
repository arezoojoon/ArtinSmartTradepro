"use client";

import { Card, CardContent } from "@/components/ui/card";
import { BarChart3 } from "lucide-react";

export default function CompareRFQPage() {
    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold flex items-center gap-2">
                    <BarChart3 className="h-8 w-8 text-violet-400" />
                    Compare Quotes
                </h1>
                <p className="text-gray-400 mt-1">Side-by-side comparison of supplier quotes</p>
            </div>
            <Card className="bg-navy-900 border-navy-800">
                <CardContent className="py-16 text-center">
                    <BarChart3 className="h-16 w-16 mx-auto mb-4 text-gray-700" />
                    <p className="text-gray-500">Quote Comparison — Coming Soon</p>
                    <p className="text-xs text-gray-600 mt-2">Compare pricing, terms, and delivery timelines across suppliers.</p>
                </CardContent>
            </Card>
        </div>
    );
}
