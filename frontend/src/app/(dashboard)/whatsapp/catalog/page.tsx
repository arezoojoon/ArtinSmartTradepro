"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
    Package, Plus, Image, FileText, Trash2, DollarSign
} from "lucide-react";

export default function CatalogPage() {
    const [products, setProducts] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [showAdd, setShowAdd] = useState(false);
    const [newProduct, setNewProduct] = useState({
        name: "", sku: "", price: "", currency: "USD", category: "", description: ""
    });

    useEffect(() => {
        api.get("/api/v1/sourcing/products")
            .then(res => setProducts(Array.isArray(res.data) ? res.data : []))
            .catch(() => setProducts([]))
            .finally(() => setLoading(false));
    }, []);

    const handleAdd = async () => {
        try {
            await api.post("/api/v1/sourcing/products", newProduct);
            setShowAdd(false);
            setNewProduct({ name: "", sku: "", price: "", currency: "USD", category: "", description: "" });
            const res = await api.get("/api/v1/sourcing/products");
            setProducts(Array.isArray(res.data) ? res.data : []);
        } catch { }
    };

    return (
        <div className="p-8 bg-black min-h-screen text-white">
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-3xl font-bold flex items-center gap-2">
                        <Package className="h-8 w-8 text-purple-400" />
                        Product Catalog
                    </h1>
                    <p className="text-gray-400">Manage products shown to WhatsApp bot users</p>
                </div>
                <Button onClick={() => setShowAdd(!showAdd)} className="bg-purple-600 hover:bg-purple-500">
                    <Plus className="h-4 w-4 mr-2" />
                    Add Product
                </Button>
            </div>

            {showAdd && (
                <Card className="bg-navy-900 border-navy-800 mb-6">
                    <CardContent className="pt-6">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <Input placeholder="Product Name *" value={newProduct.name}
                                className="bg-navy-950 border-navy-700"
                                onChange={e => setNewProduct({ ...newProduct, name: e.target.value })} />
                            <Input placeholder="SKU" value={newProduct.sku}
                                className="bg-navy-950 border-navy-700"
                                onChange={e => setNewProduct({ ...newProduct, sku: e.target.value })} />
                            <Input placeholder="Category" value={newProduct.category}
                                className="bg-navy-950 border-navy-700"
                                onChange={e => setNewProduct({ ...newProduct, category: e.target.value })} />
                            <Input placeholder="Price" type="number" value={newProduct.price}
                                className="bg-navy-950 border-navy-700"
                                onChange={e => setNewProduct({ ...newProduct, price: e.target.value })} />
                            <Input placeholder="Currency" value={newProduct.currency}
                                className="bg-navy-950 border-navy-700"
                                onChange={e => setNewProduct({ ...newProduct, currency: e.target.value })} />
                            <Input placeholder="Description" value={newProduct.description}
                                className="bg-navy-950 border-navy-700"
                                onChange={e => setNewProduct({ ...newProduct, description: e.target.value })} />
                        </div>
                        <div className="flex justify-end mt-4">
                            <Button onClick={handleAdd} disabled={!newProduct.name}
                                className="bg-emerald-600 hover:bg-emerald-500">
                                Save Product
                            </Button>
                        </div>
                    </CardContent>
                </Card>
            )}

            {loading ? (
                <p className="text-gray-500">Loading...</p>
            ) : products.length === 0 ? (
                <Card className="bg-navy-900 border-navy-800">
                    <CardContent className="py-16 text-center">
                        <Package className="h-16 w-16 mx-auto mb-4 text-gray-700" />
                        <p className="text-gray-500">No products yet. Add your first product above.</p>
                    </CardContent>
                </Card>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {products.map((p: any) => (
                        <Card key={p.id} className="bg-navy-900 border-navy-800 hover:border-purple-800 transition">
                            <CardHeader className="pb-2">
                                <div className="flex justify-between items-start">
                                    <CardTitle className="text-white text-base">{p.name}</CardTitle>
                                    <Badge className="bg-purple-900/60 text-purple-300">{p.category || "General"}</Badge>
                                </div>
                            </CardHeader>
                            <CardContent>
                                <p className="text-sm text-gray-400 mb-3">{p.description || "No description"}</p>
                                <div className="flex justify-between items-center">
                                    <span className="text-lg font-bold text-emerald-400 flex items-center gap-1">
                                        <DollarSign className="h-4 w-4" />
                                        {p.price || "N/A"} {p.currency}
                                    </span>
                                    <span className="text-xs text-gray-500">SKU: {p.sku || "—"}</span>
                                </div>
                                <div className="flex gap-2 mt-3">
                                    <Badge variant="outline" className="text-xs text-gray-400">
                                        Stock: {p.stock_quantity || 0}
                                    </Badge>
                                </div>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            )}
        </div>
    );
}
