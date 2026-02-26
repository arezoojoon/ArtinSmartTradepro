"use client";

import { Card, CardContent } from "@/components/ui/card";
import { CreditCard } from "lucide-react";

export default function PaymentPage() {
    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold flex items-center gap-2">
                    <CreditCard className="h-8 w-8 text-indigo-400" />
                    Payments
                </h1>
                <p className="text-gray-400 mt-1">Manage invoices, payments, and billing</p>
            </div>
            <Card className="bg-[#0e1e33] border-[#1e3a5f]">
                <CardContent className="py-16 text-center">
                    <CreditCard className="h-16 w-16 mx-auto mb-4 text-gray-700" />
                    <p className="text-amber-400/80 font-medium">Payment Management — Under Development</p>
                    <p className="text-xs text-gray-600 mt-2">Track invoices, process payments, and manage billing cycles. This feature is being built.</p>
                </CardContent>
            </Card>
        </div>
    );
}
