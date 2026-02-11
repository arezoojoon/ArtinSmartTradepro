"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Calculator, Plus, TrendingUp, AlertTriangle, DollarSign } from "lucide-react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";

export default function FinancialSimulatorPage() {
    const [scenarios, setScenarios] = useState<any[]>([]);
    const [selectedScenarioId, setSelectedScenarioId] = useState<string | null>(null);
    const [simulation, setSimulation] = useState<any>(null);
    const [loading, setLoading] = useState(false);

    // Forms
    const [newScenarioName, setNewScenarioName] = useState("");
    const [openScenarioDialog, setOpenScenarioDialog] = useState(false);

    useEffect(() => {
        fetchScenarios();
    }, []);

    useEffect(() => {
        if (selectedScenarioId) {
            fetchSimulation(selectedScenarioId);
        }
    }, [selectedScenarioId]);

    const fetchScenarios = async () => {
        try {
            const res = await api.get("/api/v1/finance/scenarios");
            setScenarios(res.data);
            if (res.data.length > 0 && !selectedScenarioId) {
                setSelectedScenarioId(res.data[0].id);
            }
        } catch (e) {
            console.error(e);
        }
    };

    const fetchSimulation = async (id: string) => {
        setLoading(true);
        try {
            const res = await api.get(`/api/v1/finance/scenarios/${id}/simulation`);
            setSimulation(res.data);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    const createScenario = async () => {
        try {
            const res = await api.post("/api/v1/finance/scenarios", { name: newScenarioName, currency: "USD" });
            setScenarios([...scenarios, res.data]);
            setSelectedScenarioId(res.data.id);
            setOpenScenarioDialog(false);
            setNewScenarioName("");
        } catch (e) {
            alert("Failed to create scenario");
        }
    };

    const addCost = async (name: string, amount: number) => {
        if (!selectedScenarioId) return;
        try {
            await api.post("/api/v1/finance/costs", {
                scenario_id: selectedScenarioId,
                name,
                amount,
                cost_type: "variable"
            });
            fetchSimulation(selectedScenarioId);
        } catch (e) {
            console.error(e);
        }
    };

    const addRisk = async (type: string, impact: number, prob: number) => {
        if (!selectedScenarioId) return;
        try {
            await api.post("/api/v1/finance/risks", {
                scenario_id: selectedScenarioId,
                factor_type: type,
                impact_percent: impact,
                probability: prob
            });
            fetchSimulation(selectedScenarioId);
        } catch (e) {
            console.error(e);
        }
    };

    return (
        <div className="p-8 space-y-8 bg-black min-h-screen text-white">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold flex items-center gap-2">
                        <Calculator className="h-8 w-8 text-gold-500" />
                        Financial OS
                    </h1>
                    <p className="text-gray-400">Profit Simulator & Risk Engine</p>
                </div>

                <div className="flex gap-4">
                    <Select value={selectedScenarioId || ""} onValueChange={setSelectedScenarioId}>
                        <SelectTrigger className="w-[200px] bg-navy-900 border-navy-700">
                            <SelectValue placeholder="Select Scenario" />
                        </SelectTrigger>
                        <SelectContent className="bg-navy-900 border-navy-700 text-white">
                            {scenarios.map((s) => (
                                <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>
                            ))}
                        </SelectContent>
                    </Select>

                    <Dialog open={openScenarioDialog} onOpenChange={setOpenScenarioDialog}>
                        <DialogTrigger asChild>
                            <Button className="bg-gold-500 text-black hover:bg-gold-400">
                                <Plus className="h-4 w-4 mr-2" /> New Scenario
                            </Button>
                        </DialogTrigger>
                        <DialogContent className="bg-navy-900 border-navy-800 text-white">
                            <DialogHeader>
                                <DialogTitle>Create Trade Scenario</DialogTitle>
                            </DialogHeader>
                            <div className="space-y-4 py-4">
                                <Input
                                    placeholder="Scenario Name (e.g. Deal 101 - Optimistic)"
                                    className="bg-navy-950 border-navy-700"
                                    value={newScenarioName}
                                    onChange={(e) => setNewScenarioName(e.target.value)}
                                />
                                <Button onClick={createScenario} className="w-full bg-gold-500 text-black">
                                    Create
                                </Button>
                            </div>
                        </DialogContent>
                    </Dialog>
                </div>
            </div>

            {simulation && (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Left: Economics */}
                    <div className="lg:col-span-2 space-y-6">
                        <Card className="bg-navy-900 border-navy-800">
                            <CardHeader>
                                <CardTitle className="text-white flex items-center gap-2">
                                    <DollarSign className="h-5 w-5 text-green-500" />
                                    Deal Economics
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-6">
                                <div className="grid grid-cols-3 gap-4 text-center">
                                    <div className="p-4 bg-navy-950 rounded">
                                        <div className="text-gray-400 text-sm">Revenue (Est)</div>
                                        <div className="text-2xl font-bold text-white">${simulation.economics.revenue}</div>
                                    </div>
                                    <div className="p-4 bg-navy-950 rounded">
                                        <div className="text-gray-400 text-sm">Landed Cost</div>
                                        <div className="text-2xl font-bold text-red-400">${simulation.economics.landed_cost}</div>
                                    </div>
                                    <div className="p-4 bg-navy-950 rounded border border-green-500/30">
                                        <div className="text-green-400 text-sm">Net Profit</div>
                                        <div className="text-2xl font-bold text-green-500">${simulation.economics.net_profit}</div>
                                    </div>
                                </div>

                                <div>
                                    <h3 className="text-sm font-medium text-gray-400 mb-3">Cost Breakdown</h3>
                                    <div className="space-y-2">
                                        {Object.entries(simulation.cost_structure).map(([name, amount]: [string, any]) => (
                                            <div key={name} className="flex justify-between p-2 bg-navy-950 rounded text-sm">
                                                <span>{name}</span>
                                                <span className="font-mono">${amount}</span>
                                            </div>
                                        ))}
                                    </div>
                                    <div className="mt-4 flex gap-2">
                                        <Button size="sm" variant="outline" onClick={() => addCost("Freight", 1500)}>+ Freight ($1.5k)</Button>
                                        <Button size="sm" variant="outline" onClick={() => addCost("Insurance", 200)}>+ Insurance ($200)</Button>
                                        <Button size="sm" variant="outline" onClick={() => addCost("Customs", 500)}>+ Customs ($500)</Button>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Right: Risk Engine */}
                    <div className="space-y-6">
                        <Card className="bg-navy-900 border-navy-800">
                            <CardHeader>
                                <CardTitle className="text-white flex items-center gap-2">
                                    <AlertTriangle className="h-5 w-5 text-yellow-500" />
                                    Risk Adjusted Margin
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="text-center">
                                <div className="mb-6">
                                    <div className="text-sm text-gray-400 mb-1">Net Margin</div>
                                    <div className="text-3xl font-bold text-white">{simulation.economics.net_margin_percent}%</div>
                                </div>

                                <div className="flex justify-center items-center gap-4 mb-6">
                                    <div className="h-px bg-gray-700 flex-1"></div>
                                    <div className="text-red-500 font-bold">-{simulation.risk_analysis.risk_penalty_percent}% Risk</div>
                                    <div className="h-px bg-gray-700 flex-1"></div>
                                </div>

                                <div className="p-4 bg-gold-500/10 border border-gold-500 rounded">
                                    <div className="text-gold-500 text-sm font-bold uppercase tracking-widest">Risk Adjusted</div>
                                    <div className="text-4xl font-black text-white mt-1">
                                        {simulation.risk_analysis.risk_adjusted_margin_percent}%
                                    </div>
                                </div>
                            </CardContent>
                        </Card>

                        <Card className="bg-navy-900 border-navy-800">
                            <CardHeader>
                                <CardTitle className="text-sm text-gray-400">Active Risk Factors</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-2">
                                {simulation.risk_analysis.factors.map((f: any, i: number) => (
                                    <div key={i} className="flex justify-between items-center text-sm p-2 bg-navy-950 rounded">
                                        <span>{f.type}</span>
                                        <Badge variant="outline" className="text-red-400 border-red-900">
                                            -{f.expected_penalty}%
                                        </Badge>
                                    </div>
                                ))}
                                <div className="pt-4 flex flex-col gap-2">
                                    <Button size="sm" variant="ghost" className="text-red-400 hover:text-red-300 hover:bg-red-900/20" onClick={() => addRisk("FX Volatility", 5, 0.5)}>
                                        + FX Risk (Low)
                                    </Button>
                                    <Button size="sm" variant="ghost" className="text-red-400 hover:text-red-300 hover:bg-red-900/20" onClick={() => addRisk("Logistics Delay", 10, 0.3)}>
                                        + Delay Risk (Med)
                                    </Button>
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                </div>
            )}
        </div>
    );
}
