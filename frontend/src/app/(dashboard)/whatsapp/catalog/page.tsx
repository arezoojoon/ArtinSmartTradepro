"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ShoppingBag, Plus, Search, X, Loader2, DollarSign, Image, Send, Tag, Package } from "lucide-react";
import api from "@/lib/api";

interface Product {
    id: string;
    name: string;
    description: string;
    price: number;
    currency: string;
    category: string;
    sku: string;
    in_stock: boolean;
    image_url?: string;
}

export default function CatalogPage() {
    const [products, setProducts] = useState<Product[]>([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState("");
    const [showModal, setShowModal] = useState(false);
    const [form, setForm] = useState({ name: "", description: "", price: "", currency: "USD", category: "General", sku: "" });
    const [saving, setSaving] = useState(false);

    const fetchProducts = async () => {
        try {
            const res = await api.get("/whatsapp/catalog/products");
            setProducts(Array.isArray(res.data) ? res.data : []);
        } catch { setProducts([]); }
        finally { setLoading(false); }
    };

    useEffect(() => { fetchProducts(); }, []);

    const handleCreate = async () => {
        if (!form.name || !form.price) return;
        setSaving(true);
        try {
            await api.post("/whatsapp/catalog/products", {
                name: form.name, description: form.description,
                price: parseFloat(form.price), currency: form.currency,
                category: form.category, sku: form.sku || undefined,
            });
            setShowModal(false);
            setForm({ name: "", description: "", price: "", currency: "USD", category: "General", sku: "" });
            fetchProducts();
        } catch (e) { console.error("Failed to add product", e); }
        finally { setSaving(false); }
    };

    const handleShare = async (product: Product) => {
        try {
            await api.post("/whatsapp/catalog/share", { product_id: product.id });
        } catch (e) { console.error("Share failed", e); }
    };

    const filtered = products.filter(p =>
        p.name?.toLowerCase().includes(search.toLowerCase()) ||
        p.category?.toLowerCase().includes(search.toLowerCase())
    );

    return (
        <div className="space-y-6 p-4 md:p-8 max-w-[1400px] mx-auto">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold flex items-center gap-2 text-white">
                        <ShoppingBag className="h-6 w-6 text-[#f5a623]" /> Product Catalog
                    </h1>
                    <p className="text-white/50 text-sm">Manage and share products via WhatsApp</p>
                </div>
                <Button onClick={() => setShowModal(true)} className="bg-[#f5a623] text-black hover:bg-[#e09000]">
                    <Plus className="h-4 w-4 mr-2" /> Add Product
                </Button>
            </div>

            {/* Stats */}
            <div className="grid gap-4 sm:grid-cols-3">
                <Card className="bg-[#0e1e33] border-[#1e3a5f]">
                    <CardContent className="p-4 flex items-center justify-between">
                        <div><p className="text-white/50 text-xs uppercase">Total Products</p><p className="text-xl font-bold text-white mt-1">{products.length}</p></div>
                        <Package className="h-7 w-7 text-blue-400/40" />
                    </CardContent>
                </Card>
                <Card className="bg-[#0e1e33] border-[#1e3a5f]">
                    <CardContent className="p-4 flex items-center justify-between">
                        <div><p className="text-white/50 text-xs uppercase">In Stock</p><p className="text-xl font-bold text-emerald-400 mt-1">{products.filter(p => p.in_stock).length}</p></div>
                        <Tag className="h-7 w-7 text-emerald-400/40" />
                    </CardContent>
                </Card>
                <Card className="bg-[#0e1e33] border-[#1e3a5f]">
                    <CardContent className="p-4 flex items-center justify-between">
                        <div><p className="text-white/50 text-xs uppercase">Categories</p><p className="text-xl font-bold text-[#f5a623] mt-1">{new Set(products.map(p => p.category)).size}</p></div>
                        <ShoppingBag className="h-7 w-7 text-[#f5a623]/40" />
                    </CardContent>
                </Card>
            </div>

            {/* Search */}
            <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-white/30" />
                <Input placeholder="Search products..." value={search} onChange={e => setSearch(e.target.value)} className="pl-10 bg-[#0e1e33] border-[#1e3a5f] text-white" />
            </div>

            {/* Product Grid */}
            {loading ? (
                <div className="flex justify-center py-16"><Loader2 className="h-6 w-6 animate-spin text-white/40" /></div>
            ) : filtered.length === 0 ? (
                <Card className="bg-[#0e1e33] border-[#1e3a5f]">
                    <CardContent className="py-16 text-center">
                        <ShoppingBag className="h-12 w-12 mx-auto mb-3 text-white/10" />
                        <p className="text-white/40 text-sm">{products.length === 0 ? "No products yet" : "No products match your search"}</p>
                        {products.length === 0 && <Button onClick={() => setShowModal(true)} variant="link" className="text-[#f5a623] mt-2">Add your first product</Button>}
                    </CardContent>
                </Card>
            ) : (
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                    {filtered.map(product => (
                        <Card key={product.id} className="bg-[#0e1e33] border-[#1e3a5f] hover:border-[#f5a623]/30 transition-colors">
                            <CardContent className="p-4 space-y-3">
                                <div className="h-32 bg-white/5 rounded-lg flex items-center justify-center">
                                    {product.image_url ? <img src={product.image_url} alt={product.name} className="h-full object-contain rounded-lg" />
                                        : <Image className="h-10 w-10 text-white/10" />}
                                </div>
                                <div>
                                    <div className="flex items-start justify-between">
                                        <h3 className="text-white font-semibold text-sm">{product.name}</h3>
                                        <Badge className={product.in_stock ? "bg-emerald-500/20 text-emerald-400 text-[10px]" : "bg-rose-500/20 text-rose-400 text-[10px]"}>
                                            {product.in_stock ? "In Stock" : "Out of Stock"}
                                        </Badge>
                                    </div>
                                    <p className="text-white/40 text-xs mt-1 line-clamp-2">{product.description}</p>
                                    <div className="flex items-center justify-between mt-3">
                                        <span className="text-[#f5a623] font-bold">${product.price?.toLocaleString()} <span className="text-xs text-white/30">{product.currency}</span></span>
                                        <Button size="sm" variant="ghost" onClick={() => handleShare(product)} className="text-green-400 hover:text-green-300 text-xs">
                                            <Send className="h-3 w-3 mr-1" /> Share
                                        </Button>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            )}

            {/* Modal */}
            {showModal && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50" onClick={() => setShowModal(false)}>
                    <div className="bg-[#0e1e33] border border-[#1e3a5f] rounded-xl p-6 w-full max-w-md space-y-4" onClick={e => e.stopPropagation()}>
                        <div className="flex items-center justify-between">
                            <h3 className="text-white font-bold text-lg">Add Product</h3>
                            <button onClick={() => setShowModal(false)}><X className="h-5 w-5 text-white/40" /></button>
                        </div>
                        <div className="space-y-3">
                            <Input placeholder="Product Name *" value={form.name} onChange={e => setForm(p => ({ ...p, name: e.target.value }))} className="bg-white/5 border-white/10 text-white" />
                            <Input placeholder="Description" value={form.description} onChange={e => setForm(p => ({ ...p, description: e.target.value }))} className="bg-white/5 border-white/10 text-white" />
                            <div className="grid grid-cols-2 gap-3">
                                <Input placeholder="Price *" type="number" value={form.price} onChange={e => setForm(p => ({ ...p, price: e.target.value }))} className="bg-white/5 border-white/10 text-white" />
                                <Input placeholder="SKU" value={form.sku} onChange={e => setForm(p => ({ ...p, sku: e.target.value }))} className="bg-white/5 border-white/10 text-white" />
                            </div>
                            <Input placeholder="Category" value={form.category} onChange={e => setForm(p => ({ ...p, category: e.target.value }))} className="bg-white/5 border-white/10 text-white" />
                        </div>
                        <Button onClick={handleCreate} disabled={saving || !form.name || !form.price} className="w-full bg-[#f5a623] text-black hover:bg-[#e09000]">
                            {saving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Plus className="h-4 w-4 mr-2" />} Add Product
                        </Button>
                    </div>
                </div>
            )}
        </div>
    );
}
