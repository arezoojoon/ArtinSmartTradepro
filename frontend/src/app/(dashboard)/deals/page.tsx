"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
    Handshake, FileText, Shield, DollarSign, Clock,
    Users, Globe, Plus, Loader2
} from "lucide-react";
import Link from "next/link";
import api from "@/lib/api";

const DEAL_STAGES = [
    { id: "identified", label: "Identified", color: "bg-slate-500" },
    { id: "matching", label: "Matching", color: "bg-blue-500" },
    { id: "validating", label: "Validating", color: "bg-amber-500" },
    { id: "negotiating", label: "Negotiating", color: "bg-purple-500" },
    { id: "closed_won", label: "Closed Won", color: "bg-emerald-500" },
    { id: "closed_lost", label: "Closed Lost", color: "bg-rose-500" },
];

export default function DealsPage() {
    const [deals, setDeals] = useState<any[]>([]);
    const [pipelines, setPipelines] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [pipeRes] = await Promise.all([
                    api.get("/crm/pipelines")
                ]);
                const pipes = pipeRes.data || [];
                setPipelines(pipes);

                // Fetch deals from first pipeline if available
                if (pipes.length > 0) {
                    const dealRes = await api.get(`/crm/pipelines/${pipes[0].id}/board`);
                    const boardDeals = dealRes.data?.deals || dealRes.data || [];
                    setDeals(Array.isArray(boardDeals) ? boardDeals : []);
                }
            } catch (e) {
                console.error("Failed to fetch deals:", e);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    // Count deals per stage
    const stageCounts: Record<string, number> = {};
    deals.forEach((d: any) => {
        const sid = d.stage_id || d.status || "unknown";
        stageCounts[sid] = (stageCounts[sid] || 0) + 1;
    });

    return (
        <div className="p-4 md:p-8 space-y-6 text-white">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-bold flex items-center gap-2">
                        <Handshake className="h-6 w-6 text-[#f5a623]" /> Deal Room
                    </h1>
                    <p className="text-white/60 text-sm">
                        Manage end-to-end trade deals: buyer, supplier, incoterms, docs, margins
                    </p>
                </div>
                <Link href="/crm/pipelines">
                    <Button className="bg-gold-500 hover:bg-gold-600 text-navy-900 font-bold">
                        <Plus className="h-4 w-4 mr-2" /> Manage Pipelines
                    </Button>
                </Link>
            </div>

            {loading ? (
                <div className="flex items-center justify-center py-12">
                    <Loader2 className="h-6 w-6 animate-spin text-[#f5a623]" />
                    <span className="ml-2 text-white/60">Loading deals...</span>
                </div>
            ) : (
            <>
            {/* Stage Pipeline */}
            <div className="flex gap-2 overflow-x-auto pb-2">
                {DEAL_STAGES.map((stage) => (
                    <div
                        key={stage.id}
                        className="flex items-center gap-2 px-4 py-2 bg-[#0e1e33] border border-[#1e3a5f] rounded-lg whitespace-nowrap"
                    >
                        <div className={`h-2.5 w-2.5 rounded-full ${stage.color}`}></div>
                        <span className="text-sm font-medium">{stage.label}</span>
                        <Badge variant="outline" className="text-white/40 border-white/10 text-xs ml-1">
                            {stageCounts[stage.id] || 0}
                        </Badge>
                    </div>
                ))}
            </div>

            {/* Deal List */}
            {deals.length === 0 ? (
                <Card className="bg-[#0e1e33] border-[#1e3a5f]">
                    <CardContent className="p-12 flex flex-col items-center justify-center text-center">
                        <Handshake className="h-16 w-16 text-navy-700 mb-4" />
                        <h3 className="text-xl font-bold text-white mb-2">No deals yet</h3>
                        <p className="text-white/50 max-w-md mb-6">
                            Create your first deal to track buyers, suppliers, price components,
                            documents, risk checklists, and margin calculations in one place.
                        </p>
                        <Link href="/crm/pipelines">
                            <Button className="bg-gold-500 hover:bg-gold-600 text-navy-900 font-bold">
                                Go to Pipelines
                            </Button>
                        </Link>
                    </CardContent>
                </Card>
            ) : (
                <div className="grid gap-3">
                    {deals.map((deal: any) => (
                        <Card key={deal.id} className="bg-[#0e1e33] border-[#1e3a5f] hover:border-gold-500/30 transition-colors">
                            <CardContent className="p-4 flex items-center justify-between">
                                <div>
                                    <h4 className="font-semibold text-white">{deal.name}</h4>
                                    <p className="text-xs text-white/50">
                                        {deal.currency || "AED"} {Number(deal.value || 0).toLocaleString()} · {deal.status || deal.stage_id}
                                    </p>
                                </div>
                                <Badge variant="outline" className="text-[#f5a623] border-gold-500/30 capitalize">
                                    {deal.status || "open"}
                                </Badge>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            )}

            {/* Deal Room Features Checklist */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {[
                    { icon: Users, title: "Parties", desc: "Buyer + Supplier with contacts" },
                    { icon: Globe, title: "Incoterms", desc: "FOB, CIF, DDP, EXW..." },
                    { icon: DollarSign, title: "Price Components", desc: "Freight, insurance, customs, markup" },
                    { icon: FileText, title: "Documents", desc: "BL, Invoice, COO, LC checklist" },
                    { icon: Shield, title: "Risk Checklist", desc: "Sanction, customs, FX, supplier" },
                    { icon: Clock, title: "Timeline", desc: "Key dates and milestones" },
                ].map((feat) => (
                    <Card key={feat.title} className="bg-[#0e1e33]/50 border-[#1e3a5f] hover:border-gold-500/30 transition-colors cursor-pointer">
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
            </>
            )}
        </div>
    );
}
