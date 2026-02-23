"use client";

import { Card, CardContent } from "@/components/ui/card";
import { ShoppingBag } from "lucide-react";

export default function CatalogPage() {
    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold flex items-center gap-2">
                    <ShoppingBag className="h-8 w-8 text-amber-400" />
                    Product Catalog
                </h1>
                <p className="text-gray-400 mt-1">Manage your WhatsApp product catalog</p>
            </div>

            <Card className="bg-[#0e1e33] border-[#1e3a5f]">
                <CardContent className="py-16 text-center">
                    <ShoppingBag className="h-16 w-16 mx-auto mb-4 text-gray-700" />
                    <p className="text-gray-500">Product Catalog — Coming Soon</p>
                    <p className="text-xs text-gray-600 mt-2">
                        Share your product catalog directly through WhatsApp conversations.
                    </p>
                </CardContent>
            </Card>
        </div>
    );
}
