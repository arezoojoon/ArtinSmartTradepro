"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
    ShoppingCart, MapPin, DollarSign, Clock, User, Package
} from "lucide-react";

export default function RFQsPage() {
    const [rfqs, setRfqs] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        api.get("/api/v1/sourcing/rfqs")
            .then(res => {
                const data = res.data;
                setRfqs(Array.isArray(data) ? data : (data?.rfqs || []));
            })
            .catch(() => setRfqs([]))
            .finally(() => setLoading(false));
    }, []);

    const statusColor = (status: string) => {
        switch (status) {
            case "open": return "bg-emerald-900/60 text-emerald-300";
            case "quoted": return "bg-blue-900/60 text-blue-300";
            case "awarded": return "bg-gold-900/60 text-gold-300";
            case "closed": return "bg-gray-800 text-gray-400";
            default: return "bg-navy-800 text-gray-400";
        }
    };

    return (
        <div className="p-8 bg-black min-h-screen text-white">
            <div className="mb-8">
                <h1 className="text-3xl font-bold flex items-center gap-2">
                    <ShoppingCart className="h-8 w-8 text-blue-400" />
                    Incoming Buyer Requests (RFQs)
                </h1>
                <p className="text-gray-400">Requests from WhatsApp bot buyers — respond to close deals</p>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                <Card className="bg-navy-900 border-navy-800">
                    <CardContent className="pt-4 text-center">
                        <p className="text-2xl font-bold text-white">{rfqs.length}</p>
                        <p className="text-xs text-gray-500">Total RFQs</p>
                    </CardContent>
                </Card>
                <Card className="bg-navy-900 border-navy-800">
                    <CardContent className="pt-4 text-center">
                        <p className="text-2xl font-bold text-emerald-400">{rfqs.filter(r => r.status === "open").length}</p>
                        <p className="text-xs text-gray-500">Open</p>
                    </CardContent>
                </Card>
                <Card className="bg-navy-900 border-navy-800">
                    <CardContent className="pt-4 text-center">
                        <p className="text-2xl font-bold text-blue-400">{rfqs.filter(r => r.status === "quoted").length}</p>
                        <p className="text-xs text-gray-500">Quoted</p>
                    </CardContent>
                </Card>
                <Card className="bg-navy-900 border-navy-800">
                    <CardContent className="pt-4 text-center">
                        <p className="text-2xl font-bold text-gold-400">{rfqs.filter(r => r.status === "awarded").length}</p>
                        <p className="text-xs text-gray-500">Awarded</p>
                    </CardContent>
                </Card>
            </div>

            {loading ? (
                <p className="text-gray-500">Loading...</p>
            ) : rfqs.length === 0 ? (
                <Card className="bg-navy-900 border-navy-800">
                    <CardContent className="py-16 text-center">
                        <ShoppingCart className="h-16 w-16 mx-auto mb-4 text-gray-700" />
                        <p className="text-gray-500">No buyer requests yet. RFQs from the WhatsApp bot will appear here.</p>
                    </CardContent>
                </Card>
            ) : (
                <div className="space-y-4">
                    {rfqs.map((rfq: any) => (
                        <Card key={rfq.id} className="bg-navy-900 border-navy-800 hover:border-blue-800 transition">
                            <CardContent className="pt-4">
                                <div className="flex justify-between items-start mb-3">
                                    <div>
                                        <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                                            <Package className="h-4 w-4 text-blue-400" />
                                            {rfq.title}
                                        </h3>
                                        <p className="text-sm text-gray-400 mt-1 whitespace-pre-line">
                                            {rfq.description}
                                        </p>
                                    </div>
                                    <Badge className={statusColor(rfq.status)}>
                                        {rfq.status?.toUpperCase()}
                                    </Badge>
                                </div>
                                <div className="flex gap-4 text-xs text-gray-500">
                                    {rfq.budget && (
                                        <span className="flex items-center gap-1">
                                            <DollarSign className="h-3 w-3" /> {rfq.budget}
                                        </span>
                                    )}
                                    {rfq.deadline && (
                                        <span className="flex items-center gap-1">
                                            <Clock className="h-3 w-3" /> {rfq.deadline}
                                        </span>
                                    )}
                                </div>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            )}
        </div>
    );
}
