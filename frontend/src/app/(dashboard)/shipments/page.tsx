"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
    Ship, Package, FileText, AlertTriangle, MapPin,
    Clock, Plus, Search, ExternalLink
} from "lucide-react";

export default function ShipmentsPage() {
    return (
        <div className="p-4 md:p-8 space-y-6 text-white">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-bold flex items-center gap-2">
                        <Ship className="h-6 w-6 text-[#f5a623]" /> Shipment Tracking
                    </h1>
                    <p className="text-white/60 text-sm">
                        Track shipments, port delays, and manage trade documents
                    </p>
                </div>
                <Button className="bg-gold-500 hover:bg-gold-600 text-navy-900 font-bold">
                    <Plus className="h-4 w-4 mr-2" /> Add Shipment
                </Button>
            </div>

            {/* Status Summary */}
            <div className="grid gap-4 md:grid-cols-4">
                {[
                    { label: "In Transit", value: "0", icon: Ship, color: "text-blue-400" },
                    { label: "At Port", value: "0", icon: MapPin, color: "text-amber-400" },
                    { label: "Delivered", value: "0", icon: Package, color: "text-emerald-400" },
                    { label: "Delayed", value: "0", icon: AlertTriangle, color: "text-rose-400" },
                ].map((stat) => (
                    <Card key={stat.label} className="bg-[#0e1e33] border-[#1e3a5f]">
                        <CardContent className="p-4 flex items-center gap-3">
                            <div className="p-2 rounded-lg bg-navy-800">
                                <stat.icon className={`h-5 w-5 ${stat.color}`} />
                            </div>
                            <div>
                                <div className="text-2xl font-bold text-white">{stat.value}</div>
                                <div className="text-xs text-white/50">{stat.label}</div>
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>

            {/* Empty State */}
            <Card className="bg-[#0e1e33] border-[#1e3a5f]">
                <CardContent className="p-12 flex flex-col items-center justify-center text-center">
                    <Ship className="h-16 w-16 text-navy-700 mb-4" />
                    <h3 className="text-xl font-bold text-white mb-2">No shipments tracked</h3>
                    <p className="text-white/50 max-w-md mb-6">
                        Add a shipment to track container movements, port delays, and manage
                        your document vault (BL, Invoice, COO, Packing List).
                    </p>
                    <div className="flex gap-3">
                        <Button variant="outline" className="border-navy-700 text-white">
                            <Search className="h-4 w-4 mr-2" /> Track by BL Number
                        </Button>
                        <Button className="bg-gold-500 hover:bg-gold-600 text-navy-900 font-bold">
                            Add Shipment
                        </Button>
                    </div>
                </CardContent>
            </Card>

            {/* Features Grid */}
            <div className="grid gap-4 md:grid-cols-3">
                {[
                    { icon: Ship, title: "Container Tracking", desc: "Real-time location + ETA updates" },
                    { icon: AlertTriangle, title: "Port Delay Alerts", desc: "Congestion, demurrage risk warnings" },
                    { icon: FileText, title: "Document Vault", desc: "BL, Invoice, COO, certificates — all in one place" },
                ].map((feat) => (
                    <Card key={feat.title} className="bg-[#0e1e33]/50 border-[#1e3a5f] hover:border-gold-500/30 transition-colors">
                        <CardContent className="p-4 flex items-start gap-3">
                            <div className="p-2 rounded-lg bg-navy-800">
                                <feat.icon className="h-5 w-5 text-[#f5a623]" />
                            </div>
                            <div>
                                <h4 className="font-semibold text-white text-sm">{feat.title}</h4>
                                <p className="text-xs text-white/40">{feat.desc}</p>
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>
        </div>
    );
}
