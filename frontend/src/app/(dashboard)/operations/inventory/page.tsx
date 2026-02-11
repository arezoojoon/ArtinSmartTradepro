"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Warehouse, CloudRain, AlertTriangle, MapPin, Box } from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export default function OperationsPage() {
    const [warehouses, setWarehouses] = useState<any[]>([]);
    const [risks, setRisks] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [openWH, setOpenWH] = useState(false);

    const [newWH, setNewWH] = useState({ name: "", lat: 0, lon: 0, capacity: 5000 });

    const refreshData = async () => {
        setLoading(true);
        try {
            const [whRes, riskRes] = await Promise.all([
                api.get("/api/v1/operations/inventory/warehouses"),
                api.get("/api/v1/operations/climate/risks")
            ]);
            setWarehouses(whRes.data);
            setRisks(riskRes.data);
        } catch (e) {
            console.error("Failed to load operations data", e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        refreshData();
    }, []);

    const createWarehouse = async () => {
        try {
            await api.post("/api/v1/operations/inventory/warehouses", newWH);
            setOpenWH(false);
            refreshData();
        } catch (e) {
            alert("Failed to create warehouse");
        }
    };

    return (
        <div className="p-8 space-y-8 bg-black min-h-screen text-white">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold flex items-center gap-2">
                        <Warehouse className="h-8 w-8 text-gold-500" />
                        Operations & Inventory
                    </h1>
                    <p className="text-gray-400">Physical Asset Management & Climate Risk</p>
                </div>

                <Dialog open={openWH} onOpenChange={setOpenWH}>
                    <DialogTrigger asChild>
                        <Button className="bg-gold-500 text-black hover:bg-gold-400">
                            <Box className="h-4 w-4 mr-2" /> Add Warehouse
                        </Button>
                    </DialogTrigger>
                    <DialogContent className="bg-navy-900 border-navy-800 text-white">
                        <DialogHeader>
                            <DialogTitle>Add New Warehouse</DialogTitle>
                        </DialogHeader>
                        <div className="space-y-4 py-4">
                            <Input
                                placeholder="Warehouse Name"
                                className="bg-navy-950 border-navy-700"
                                value={newWH.name}
                                onChange={(e) => setNewWH({ ...newWH, name: e.target.value })}
                            />
                            <div className="grid grid-cols-2 gap-4">
                                <Input
                                    placeholder="Latitude"
                                    type="number"
                                    className="bg-navy-950 border-navy-700"
                                    onChange={(e) => setNewWH({ ...newWH, lat: parseFloat(e.target.value) })}
                                />
                                <Input
                                    placeholder="Longitude"
                                    type="number"
                                    className="bg-navy-950 border-navy-700"
                                    onChange={(e) => setNewWH({ ...newWH, lon: parseFloat(e.target.value) })}
                                />
                            </div>
                            <Button onClick={createWarehouse} className="w-full bg-gold-500 text-black">
                                Create Warehouse
                            </Button>
                        </div>
                    </DialogContent>
                </Dialog>
            </div>

            {/* Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">

                {/* Warehouses Section */}
                <div className="space-y-4">
                    <h2 className="text-xl font-semibold flex items-center gap-2">
                        <MapPin className="h-5 w-5 text-blue-400" /> Global Inventory
                    </h2>
                    {loading ? <div>Loading...</div> : (
                        <div className="grid grid-cols-1 gap-4">
                            {warehouses.length === 0 ? (
                                <div className="p-4 border border-dashed border-gray-700 rounded text-gray-500 text-center">
                                    No warehouses Configured.
                                </div>
                            ) : warehouses.map(w => (
                                <Card key={w.id} className="bg-navy-900 border-navy-800">
                                    <CardHeader>
                                        <CardTitle className="flex justify-between items-center text-white">
                                            {w.name}
                                            <Badge variant="outline" className="text-green-400 border-green-900">Active</Badge>
                                        </CardTitle>
                                        <CardDescription>
                                            Capacity: {w.capacity_sqm} sqm • Lat: {w.location_lat}, Lon: {w.location_lon}
                                        </CardDescription>
                                    </CardHeader>
                                </Card>
                            ))}
                        </div>
                    )}
                </div>

                {/* Climate Risk Section */}
                <div className="space-y-4">
                    <h2 className="text-xl font-semibold flex items-center gap-2">
                        <CloudRain className="h-5 w-5 text-red-400" /> Active Climate Risks
                    </h2>
                    {loading ? <div>Loading...</div> : (
                        <div className="grid grid-cols-1 gap-4">
                            {risks.length === 0 ? (
                                <div className="p-4 border border-dashed border-gray-700 rounded text-gray-500 text-center">
                                    No active weather alerts.
                                </div>
                            ) : risks.map(r => (
                                <Card key={r.id} className="bg-navy-900 border-red-900/50">
                                    <CardHeader>
                                        <CardTitle className="flex justify-between items-center text-white">
                                            {r.risk_type}
                                            <Badge variant="destructive" className="uppercase">{r.severity}</Badge>
                                        </CardTitle>
                                        <CardDescription className="text-gray-400">
                                            Region: {r.region}
                                        </CardDescription>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="flex items-center gap-2 text-yellow-500 text-sm">
                                            <AlertTriangle className="h-4 w-4" />
                                            <span>Impacts Trade Lanes through {r.region}</span>
                                        </div>
                                    </CardContent>
                                </Card>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
