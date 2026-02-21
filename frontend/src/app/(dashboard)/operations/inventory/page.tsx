"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Package } from "lucide-react";

export default function InventoryPage() {
    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold flex items-center gap-2">
                    <Package className="h-8 w-8 text-teal-400" />
                    Inventory Management
                </h1>
                <p className="text-gray-400 mt-1">Track stock levels, shipments, and warehouse operations</p>
            </div>
            <Card className="bg-navy-900 border-navy-800">
                <CardContent className="py-16 text-center">
                    <Package className="h-16 w-16 mx-auto mb-4 text-gray-700" />
                    <p className="text-gray-500">Inventory — Coming Soon</p>
                    <p className="text-xs text-gray-600 mt-2">Monitor stock levels and shipment tracking.</p>
                </CardContent>
            </Card>
        </div>
    );
}
