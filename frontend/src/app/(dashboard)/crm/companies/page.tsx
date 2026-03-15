"use client";

import { useState, useEffect } from "react";
import {
    Plus, Search, Filter, MoreHorizontal, Building2, MapPin,
    Globe, Linkedin, Tag, TrendingUp, ShieldCheck,
    ExternalLink, ArrowUpRight, X
} from "lucide-react";
import api from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
    Table, TableBody, TableCell, TableHead, TableHeader, TableRow
} from "@/components/ui/table";
import {
    DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger
} from "@/components/ui/dropdown-menu";
import { Progress } from "@/components/ui/progress";

export default function CompaniesPage() {
    const [companies, setCompanies] = useState([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState("");
    const [showAdd, setShowAdd] = useState(false);
    const [saving, setSaving] = useState(false);
    const [addForm, setAddForm] = useState({ name: "", website: "", industry: "", country: "", city: "", address: "", linkedin_url: "" });

    useEffect(() => {
        fetchCompanies();
    }, [search]);

    const fetchCompanies = async () => {
        setLoading(true);
        try {
            const query = search ? `?search=${search}` : "";
            const { data } = await api.get(`/crm/companies${query}`);
            setCompanies(data.companies || data);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleAddCompany = async () => {
        if (!addForm.name.trim()) return;
        setSaving(true);
        try {
            await api.post("/crm/companies", addForm);
            setShowAdd(false);
            setAddForm({ name: "", website: "", industry: "", country: "", city: "", address: "", linkedin_url: "" });
            fetchCompanies();
        } catch (e) { console.error("Failed to create company:", e); }
        finally { setSaving(false); }
    };

    const getRiskLabel = (score: number) => {
        if (score <= 30) return "Low Risk";
        if (score <= 60) return "Moderate";
        return "High Risk";
    };

    return (
        <div className="max-w-7xl mx-auto space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-white">Companies</h1>
                    <p className="text-slate-400 mt-1">Manage global trade partners and enterprise accounts.</p>
                </div>
                <div className="flex items-center gap-3">
                    <Button variant="outline" className="hidden sm:flex border-white/10">
                        <ArrowUpRight className="h-4 w-4 mr-2" />
                        Export Data
                    </Button>
                    <Button onClick={() => setShowAdd(true)} className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold">
                        <Plus className="h-4 w-4 mr-2" />
                        Add Company
                    </Button>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card className="shadow-sm border-white/10 bg-white/5">
                    <CardContent className="p-4 flex items-center gap-4">
                        <div className="p-2 bg-indigo-500/10 rounded-lg"><Building2 className="h-5 w-5 text-indigo-400" /></div>
                        <div>
                            <p className="text-sm font-medium text-slate-400">Total Partners</p>
                            <p className="text-2xl font-bold text-white">{loading ? "..." : companies.length}</p>
                        </div>
                    </CardContent>
                </Card>
                <Card className="shadow-sm border-white/10 bg-white/5">
                    <CardContent className="p-4 flex items-center gap-4">
                        <div className="p-2 bg-emerald-500/10 rounded-lg"><ShieldCheck className="h-5 w-5 text-emerald-400" /></div>
                        <div>
                            <p className="text-sm font-medium text-slate-400">With Website</p>
                            <p className="text-2xl font-bold text-white">{companies.filter((c: any) => c.website).length}</p>
                        </div>
                    </CardContent>
                </Card>
                <Card className="shadow-sm border-white/10 bg-white/5">
                    <CardContent className="p-4 flex items-center gap-4">
                        <div className="p-2 bg-amber-500/10 rounded-lg"><TrendingUp className="h-5 w-5 text-amber-400" /></div>
                        <div>
                            <p className="text-sm font-medium text-slate-400">With LinkedIn</p>
                            <p className="text-2xl font-bold text-white">{companies.filter((c: any) => c.linkedin_url).length}</p>
                        </div>
                    </CardContent>
                </Card>
            </div>

            <div className="flex flex-col sm:flex-row gap-4 items-center justify-between bg-white/5 p-4 rounded-xl border border-white/10">
                <div className="relative w-full sm:max-w-md">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                    <Input placeholder="Search by name, industry, or domain..." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-10 bg-white/5 border-white/10" />
                </div>
            </div>

            <Card className="shadow-sm border-white/10 overflow-hidden bg-white/5">
                <Table>
                    <TableHeader className="bg-white/5">
                        <TableRow>
                            <TableHead className="w-[300px] font-bold text-slate-300">Company & Domain</TableHead>
                            <TableHead className="font-bold text-slate-300">Industry & Size</TableHead>
                            <TableHead className="font-bold text-slate-300">Location</TableHead>
                            <TableHead className="font-bold text-slate-300">Risk Radar</TableHead>
                            <TableHead className="text-right font-bold text-slate-300">Actions</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {loading ? (
                            Array.from({ length: 3 }).map((_, i) => (
                                <TableRow key={i}><TableCell colSpan={5} className="h-16 animate-pulse bg-white/5" /></TableRow>
                            ))
                        ) : companies.length === 0 ? (
                            <TableRow>
                                <TableCell colSpan={5} className="h-64 text-center">
                                    <div className="flex flex-col items-center justify-center text-slate-400">
                                        <Building2 className="h-12 w-12 mb-4 opacity-20" />
                                        <p className="text-lg font-medium">No partners found</p>
                                        <p className="text-sm mb-4">Add your first company partner</p>
                                        <Button onClick={() => setShowAdd(true)} className="bg-indigo-600 hover:bg-indigo-700 text-white">
                                            <Plus className="h-4 w-4 mr-2" /> Add Company
                                        </Button>
                                    </div>
                                </TableCell>
                            </TableRow>
                        ) : (
                            companies.map((company: any) => (
                                <TableRow key={company.id} className="hover:bg-white/5 transition-colors group">
                                    <TableCell>
                                        <div className="flex items-center gap-3">
                                            <div className="h-10 w-10 rounded-xl bg-indigo-500/10 flex items-center justify-center border border-indigo-500/20">
                                                <Building2 className="h-5 w-5 text-indigo-400" />
                                            </div>
                                            <div>
                                                <div className="font-bold text-white">{company.name}</div>
                                                <div className="text-xs text-slate-500 font-mono flex items-center gap-1">
                                                    {company.domain || company.website?.replace(/https?:\/\//, '')}
                                                    {company.website && <ExternalLink className="h-2 w-2 opacity-0 group-hover:opacity-100 transition-opacity" />}
                                                </div>
                                            </div>
                                        </div>
                                    </TableCell>
                                    <TableCell>
                                        <div className="space-y-1">
                                            <div className="text-sm font-medium text-slate-200">{company.industry || "General Trade"}</div>
                                            <Badge variant="outline" className="text-[10px] font-bold uppercase bg-white/10 text-slate-400 border-white/10">{company.size || "SME"}</Badge>
                                        </div>
                                    </TableCell>
                                    <TableCell>
                                        <div className="flex flex-col">
                                            <div className="flex items-center gap-1.5 text-sm font-medium text-slate-200">
                                                <MapPin className="h-3 w-3 text-rose-500" />{company.country || "Global"}
                                            </div>
                                            <div className="text-xs text-slate-500 ml-5">{company.city || ""}</div>
                                        </div>
                                    </TableCell>
                                    <TableCell>
                                        <div className="w-32 space-y-1.5">
                                            <div className="flex justify-between text-[10px] font-bold uppercase">
                                                <span className="text-slate-500">{getRiskLabel(company.risk_score || 20)}</span>
                                                <span className="text-slate-300">{(company.risk_score || 20).toFixed(0)}%</span>
                                            </div>
                                            <Progress value={company.risk_score || 20} className="h-1.5" />
                                        </div>
                                    </TableCell>
                                    <TableCell className="text-right">
                                        <DropdownMenu>
                                            <DropdownMenuTrigger asChild>
                                                <Button variant="ghost" size="icon" className="h-8 w-8 hover:bg-white/10"><MoreHorizontal className="h-4 w-4" /></Button>
                                            </DropdownMenuTrigger>
                                            <DropdownMenuContent align="end">
                                                <DropdownMenuItem>Edit Company</DropdownMenuItem>
                                                <DropdownMenuItem className="text-rose-600" onClick={async () => { if (confirm(`Delete ${company.name}?`)) { try { await api.delete(`/crm/companies/${company.id}`); fetchCompanies(); } catch (e) { console.error(e); } } }}>Delete</DropdownMenuItem>
                                            </DropdownMenuContent>
                                        </DropdownMenu>
                                    </TableCell>
                                </TableRow>
                            ))
                        )}
                    </TableBody>
                </Table>
            </Card>

            {/* Add Company Modal */}
            {showAdd && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={() => setShowAdd(false)}>
                    <div className="bg-[#0F172A] border border-white/10 rounded-2xl p-6 w-full max-w-md space-y-4" onClick={e => e.stopPropagation()}>
                        <div className="flex items-center justify-between">
                            <h3 className="text-white font-bold text-lg">Add Company</h3>
                            <button onClick={() => setShowAdd(false)} className="p-1 hover:bg-white/10 rounded-lg"><X className="h-5 w-5 text-slate-400" /></button>
                        </div>
                        <Input placeholder="Company Name *" value={addForm.name} onChange={e => setAddForm(p => ({ ...p, name: e.target.value }))} className="bg-white/5 border-white/10" />
                        <Input placeholder="Website (https://...)" value={addForm.website} onChange={e => setAddForm(p => ({ ...p, website: e.target.value }))} className="bg-white/5 border-white/10" />
                        <div className="grid grid-cols-2 gap-3">
                            <Input placeholder="Industry" value={addForm.industry} onChange={e => setAddForm(p => ({ ...p, industry: e.target.value }))} className="bg-white/5 border-white/10" />
                            <Input placeholder="Country" value={addForm.country} onChange={e => setAddForm(p => ({ ...p, country: e.target.value }))} className="bg-white/5 border-white/10" />
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                            <Input placeholder="City" value={addForm.city} onChange={e => setAddForm(p => ({ ...p, city: e.target.value }))} className="bg-white/5 border-white/10" />
                            <Input placeholder="Address" value={addForm.address} onChange={e => setAddForm(p => ({ ...p, address: e.target.value }))} className="bg-white/5 border-white/10" />
                        </div>
                        <Input placeholder="LinkedIn URL" value={addForm.linkedin_url} onChange={e => setAddForm(p => ({ ...p, linkedin_url: e.target.value }))} className="bg-white/5 border-white/10" />
                        <Button onClick={handleAddCompany} disabled={saving || !addForm.name.trim()} className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-semibold">
                            {saving ? "Creating..." : "Create Company"}
                        </Button>
                    </div>
                </div>
            )}
        </div>
    );
}
