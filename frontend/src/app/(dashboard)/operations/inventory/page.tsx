"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Package, Plus, Search, Warehouse, AlertTriangle, TrendingUp, TrendingDown, Loader2, X, Archive, BarChart3 } from "lucide-react";
import api from "@/lib/api";

interface InventoryItem {
    id: string;
    name: string;
    sku: string;
    quantity: number;
    min_stock: number;
    warehouse: string;
    category: string;
    unit_cost: number;
    status: string;
}

export default function InventoryPage() {
    const [items, setItems] = useState<InventoryItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState("");
    const [showModal, setShowModal] = useState(false);
    const [form, setForm] = useState({ name: "", sku: "", quantity: "0", min_stock: "10", warehouse: "Main Warehouse", category: "General", unit_cost: "0" });
    const [saving, setSaving] = useState(false);

    const fetchItems = async () => {
        try {
            const res = await api.get("/operations/inventory");
            setItems(Array.isArray(res.data) ? res.data : []);
        } catch { setItems([]); }
        finally { setLoading(false); }
    };

    useEffect(() => { fetchItems(); }, []);

    const handleCreate = async () => {
        if (!form.name || !form.sku) return;
        setSaving(true);
        try {
            await api.post("/operations/inventory", {
                name: form.name, sku: form.sku,
                quantity: parseInt(form.quantity) || 0,
                min_stock: parseInt(form.min_stock) || 10,
                warehouse: form.warehouse, category: form.category,
                unit_cost: parseFloat(form.unit_cost) || 0,
            });
            setShowModal(false);
            setForm({ name: "", sku: "", quantity: "0", min_stock: "10", warehouse: "Main Warehouse", category: "General", unit_cost: "0" });
            fetchItems();
        } catch (e) { console.error("Failed to create item", e); }
        finally { setSaving(false); }
    };

    const filtered = items.filter(i => i.name?.toLowerCase().includes(search.toLowerCase()) || i.sku?.toLowerCase().includes(search.toLowerCase()));
    const lowStock = items.filter(i => i.quantity <= i.min_stock).length;
    const totalValue = items.reduce((s, i) => s + (i.quantity * i.unit_cost), 0);
    const totalItems = items.reduce((s, i) => s + i.quantity, 0);

    return (
        <div className="space-y-6 p-4 md:p-8 max-w-[1400px] mx-auto">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold flex items-center gap-2 text-white">
                        <Package className="h-6 w-6 text-[#f5a623]" /> Inventory Management
                    </h1>
                    <p className="text-white/50 text-sm">Track stock levels, warehouses, and inventory value</p>
                </div>
                <Button onClick={() => setShowModal(true)} className="bg-[#f5a623] text-black hover:bg-[#e09000]">
                    <Plus className="h-4 w-4 mr-2" /> Add Item
                </Button>
            </div>

            {/* KPI Cards */}
            <div className="grid gap-4 sm:grid-cols-4">
                {[
                    { label: "Total SKUs", value: items.length, icon: Archive, color: "text-blue-400" },
                    { label: "Total Units", value: totalItems.toLocaleString(), icon: Package, color: "text-emerald-400" },
                    { label: "Inventory Value", value: `$${totalValue.toLocaleString()}`, icon: BarChart3, color: "text-[#f5a623]" },
                    { label: "Low Stock Alerts", value: lowStock, icon: AlertTriangle, color: "text-rose-400" },
                ].map((kpi) => (
                    <Card key={kpi.label} className="bg-[#0e1e33] border-[#1e3a5f]">
                        <CardContent className="p-4 flex items-center justify-between">
                            <div>
                                <p className="text-white/50 text-xs uppercase">{kpi.label}</p>
                                <p className={`text-xl font-bold mt-1 ${kpi.color}`}>{kpi.value}</p>
                            </div>
                            <kpi.icon className={`h-7 w-7 ${kpi.color} opacity-40`} />
                        </CardContent>
                    </Card>
                ))}
            </div>

            {/* Search + Table */}
            <Card className="bg-[#0e1e33] border-[#1e3a5f]">
                <CardHeader>
                    <div className="flex items-center gap-3">
                        <div className="relative flex-1">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-white/30" />
                            <Input placeholder="Search by name or SKU..." value={search} onChange={e => setSearch(e.target.value)} className="pl-10 bg-white/5 border-white/10 text-white" />
                        </div>
                    </div>
                </CardHeader>
                <CardContent>
                    {loading ? (
                        <div className="flex justify-center py-12"><Loader2 className="h-5 w-5 animate-spin text-white/40" /></div>
                    ) : filtered.length === 0 ? (
                        <div className="text-center py-12">
                            <Package className="h-12 w-12 mx-auto mb-3 text-white/10" />
                            <p className="text-white/40 text-sm">{items.length === 0 ? "No inventory items yet" : "No items match your search"}</p>
                            {items.length === 0 && <Button onClick={() => setShowModal(true)} variant="link" className="text-[#f5a623] mt-2">Add your first item</Button>}
                        </div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead><tr className="text-white/40 text-xs uppercase border-b border-white/5">
                                    <th className="text-left py-3 px-2">Item</th>
                                    <th className="text-left py-3 px-2">SKU</th>
                                    <th className="text-left py-3 px-2">Warehouse</th>
                                    <th className="text-right py-3 px-2">Qty</th>
                                    <th className="text-right py-3 px-2">Min</th>
                                    <th className="text-right py-3 px-2">Value</th>
                                    <th className="text-center py-3 px-2">Status</th>
                                </tr></thead>
                                <tbody className="divide-y divide-white/5">
                                    {filtered.map(item => {
                                        const isLow = item.quantity <= item.min_stock;
                                        return (
                                            <tr key={item.id} className="hover:bg-white/5 transition-colors">
                                                <td className="py-3 px-2 text-white font-medium">{item.name}</td>
                                                <td className="py-3 px-2 text-white/50 font-mono text-xs">{item.sku}</td>
                                                <td className="py-3 px-2 text-white/50">{item.warehouse}</td>
                                                <td className="py-3 px-2 text-right text-white">{item.quantity}</td>
                                                <td className="py-3 px-2 text-right text-white/40">{item.min_stock}</td>
                                                <td className="py-3 px-2 text-right text-white">${(item.quantity * item.unit_cost).toLocaleString()}</td>
                                                <td className="py-3 px-2 text-center">
                                                    <Badge className={isLow ? "bg-rose-500/20 text-rose-400" : "bg-emerald-500/20 text-emerald-400"}>
                                                        {isLow ? "Low Stock" : "In Stock"}
                                                    </Badge>
                                                </td>
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Modal */}
            {showModal && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50" onClick={() => setShowModal(false)}>
                    <div className="bg-[#0e1e33] border border-[#1e3a5f] rounded-xl p-6 w-full max-w-md space-y-4" onClick={e => e.stopPropagation()}>
                        <div className="flex items-center justify-between">
                            <h3 className="text-white font-bold text-lg">Add Inventory Item</h3>
                            <button onClick={() => setShowModal(false)}><X className="h-5 w-5 text-white/40" /></button>
                        </div>
                        <div className="space-y-3">
                            <Input placeholder="Item Name *" value={form.name} onChange={e => setForm(p => ({ ...p, name: e.target.value }))} className="bg-white/5 border-white/10 text-white" />
                            <Input placeholder="SKU *" value={form.sku} onChange={e => setForm(p => ({ ...p, sku: e.target.value }))} className="bg-white/5 border-white/10 text-white" />
                            <div className="grid grid-cols-3 gap-3">
                                <div><label className="text-white/50 text-xs">Quantity</label><Input type="number" value={form.quantity} onChange={e => setForm(p => ({ ...p, quantity: e.target.value }))} className="bg-white/5 border-white/10 text-white" /></div>
                                <div><label className="text-white/50 text-xs">Min Stock</label><Input type="number" value={form.min_stock} onChange={e => setForm(p => ({ ...p, min_stock: e.target.value }))} className="bg-white/5 border-white/10 text-white" /></div>
                                <div><label className="text-white/50 text-xs">Unit Cost ($)</label><Input type="number" value={form.unit_cost} onChange={e => setForm(p => ({ ...p, unit_cost: e.target.value }))} className="bg-white/5 border-white/10 text-white" /></div>
                            </div>
                            <Input placeholder="Warehouse" value={form.warehouse} onChange={e => setForm(p => ({ ...p, warehouse: e.target.value }))} className="bg-white/5 border-white/10 text-white" />
                            <Input placeholder="Category" value={form.category} onChange={e => setForm(p => ({ ...p, category: e.target.value }))} className="bg-white/5 border-white/10 text-white" />
                        </div>
                        <Button onClick={handleCreate} disabled={saving || !form.name || !form.sku} className="w-full bg-[#f5a623] text-black hover:bg-[#e09000]">
                            {saving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Plus className="h-4 w-4 mr-2" />} Add Item
                        </Button>
                    </div>
                </div>
            )}
        </div>
    );
}
