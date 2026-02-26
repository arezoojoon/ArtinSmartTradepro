"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Calculator, Plus, X, Loader2, DollarSign, TrendingUp, AlertTriangle, Copy, BarChart3, PieChart, Play } from "lucide-react";
import api from "@/lib/api";

interface Scenario {
    id: string;
    name: string;
    currency: string;
    created_at: string;
    total_costs?: number;
    risk_adjusted_margin?: number;
}

interface SimResult {
    total_costs: number;
    total_risk_impact: number;
    risk_adjusted_margin: number;
    costs: { name: string; amount: number; cost_type: string }[];
    risks: { factor_type: string; probability: number; impact_percent: number }[];
}

export default function FinanceSimulatorPage() {
    const [scenarios, setScenarios] = useState<Scenario[]>([]);
    const [loading, setLoading] = useState(true);
    const [showCreate, setShowCreate] = useState(false);
    const [showCost, setShowCost] = useState<string | null>(null);
    const [showRisk, setShowRisk] = useState<string | null>(null);
    const [simResults, setSimResults] = useState<Record<string, SimResult>>({});
    const [simulating, setSimulating] = useState<string | null>(null);
    const [form, setForm] = useState({ name: "", currency: "USD" });
    const [costForm, setCostForm] = useState({ name: "", amount: "", cost_type: "variable" });
    const [riskForm, setRiskForm] = useState({ factor_type: "fx", probability: "0.3", impact_percent: "5" });
    const [saving, setSaving] = useState(false);

    const fetchScenarios = async () => {
        try {
            const res = await api.get("/financial/scenarios");
            setScenarios(Array.isArray(res.data) ? res.data : []);
        } catch { setScenarios([]); }
        finally { setLoading(false); }
    };

    useEffect(() => { fetchScenarios(); }, []);

    const handleCreate = async () => {
        if (!form.name) return;
        setSaving(true);
        try {
            await api.post("/financial/scenarios", form);
            setShowCreate(false);
            setForm({ name: "", currency: "USD" });
            fetchScenarios();
        } catch (e) { console.error("Create failed", e); }
        finally { setSaving(false); }
    };

    const handleAddCost = async () => {
        if (!costForm.name || !costForm.amount || !showCost) return;
        setSaving(true);
        try {
            await api.post("/financial/costs", { scenario_id: showCost, name: costForm.name, amount: parseFloat(costForm.amount), cost_type: costForm.cost_type });
            setCostForm({ name: "", amount: "", cost_type: "variable" });
            setShowCost(null);
            runSimulation(showCost);
        } catch (e) { console.error("Add cost failed", e); }
        finally { setSaving(false); }
    };

    const handleAddRisk = async () => {
        if (!showRisk) return;
        setSaving(true);
        try {
            await api.post("/financial/risks", { scenario_id: showRisk, factor_type: riskForm.factor_type, probability: parseFloat(riskForm.probability), impact_percent: parseFloat(riskForm.impact_percent) });
            setRiskForm({ factor_type: "fx", probability: "0.3", impact_percent: "5" });
            setShowRisk(null);
            runSimulation(showRisk);
        } catch (e) { console.error("Add risk failed", e); }
        finally { setSaving(false); }
    };

    const runSimulation = async (id: string) => {
        setSimulating(id);
        try {
            const res = await api.get(`/financial/scenarios/${id}/simulation`);
            setSimResults(prev => ({ ...prev, [id]: res.data }));
        } catch (e) { console.error("Simulation failed", e); }
        finally { setSimulating(null); }
    };

    const cloneScenario = async (id: string, name: string) => {
        try {
            await api.post(`/financial/scenarios/${id}/clone`, { new_name: `${name} (Copy)` });
            fetchScenarios();
        } catch (e) { console.error("Clone failed", e); }
    };

    return (
        <div className="space-y-6 p-4 md:p-8 max-w-[1400px] mx-auto">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold flex items-center gap-2 text-white">
                        <Calculator className="h-6 w-6 text-blue-400" /> Finance Simulator
                    </h1>
                    <p className="text-white/50 text-sm">Create trade scenarios, add costs and risks, run margin simulations</p>
                </div>
                <Button onClick={() => setShowCreate(true)} className="bg-[#f5a623] text-black hover:bg-[#e09000]">
                    <Plus className="h-4 w-4 mr-2" /> New Scenario
                </Button>
            </div>

            {/* Stats */}
            <div className="grid gap-4 sm:grid-cols-3">
                <Card className="bg-[#0e1e33] border-[#1e3a5f]"><CardContent className="p-4 flex items-center justify-between">
                    <div><p className="text-white/50 text-xs uppercase">Scenarios</p><p className="text-xl font-bold text-white mt-1">{scenarios.length}</p></div>
                    <PieChart className="h-7 w-7 text-blue-400/40" />
                </CardContent></Card>
                <Card className="bg-[#0e1e33] border-[#1e3a5f]"><CardContent className="p-4 flex items-center justify-between">
                    <div><p className="text-white/50 text-xs uppercase">Simulated</p><p className="text-xl font-bold text-emerald-400 mt-1">{Object.keys(simResults).length}</p></div>
                    <BarChart3 className="h-7 w-7 text-emerald-400/40" />
                </CardContent></Card>
                <Card className="bg-[#0e1e33] border-[#1e3a5f]"><CardContent className="p-4 flex items-center justify-between">
                    <div><p className="text-white/50 text-xs uppercase">Avg Margin</p><p className="text-xl font-bold text-[#f5a623] mt-1">{Object.values(simResults).length > 0 ? `${(Object.values(simResults).reduce((s, r) => s + (r.risk_adjusted_margin || 0), 0) / Object.values(simResults).length).toFixed(1)}%` : "—"}</p></div>
                    <TrendingUp className="h-7 w-7 text-[#f5a623]/40" />
                </CardContent></Card>
            </div>

            {/* Scenario List */}
            {loading ? (
                <div className="flex justify-center py-16"><Loader2 className="h-6 w-6 animate-spin text-white/40" /></div>
            ) : scenarios.length === 0 ? (
                <Card className="bg-[#0e1e33] border-[#1e3a5f]"><CardContent className="py-16 text-center">
                    <Calculator className="h-12 w-12 mx-auto mb-3 text-white/10" />
                    <p className="text-white/40 text-sm">No scenarios yet</p>
                    <Button onClick={() => setShowCreate(true)} variant="link" className="text-[#f5a623] mt-2">Create your first scenario</Button>
                </CardContent></Card>
            ) : (
                <div className="space-y-4">
                    {scenarios.map(sc => {
                        const sim = simResults[sc.id];
                        return (
                            <Card key={sc.id} className="bg-[#0e1e33] border-[#1e3a5f]">
                                <CardContent className="p-5">
                                    <div className="flex items-center justify-between mb-4">
                                        <div>
                                            <h3 className="text-white font-bold text-lg">{sc.name}</h3>
                                            <p className="text-white/40 text-xs">{sc.currency} · Created {new Date(sc.created_at).toLocaleDateString()}</p>
                                        </div>
                                        <div className="flex gap-2">
                                            <Button size="sm" variant="outline" className="border-white/20 text-white text-xs" onClick={() => setShowCost(sc.id)}>
                                                <DollarSign className="h-3 w-3 mr-1" /> Add Cost
                                            </Button>
                                            <Button size="sm" variant="outline" className="border-white/20 text-white text-xs" onClick={() => setShowRisk(sc.id)}>
                                                <AlertTriangle className="h-3 w-3 mr-1" /> Add Risk
                                            </Button>
                                            <Button size="sm" variant="outline" className="border-white/20 text-white text-xs" onClick={() => cloneScenario(sc.id, sc.name)}>
                                                <Copy className="h-3 w-3 mr-1" /> Clone
                                            </Button>
                                            <Button size="sm" className="bg-blue-600 text-white text-xs" onClick={() => runSimulation(sc.id)} disabled={simulating === sc.id}>
                                                {simulating === sc.id ? <Loader2 className="h-3 w-3 animate-spin mr-1" /> : <Play className="h-3 w-3 mr-1" />} Simulate
                                            </Button>
                                        </div>
                                    </div>
                                    {sim && (
                                        <div className="grid grid-cols-3 gap-3 mt-3 p-3 bg-white/5 rounded-lg">
                                            <div className="text-center">
                                                <p className="text-white/40 text-[10px] uppercase">Total Costs</p>
                                                <p className="text-rose-400 font-bold">${sim.total_costs?.toLocaleString()}</p>
                                            </div>
                                            <div className="text-center">
                                                <p className="text-white/40 text-[10px] uppercase">Risk Impact</p>
                                                <p className="text-amber-400 font-bold">{sim.total_risk_impact?.toFixed(1)}%</p>
                                            </div>
                                            <div className="text-center">
                                                <p className="text-white/40 text-[10px] uppercase">Adj. Margin</p>
                                                <p className={`font-bold ${(sim.risk_adjusted_margin || 0) >= 0 ? "text-emerald-400" : "text-rose-400"}`}>{sim.risk_adjusted_margin?.toFixed(1)}%</p>
                                            </div>
                                        </div>
                                    )}
                                </CardContent>
                            </Card>
                        );
                    })}
                </div>
            )}

            {/* Create Scenario Modal */}
            {showCreate && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50" onClick={() => setShowCreate(false)}>
                    <div className="bg-[#0e1e33] border border-[#1e3a5f] rounded-xl p-6 w-full max-w-sm space-y-4" onClick={e => e.stopPropagation()}>
                        <div className="flex items-center justify-between"><h3 className="text-white font-bold">New Scenario</h3><button onClick={() => setShowCreate(false)}><X className="h-5 w-5 text-white/40" /></button></div>
                        <Input placeholder="Scenario Name *" value={form.name} onChange={e => setForm(p => ({ ...p, name: e.target.value }))} className="bg-white/5 border-white/10 text-white" />
                        <select value={form.currency} onChange={e => setForm(p => ({ ...p, currency: e.target.value }))} className="w-full p-2 bg-white/5 border border-white/10 text-white rounded-md text-sm">
                            <option value="USD">USD</option><option value="EUR">EUR</option><option value="GBP">GBP</option><option value="AED">AED</option>
                        </select>
                        <Button onClick={handleCreate} disabled={saving || !form.name} className="w-full bg-[#f5a623] text-black hover:bg-[#e09000]">
                            {saving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Plus className="h-4 w-4 mr-2" />} Create
                        </Button>
                    </div>
                </div>
            )}

            {/* Add Cost Modal */}
            {showCost && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50" onClick={() => setShowCost(null)}>
                    <div className="bg-[#0e1e33] border border-[#1e3a5f] rounded-xl p-6 w-full max-w-sm space-y-4" onClick={e => e.stopPropagation()}>
                        <div className="flex items-center justify-between"><h3 className="text-white font-bold">Add Cost Component</h3><button onClick={() => setShowCost(null)}><X className="h-5 w-5 text-white/40" /></button></div>
                        <Input placeholder="Cost Name (e.g. Freight)" value={costForm.name} onChange={e => setCostForm(p => ({ ...p, name: e.target.value }))} className="bg-white/5 border-white/10 text-white" />
                        <Input placeholder="Amount" type="number" value={costForm.amount} onChange={e => setCostForm(p => ({ ...p, amount: e.target.value }))} className="bg-white/5 border-white/10 text-white" />
                        <select value={costForm.cost_type} onChange={e => setCostForm(p => ({ ...p, cost_type: e.target.value }))} className="w-full p-2 bg-white/5 border border-white/10 text-white rounded-md text-sm">
                            <option value="fixed">Fixed</option><option value="variable">Variable</option>
                        </select>
                        <Button onClick={handleAddCost} disabled={saving || !costForm.name || !costForm.amount} className="w-full bg-[#f5a623] text-black hover:bg-[#e09000]">
                            {saving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Plus className="h-4 w-4 mr-2" />} Add Cost
                        </Button>
                    </div>
                </div>
            )}

            {/* Add Risk Modal */}
            {showRisk && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50" onClick={() => setShowRisk(null)}>
                    <div className="bg-[#0e1e33] border border-[#1e3a5f] rounded-xl p-6 w-full max-w-sm space-y-4" onClick={e => e.stopPropagation()}>
                        <div className="flex items-center justify-between"><h3 className="text-white font-bold">Add Risk Factor</h3><button onClick={() => setShowRisk(null)}><X className="h-5 w-5 text-white/40" /></button></div>
                        <select value={riskForm.factor_type} onChange={e => setRiskForm(p => ({ ...p, factor_type: e.target.value }))} className="w-full p-2 bg-white/5 border border-white/10 text-white rounded-md text-sm">
                            <option value="fx">FX Risk</option><option value="compliance">Compliance</option><option value="logistics">Logistics</option><option value="political">Political</option><option value="credit">Credit</option>
                        </select>
                        <div className="grid grid-cols-2 gap-3">
                            <div><label className="text-white/50 text-xs">Probability (0-1)</label><Input type="number" step="0.1" value={riskForm.probability} onChange={e => setRiskForm(p => ({ ...p, probability: e.target.value }))} className="bg-white/5 border-white/10 text-white" /></div>
                            <div><label className="text-white/50 text-xs">Impact %</label><Input type="number" value={riskForm.impact_percent} onChange={e => setRiskForm(p => ({ ...p, impact_percent: e.target.value }))} className="bg-white/5 border-white/10 text-white" /></div>
                        </div>
                        <Button onClick={handleAddRisk} disabled={saving} className="w-full bg-[#f5a623] text-black hover:bg-[#e09000]">
                            {saving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Plus className="h-4 w-4 mr-2" />} Add Risk
                        </Button>
                    </div>
                </div>
            )}
        </div>
    );
}
