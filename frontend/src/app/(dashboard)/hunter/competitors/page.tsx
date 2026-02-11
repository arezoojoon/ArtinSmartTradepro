"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle, TrendingUp, TrendingDown, Search, Plus, Crosshair, BarChart3, RefreshCw } from "lucide-react";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

export default function CompetitorPage() {
    const [competitors, setCompetitors] = useState<any[]>([]);
    const [selectedComp, setSelectedComp] = useState<any>(null);
    const [products, setProducts] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [newCompName, setNewCompName] = useState("");

    // Fetch Competitors
    const fetchCompetitors = async () => {
        try {
            const res = await api.get("/api/hunter/competitors");
            setCompetitors(res.data);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchCompetitors();
    }, []);

    // Add Competitor
    const addCompetitor = async () => {
        if (!newCompName) return;
        await api.post("/api/hunter/competitors", { name: newCompName });
        setNewCompName("");
        fetchCompetitors();
    };

    // Track Competitor (Async Job)
    const trackCompetitor = async (id: string) => {
        await api.post(`/api/hunter/competitors/${id}/track`);
        alert("Tracking job queued. Results will appear shortly.");
        // Optimistic update or polling would go here
    };

    // View Details
    const viewDetails = async (comp: any) => {
        setSelectedComp(comp);
        const res = await api.get(`/api/hunter/competitors/${comp.id}/products`);
        setProducts(res.data);
    };

    return (
        <div className="p-8 space-y-8 bg-black min-h-screen text-white">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-white flex items-center gap-2">
                        <Crosshair className="h-8 w-8 text-gold-500" />
                        Competitor Intelligence
                    </h1>
                    <p className="text-gray-400">Track Rivals, Analyze Prices, Defend Margins</p>
                </div>
                <div className="flex gap-2">
                    <Input
                        placeholder="New Competitor Name..."
                        className="bg-navy-900 border-navy-700 text-white w-64"
                        value={newCompName}
                        onChange={(e) => setNewCompName(e.target.value)}
                    />
                    <Button onClick={addCompetitor} className="bg-gold-500 text-black hover:bg-gold-400">
                        <Plus className="h-4 w-4 mr-2" /> Track Rival
                    </Button>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* COMPETITOR LIST */}
                <Card className="col-span-1 bg-navy-900 border-navy-800">
                    <CardHeader>
                        <CardTitle className="text-white">Watchlist</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {competitors.map((comp) => (
                            <div
                                key={comp.id}
                                onClick={() => viewDetails(comp)}
                                className={`p-4 rounded-lg border cursor-pointer transition-all ${selectedComp?.id === comp.id
                                        ? "bg-navy-800 border-gold-500"
                                        : "bg-navy-950 border-navy-800 hover:border-gray-600"
                                    }`}
                            >
                                <div className="flex justify-between items-start">
                                    <div>
                                        <h3 className="font-bold text-lg">{comp.name}</h3>
                                        <div className="flex gap-2 mt-1">
                                            <Badge variant="outline" className="border-gray-600 text-xs">
                                                {comp.country || "Global"}
                                            </Badge>
                                            <Badge className={`${comp.threat_level === 'high' ? 'bg-red-900 text-red-100' :
                                                    comp.threat_level === 'medium' ? 'bg-yellow-900 text-yellow-100' :
                                                        'bg-green-900 text-green-100'
                                                }`}>
                                                {comp.threat_level?.toUpperCase()} THREAT
                                            </Badge>
                                        </div>
                                    </div>
                                    <Button
                                        size="icon"
                                        variant="ghost"
                                        className="h-8 w-8 text-gray-400 hover:text-white"
                                        onClick={(e) => { e.stopPropagation(); trackCompetitor(comp.id); }}
                                    >
                                        <RefreshCw className="h-4 w-4" />
                                    </Button>
                                </div>
                                <div className="mt-3 flex justify-between text-xs text-gray-400">
                                    <span>Market Share: {comp.market_share_est || 0}%</span>
                                    <span>Updated: {new Date(comp.updated_at).toLocaleDateString()}</span>
                                </div>
                            </div>
                        ))}
                    </CardContent>
                </Card>

                {/* DETAILS PANEL */}
                <div className="col-span-1 lg:col-span-2 space-y-6">
                    {selectedComp ? (
                        <>
                            {/* ALERTS BANNER */}
                            <div className="grid grid-cols-3 gap-4">
                                <Card className="bg-red-950/30 border-red-900">
                                    <CardContent className="p-4 flex items-center gap-4">
                                        <AlertTriangle className="h-8 w-8 text-red-500" />
                                        <div>
                                            <div className="text-xl font-bold text-red-500">2</div>
                                            <div className="text-xs text-red-200">Margin Alerts</div>
                                        </div>
                                    </CardContent>
                                </Card>
                                <Card className="bg-navy-900 border-navy-800">
                                    <CardContent className="p-4 flex items-center gap-4">
                                        <TrendingDown className="h-8 w-8 text-green-500" />
                                        <div>
                                            <div className="text-xl font-bold text-green-500">-5%</div>
                                            <div className="text-xs text-gray-400">Avg Price Delta</div>
                                        </div>
                                    </CardContent>
                                </Card>
                                <Card className="bg-navy-900 border-navy-800">
                                    <CardContent className="p-4 flex items-center gap-4">
                                        <BarChart3 className="h-8 w-8 text-blue-500" />
                                        <div>
                                            <div className="text-xl font-bold text-blue-500">12%</div>
                                            <div className="text-xs text-gray-400">Est. Market Share</div>
                                        </div>
                                    </CardContent>
                                </Card>
                            </div>

                            {/* PRODUCT TABLE */}
                            <Card className="bg-navy-900 border-navy-800">
                                <CardHeader className="flex flex-row items-center justify-between">
                                    <CardTitle className="text-white">Product Pricing Analysis</CardTitle>
                                    <Button variant="outline" className="border-gold-500 text-gold-500 hover:bg-gold-500 hover:text-black">
                                        Wait...
                                    </Button>
                                </CardHeader>
                                <CardContent>
                                    <Table>
                                        <TableHeader>
                                            <TableRow className="border-navy-700 hover:bg-navy-800">
                                                <TableHead className="text-gray-400">Product</TableHead>
                                                <TableHead className="text-gray-400">SKU</TableHead>
                                                <TableHead className="text-gray-400">Price</TableHead>
                                                <TableHead className="text-gray-400">Status</TableHead>
                                                <TableHead className="text-gray-400 text-right">Action</TableHead>
                                            </TableRow>
                                        </TableHeader>
                                        <TableBody>
                                            {products.length === 0 ? (
                                                <TableRow>
                                                    <TableCell colSpan={5} className="text-center py-8 text-gray-500">
                                                        No products tracked. Click refresh button to start job.
                                                    </TableCell>
                                                </TableRow>
                                            ) : (
                                                products.map((prod) => (
                                                    <TableRow key={prod.id} className="border-navy-700 hover:bg-navy-800">
                                                        <TableCell className="font-medium">
                                                            {prod.name}
                                                            <a href={prod.product_url} target="_blank" className="block text-xs text-blue-400 hover:underline">
                                                                View Source
                                                            </a>
                                                        </TableCell>
                                                        <TableCell className="text-gray-400">{prod.sku || "-"}</TableCell>
                                                        <TableCell>
                                                            <div className="font-bold text-white">
                                                                {prod.currency} {prod.last_price}
                                                            </div>
                                                            {prod.last_price < 1000 && (
                                                                <span className="text-xs text-red-400 flex items-center">
                                                                    <TrendingDown className="h-3 w-3 mr-1" /> Undercut Risk
                                                                </span>
                                                            )}
                                                        </TableCell>
                                                        <TableCell>
                                                            <Badge variant="outline" className={`
                                                                ${prod.availability_status === 'in_stock' ? 'border-green-500 text-green-500' : 'border-red-500 text-red-500'}
                                                            `}>
                                                                {prod.availability_status}
                                                            </Badge>
                                                        </TableCell>
                                                        <TableCell className="text-right">
                                                            <Button size="sm" className="bg-gold-500 text-black hover:bg-gold-400 h-8">
                                                                Counter
                                                            </Button>
                                                        </TableCell>
                                                    </TableRow>
                                                ))
                                            )}
                                        </TableBody>
                                    </Table>
                                </CardContent>
                            </Card>
                        </>
                    ) : (
                        <div className="h-full flex items-center justify-center text-gray-500 border-2 border-dashed border-navy-800 rounded-lg">
                            Select a competitor to view analysis
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
