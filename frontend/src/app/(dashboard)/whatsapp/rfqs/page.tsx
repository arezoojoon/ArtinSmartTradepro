"use client";

import { Card, CardContent } from "@/components/ui/card";
import { MessageSquare } from "lucide-react";

export default function WhatsAppRFQsPage() {
    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold flex items-center gap-2">
                    <MessageSquare className="h-8 w-8 text-green-400" />
                    WhatsApp RFQs
                </h1>
                <p className="text-gray-400 mt-1">Send and track RFQs through WhatsApp</p>
            </div>
            <Card className="bg-[#0e1e33] border-[#1e3a5f]">
                <CardContent className="py-16 text-center">
                    <MessageSquare className="h-16 w-16 mx-auto mb-4 text-gray-700" />
                    <p className="text-gray-500">WhatsApp RFQs — Coming Soon</p>
                    <p className="text-xs text-gray-600 mt-2">Send automated RFQ messages to suppliers via WhatsApp.</p>
                </CardContent>
            </Card>
        </div>
    );
}
