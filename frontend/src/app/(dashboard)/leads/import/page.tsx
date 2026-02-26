"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Upload } from "lucide-react";

export default function ImportLeadsPage() {
    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold flex items-center gap-2">
                    <Upload className="h-8 w-8 text-purple-400" />
                    Import Leads
                </h1>
                <p className="text-gray-400 mt-1">Upload CSV/Excel files to bulk-import leads</p>
            </div>
            <Card className="bg-[#0e1e33] border-[#1e3a5f]">
                <CardContent className="py-16 text-center">
                    <Upload className="h-16 w-16 mx-auto mb-4 text-gray-700" />
                    <p className="text-amber-400/80 font-medium">Lead Import — Under Development</p>
                    <p className="text-xs text-gray-600 mt-2">Upload CSV or Excel files to import leads into your CRM. This feature is being built.</p>
                </CardContent>
            </Card>
        </div>
    );
}
