"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Package, Plus, ClipboardList, TrendingUp } from "lucide-react";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";

export default function RFQPage() {
    const [rfqs, setRfqs] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [open, setOpen] = useState(false);

    // New RFQ State
    const [newRFQ, setNewRFQ] = useState({
        product_name: "",
        target_qty: "",
        hs_code: ""
    });

    const fetchRfqs = async () => {
        try {
            const res = await api.get("/sourcing/rfqs");
            setRfqs(res.data);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchRfqs();
    }, []);

    const createRFQ = async () => {
        try {
            await api.post("/sourcing/rfqs", {
                ...newRFQ,
                target_qty: parseFloat(newRFQ.target_qty)
            });
            setOpen(false);
            setNewRFQ({ product_name: "", target_qty: "", hs_code: "" });
            fetchRfqs();
        } catch (e) {
            alert("Failed to create RFQ");
        }
    };

    return (
        <div className="p-8 space-y-8 min-h-screen text-white">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-white flex items-center gap-2">
                        <Package className="h-8 w-8 text-gold-500" />
                        Sourcing OS
                    </h1>
                    <p className="text-gray-400">Manage RFQs, Evaluate Suppliers, Execute Trades</p>
                </div>

                <Dialog open={open} onOpenChange={setOpen}>
                    <DialogTrigger asChild>
                        <Button className="bg-gold-500 text-black hover:bg-[#f5a623]">
                            <Plus className="h-4 w-4 mr-2" /> New RFQ
                        </Button>
                    </DialogTrigger>
                    <DialogContent className="bg-[#0e1e33] border-[#1e3a5f] text-white">
                        <DialogHeader>
                            <DialogTitle>Create Request For Quote</DialogTitle>
                        </DialogHeader>
                        <div className="space-y-4 py-4">
                            <Input
                                placeholder="Product Name (e.g. Ceramic Tiles)"
                                className="bg-navy-950 border-navy-700"
                                value={newRFQ.product_name}
                                onChange={(e) => setNewRFQ({ ...newRFQ, product_name: e.target.value })}
                            />
                            <Input
                                placeholder="HS Code (Optional)"
                                className="bg-navy-950 border-navy-700"
                                value={newRFQ.hs_code}
                                onChange={(e) => setNewRFQ({ ...newRFQ, hs_code: e.target.value })}
                            />
                            <Input
                                placeholder="Target Quantity"
                                type="number"
                                className="bg-navy-950 border-navy-700"
                                value={newRFQ.target_qty}
                                onChange={(e) => setNewRFQ({ ...newRFQ, target_qty: e.target.value })}
                            />
                            <Button onClick={createRFQ} className="w-full bg-gold-500 text-black">
                                Launch RFQ
                            </Button>
                        </div>
                    </DialogContent>
                </Dialog>
            </div>

            <div className="grid grid-cols-1 gap-6">
                <Card className="bg-[#0e1e33] border-[#1e3a5f]">
                    <CardHeader>
                        <CardTitle className="text-white">Active Requests</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <Table>
                            <TableHeader>
                                <TableRow className="border-navy-700 hover:bg-navy-800">
                                    <TableHead className="text-gray-400">Product</TableHead>
                                    <TableHead className="text-gray-400">HS Code</TableHead>
                                    <TableHead className="text-gray-400">Qty</TableHead>
                                    <TableHead className="text-gray-400">Status</TableHead>
                                    <TableHead className="text-gray-400 text-right">Actions</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {rfqs.length === 0 ? (
                                    <TableRow>
                                        <TableCell colSpan={5} className="text-center py-8 text-gray-500">
                                            No active RFQs. Start sourcing now.
                                        </TableCell>
                                    </TableRow>
                                ) : (
                                    rfqs.map((rfq) => (
                                        <TableRow key={rfq.id} className="border-navy-700 hover:bg-navy-800">
                                            <TableCell className="font-medium text-white">{rfq.product_name}</TableCell>
                                            <TableCell className="text-gray-400">{rfq.hs_code || "-"}</TableCell>
                                            <TableCell>{rfq.target_qty}</TableCell>
                                            <TableCell>
                                                <Badge variant="outline" className="border-gold-500 text-gold-500">
                                                    {rfq.status}
                                                </Badge>
                                            </TableCell>
                                            <TableCell className="text-right">
                                                <Button size="sm" variant="outline" className="mr-2 text-white border-gray-600 hover:bg-navy-800">
                                                    <ClipboardList className="h-4 w-4 mr-1" /> Compare Quotes
                                                </Button>
                                            </TableCell>
                                        </TableRow>
                                    ))
                                )}
                            </TableBody>
                        </Table>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
