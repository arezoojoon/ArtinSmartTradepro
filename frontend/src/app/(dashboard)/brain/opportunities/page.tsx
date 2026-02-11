"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Briefcase, Plus, User, Truck, TrendingUp, CheckCircle, ArrowRight } from "lucide-react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Progress } from "@/components/ui/progress";

export default function OpportunitiesPage() {
    const [opps, setOpps] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [open, setOpen] = useState(false);

    // Form Data
    const [buyers, setBuyers] = useState<any[]>([]);
    const [suppliers, setSuppliers] = useState<any[]>([]);
    const [newOpp, setNewOpp] = useState({
        title: "",
        buyer_id: "",
        supplier_id: ""
    });

    const refreshData = async () => {
        setLoading(true);
        try {
            const [oppsRes, buyersRes, suppliersRes] = await Promise.all([
                api.get("/api/v1/execution/opportunities"),
                // Assuming these endpoints exist from previous modules or using stubs if mostly empty
                api.get("/api/v1/crm/companies").catch(() => ({ data: [] })),
                api.get("/api/v1/sourcing/suppliers").catch(() => ({ data: [] }))
            ]);
            setOpps(oppsRes.data);
            setBuyers(buyersRes.data);
            setSuppliers(suppliersRes.data);
        } catch (e) {
            console.error("Failed to load data", e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        refreshData();
    }, []);

    const createOpportunity = async () => {
        try {
            await api.post("/api/v1/execution/opportunities", newOpp);
            setOpen(false);
            setNewOpp({ title: "", buyer_id: "", supplier_id: "" });
            refreshData();
        } catch (e) {
            alert("Failed to create opportunity");
        }
    };

    return (
        <div className="p-8 space-y-8 bg-black min-h-screen text-white">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold flex items-center gap-2">
                        <Briefcase className="h-8 w-8 text-gold-500" />
                        Deal Flow
                    </h1>
                    <p className="text-gray-400">Match Buyers with Suppliers & Execute Trades</p>
                </div>

                <Dialog open={open} onOpenChange={setOpen}>
                    <DialogTrigger asChild>
                        <Button className="bg-gold-500 text-black hover:bg-gold-400">
                            <Plus className="h-4 w-4 mr-2" /> New Deal
                        </Button>
                    </DialogTrigger>
                    <DialogContent className="bg-navy-900 border-navy-800 text-white">
                        <DialogHeader>
                            <DialogTitle>Create Trade Opportunity</DialogTitle>
                        </DialogHeader>
                        <div className="space-y-4 py-4">
                            <Input
                                placeholder="Deal Title (e.g. Export 50k Tiles to UAE)"
                                className="bg-navy-950 border-navy-700"
                                value={newOpp.title}
                                onChange={(e) => setNewOpp({ ...newOpp, title: e.target.value })}
                            />

                            <div className="grid grid-cols-2 gap-4">
                                <Select value={newOpp.buyer_id} onValueChange={(v) => setNewOpp({ ...newOpp, buyer_id: v })}>
                                    <SelectTrigger className="bg-navy-950 border-navy-700">
                                        <SelectValue placeholder="Select Buyer" />
                                    </SelectTrigger>
                                    <SelectContent className="bg-navy-900 border-navy-700 text-white">
                                        {buyers.map(b => (
                                            <SelectItem key={b.id} value={b.id}>{b.company_name}</SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>

                                <Select value={newOpp.supplier_id} onValueChange={(v) => setNewOpp({ ...newOpp, supplier_id: v })}>
                                    <SelectTrigger className="bg-navy-950 border-navy-700">
                                        <SelectValue placeholder="Select Supplier" />
                                    </SelectTrigger>
                                    <SelectContent className="bg-navy-900 border-navy-700 text-white">
                                        {suppliers.map(s => (
                                            <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>

                            <Button onClick={createOpportunity} className="w-full bg-gold-500 text-black">
                                Create Deal
                            </Button>
                        </div>
                    </DialogContent>
                </Dialog>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {loading ? (
                    <div className="text-gray-500">Loading Deals...</div>
                ) : opps.length === 0 ? (
                    <div className="col-span-full text-center py-12 bg-navy-900/50 rounded border border-dashed border-navy-700 text-gray-400">
                        No active deals. Start matching buyers.
                    </div>
                ) : (
                    opps.map((opp) => (
                        <Card key={opp.id} className="bg-navy-900 border-navy-800 hover:border-gold-500/50 transition-colors group">
                            <CardHeader className="pb-3">
                                <div className="flex justify-between items-start">
                                    <CardTitle className="text-lg text-white">{opp.title}</CardTitle>
                                    <Badge variant="outline" className="uppercase text-[10px] tracking-widest border-gray-600 text-gray-400">
                                        {opp.stage}
                                    </Badge>
                                </div>
                                <CardDescription className="text-xs text-gray-500">
                                    ID: {opp.id.substring(0, 8)}...
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                {/* The Connection */}
                                <div className="flex items-center justify-between text-sm">
                                    <div className="flex items-center gap-2 text-blue-400">
                                        <User className="h-4 w-4" />
                                        <span className="truncate max-w-[100px]">{opp.buyer_name}</span>
                                    </div>
                                    <ArrowRight className="h-4 w-4 text-gray-600" />
                                    <div className="flex items-center gap-2 text-purple-400">
                                        <Truck className="h-4 w-4" />
                                        <span className="truncate max-w-[100px]">{opp.supplier_name}</span>
                                    </div>
                                </div>

                                {/* Win Prob */}
                                <div>
                                    <div className="flex justify-between text-xs mb-1">
                                        <span className="text-gray-400">Win Probability</span>
                                        <span className={opp.win_probability > 70 ? "text-green-500" : "text-yellow-500"}>
                                            {opp.win_probability}%
                                        </span>
                                    </div>
                                    <Progress value={opp.win_probability} className="h-1 bg-navy-950" indicatorClassName={opp.win_probability > 70 ? "bg-green-500" : "bg-yellow-500"} />
                                </div>
                            </CardContent>
                            <CardFooter className="pt-2 border-t border-navy-800 flex justify-between">
                                <Button variant="ghost" size="sm" className="text-xs text-gray-400 hover:text-white" onClick={() => window.location.href = `/finance/simulator?scenario_id=${opp.scenario_id}`}>
                                    <TrendingUp className="h-3 w-3 mr-1" /> View Economics
                                </Button>
                                <Button size="sm" className="bg-navy-800 text-white hover:bg-gold-500 hover:text-black">
                                    Execute
                                </Button>
                            </CardFooter>
                        </Card>
                    ))
                )}
            </div>
        </div>
    );
}
