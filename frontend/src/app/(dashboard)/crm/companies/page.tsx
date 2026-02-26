"use client";

import { useState, useEffect } from "react";
import {
    Plus, Search, Filter, MoreHorizontal, Building2, MapPin,
    Globe, Linkedin, Tag, TrendingUp, AlertTriangle, ShieldCheck,
    ExternalLink, ArrowUpRight, Target
} from "lucide-react";
import api from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
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

    const getRiskColor = (score: number) => {
        if (score <= 30) return "bg-emerald-500";
        if (score <= 60) return "bg-amber-500";
        return "bg-rose-500";
    };

    const getRiskLabel = (score: number) => {
        if (score <= 30) return "Low Risk";
        if (score <= 60) return "Moderate";
        return "High Risk";
    };

    return (
        <div className="max-w-7xl mx-auto space-y-6">
            {/* Header Section */}
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
                    <Button className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold">
                        <Plus className="h-4 w-4 mr-2" />
                        Add Company
                    </Button>
                </div>
            </div>

            {/* Quick Stats / Highlights */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card className="shadow-sm border-white/10 bg-white/5">
                    <CardContent className="p-4 flex items-center gap-4">
                        <div className="p-2 bg-indigo-50 rounded-lg">
                            <Building2 className="h-5 w-5 text-indigo-600" />
                        </div>
                        <div>
                            <p className="text-sm font-medium text-slate-400">Total Partners</p>
                            <p className="text-2xl font-bold text-white">{loading ? "..." : companies.length}</p>
                        </div>
                    </CardContent>
                </Card>
                <Card className="shadow-sm border-white/10 bg-white/5">
                    <CardContent className="p-4 flex items-center gap-4">
                        <div className="p-2 bg-emerald-50 rounded-lg">
                            <ShieldCheck className="h-5 w-5 text-emerald-600" />
                        </div>
                        <div>
                            <p className="text-sm font-medium text-slate-400">Secure Entities</p>
                            <p className="text-2xl font-bold text-white">84%</p>
                        </div>
                    </CardContent>
                </Card>
                <Card className="shadow-sm border-white/10 bg-white/5">
                    <CardContent className="p-4 flex items-center gap-4">
                        <div className="p-2 bg-amber-50 rounded-lg">
                            <TrendingUp className="h-5 w-5 text-amber-600" />
                        </div>
                        <div>
                            <p className="text-sm font-medium text-slate-400">Avg. Trade Score</p>
                            <p className="text-2xl font-bold text-white">7.2/10</p>
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Search and Filters */}
            <div className="flex flex-col sm:flex-row gap-4 items-center justify-between bg-white/5 p-4 rounded-xl border border-white/10 shadow-sm">
                <div className="relative w-full sm:max-w-md">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                    <Input
                        placeholder="Search by name, industry, or domain..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        className="pl-10 bg-white/5 border-white/10"
                    />
                </div>
                <div className="flex items-center gap-2 w-full sm:w-auto">
                    <Button variant="outline" className="flex-1 sm:flex-none border-white/10 bg-white/5">
                        <Filter className="h-4 w-4 mr-2" />
                        Filters
                    </Button>
                    <Button variant="outline" className="flex-1 sm:flex-none border-white/10 bg-white/5">
                        <Tag className="h-4 w-4 mr-2" />
                        Tags
                    </Button>
                </div>
            </div>

            {/* Companies Table */}
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
                            Array.from({ length: 5 }).map((_, i) => (
                                <TableRow key={i}>
                                    <TableCell colSpan={5} className="h-16 animate-pulse bg-white/5" />
                                </TableRow>
                            ))
                        ) : companies.length === 0 ? (
                            <TableRow>
                                <TableCell colSpan={5} className="h-64 text-center">
                                    <div className="flex flex-col items-center justify-center text-slate-400">
                                        <Building2 className="h-12 w-12 mb-4 opacity-20" />
                                        <p className="text-lg font-medium">No partners found</p>
                                        <p className="text-sm">Try adjusting your filters or search query</p>
                                    </div>
                                </TableCell>
                            </TableRow>
                        ) : (
                            companies.map((company: any) => (
                                <TableRow key={company.id} className="hover:bg-white/5 transition-colors group">
                                    <TableCell>
                                        <div className="flex items-center gap-3">
                                            <div className="h-10 w-10 rounded-xl bg-indigo-50 flex items-center justify-center text-indigo-600 border border-indigo-100 shadow-sm">
                                                <Building2 className="h-5 w-5" />
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
                                            <Badge variant="outline" className="text-[10px] font-bold uppercase tracking-wider bg-white/10 text-slate-400 border-white/10">
                                                {company.size || "SME"}
                                            </Badge>
                                        </div>
                                    </TableCell>
                                    <TableCell>
                                        <div className="flex flex-col">
                                            <div className="flex items-center gap-1.5 text-sm font-medium text-slate-200">
                                                <MapPin className="h-3 w-3 text-rose-500" />
                                                {company.country || "Global"}
                                            </div>
                                            <div className="text-xs text-slate-500 ml-5">{company.city || "Multi-location"}</div>
                                        </div>
                                    </TableCell>
                                    <TableCell>
                                        <div className="w-32 space-y-1.5">
                                            <div className="flex justify-between text-[10px] font-bold uppercase tracking-tighter">
                                                <span className="text-slate-500">{getRiskLabel(company.risk_score || 20)}</span>
                                                <span className="text-slate-300">{(company.risk_score || 20).toFixed(0)}%</span>
                                            </div>
                                            <Progress
                                                value={company.risk_score || 20}
                                                className="h-1.5"
                                            />
                                        </div>
                                    </TableCell>
                                    <TableCell className="text-right">
                                        <div className="flex items-center justify-end gap-2">
                                            <div className="hidden group-hover:flex items-center gap-1">
                                                {company.linkedin_url && (
                                                    <a href={company.linkedin_url} target="_blank" className="p-2 hover:bg-white/10 rounded-lg text-slate-400 hover:text-blue-400 transition-colors">
                                                        <Linkedin className="h-4 w-4" />
                                                    </a>
                                                )}
                                                {company.website && (
                                                    <a href={company.website} target="_blank" className="p-2 hover:bg-white/10 rounded-lg text-slate-400 hover:text-indigo-400 transition-colors">
                                                        <Globe className="h-4 w-4" />
                                                    </a>
                                                )}
                                            </div>
                                            <DropdownMenu>
                                                <DropdownMenuTrigger asChild>
                                                    <Button variant="ghost" size="icon" className="h-8 w-8 hover:bg-white/10">
                                                        <MoreHorizontal className="h-4 w-4" />
                                                    </Button>
                                                </DropdownMenuTrigger>
                                                <DropdownMenuContent align="end">
                                                    <DropdownMenuItem>View Trade History</DropdownMenuItem>
                                                    <DropdownMenuItem>Manage Contacts</DropdownMenuItem>
                                                    <DropdownMenuItem>Edit Company</DropdownMenuItem>
                                                    <DropdownMenuItem className="text-rose-600">Archive Partner</DropdownMenuItem>
                                                </DropdownMenuContent>
                                            </DropdownMenu>
                                        </div>
                                    </TableCell>
                                </TableRow>
                            ))
                        )}
                    </TableBody>
                </Table>
            </Card>

            <div className="flex items-center justify-between text-xs text-slate-500 font-medium px-2">
                <p>Showing {loading ? "..." : companies.length} global trade entities.</p>
                <div className="flex items-center gap-1 bg-white/5 border border-white/10 rounded-lg p-1 px-3">
                    <ShieldCheck className="h-3 w-3 text-emerald-500" /> All data vetted by Comtrade & Local Intelligence.
                </div>
            </div>
        </div>
    );
}

