"use client"

import { useState, useMemo } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Search, Download, Loader2, TrendingUp, Globe2 } from "lucide-react"
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer,
    AreaChart, Area
} from 'recharts';
import api from "@/lib/api"

interface TradeRecord {
    hs_code: string
    reporter_country: string
    partner_country: string
    trade_flow: string
    year: number
    trade_value_usd: number
    quantity: number
    quantity_unit: string
}

export default function TradeDataPage() {
    const [loading, setLoading] = useState(false)
    const [results, setResults] = useState<TradeRecord[]>([])

    const [hsCode, setHsCode] = useState("")
    const [country, setCountry] = useState("")

    const handleSearch = async () => {
        setLoading(true)
        try {
            const params = new URLSearchParams()
            if (hsCode) params.append("hs_code", hsCode)
            if (country) params.append("country", country)

            const res = await api.get(`/toolbox/trade-data?${params.toString()}`)
            setResults(res.data)
        } catch (error) {
            console.error("Search failed", error)
        } finally {
            setLoading(false)
        }
    }

    // Process data for charts
    const { trendsData, competitorsData } = useMemo(() => {
        if (!results || results.length === 0) return { trendsData: [], competitorsData: [] };

        // 1. Trends Data (Aggregated by Year)
        const years = Array.from(new Set(results.map(r => r.year))).sort();
        const trends = years.map(year => {
            const yearData = results.filter(r => r.year === year);
            const importVal = yearData.filter(r => r.trade_flow === 'import').reduce((sum, r) => sum + r.trade_value_usd, 0);
            const exportVal = yearData.filter(r => r.trade_flow === 'export').reduce((sum, r) => sum + r.trade_value_usd, 0);
            return { year, Import: importVal, Export: exportVal };
        });

        // 2. Competitors Data (Top Exporters)
        const competitorsMap = results
            .filter(r => r.trade_flow === 'export')
            .reduce((acc, r) => {
                acc[r.reporter_country] = (acc[r.reporter_country] || 0) + r.trade_value_usd;
                return acc;
            }, {} as Record<string, number>);

        const competitors = Object.entries(competitorsMap)
            .map(([name, value]) => ({ name, value }))
            .sort((a, b) => b.value - a.value)
            .slice(0, 5);

        return { trendsData: trends, competitorsData: competitors };
    }, [results]);

    const formatCurrency = (val: number) => {
        if (val >= 1e9) return `$${(val / 1e9).toFixed(2)}B`;
        if (val >= 1e6) return `$${(val / 1e6).toFixed(2)}M`;
        if (val >= 1e3) return `$${(val / 1e3).toFixed(2)}K`;
        return `$${val.toFixed(0)}`;
    };

    return (
        <div className="space-y-6 max-w-7xl mx-auto">
            <div className="flex items-center justify-between">
                <h2 className="text-3xl font-bold tracking-tight">Trade Data Hub 🌍</h2>
                <Button variant="outline" onClick={() => window.print()}>
                    <Download className="mr-2 h-4 w-4" /> Export Report
                </Button>
            </div>

            {/* Search Filters */}
            <Card className="bg-white border-slate-200 shadow-sm">
                <CardHeader className="pb-4">
                    <CardTitle className="text-lg">HS Finder & Global Database</CardTitle>
                    <CardDescription>
                        Explore 50M+ records from UN Comtrade & TradeMap for robust market validation.
                    </CardDescription>
                </CardHeader>
                <CardContent className="flex flex-col sm:flex-row gap-4">
                    <div className="flex-1 max-w-sm relative">
                        <Search className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                        <Input
                            className="pl-9"
                            placeholder="HS Code (e.g. 091091)"
                            value={hsCode}
                            onChange={(e) => setHsCode(e.target.value)}
                        />
                    </div>
                    <div className="flex-1 max-w-sm">
                        <Input
                            placeholder="Country ISO3 (e.g. USA, IND)"
                            value={country}
                            onChange={(e) => setCountry(e.target.value.toUpperCase())}
                        />
                    </div>
                    <Button onClick={handleSearch} disabled={loading} className="px-8 shadow-sm">
                        {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : "Analyze Market"}
                    </Button>
                </CardContent>
            </Card>

            {results.length > 0 && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 animate-in fade-in duration-500">
                    {/* Visual Analytics 1: Import/Export Trends */}
                    <Card className="border-slate-200 shadow-sm overflow-hidden">
                        <CardHeader className="bg-slate-50/50 border-b border-slate-100 pb-4">
                            <div className="flex items-center gap-2">
                                <TrendingUp className="h-5 w-5 text-indigo-500" />
                                <CardTitle className="text-md">Import/Export Trends</CardTitle>
                            </div>
                        </CardHeader>
                        <CardContent className="p-6">
                            <div className="h-64 w-full">
                                <ResponsiveContainer width="100%" height="100%">
                                    <AreaChart data={trendsData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                                        <defs>
                                            <linearGradient id="colorImp" x1="0" y1="0" x2="0" y2="1">
                                                <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.8} />
                                                <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                                            </linearGradient>
                                            <linearGradient id="colorExp" x1="0" y1="0" x2="0" y2="1">
                                                <stop offset="5%" stopColor="#10b981" stopOpacity={0.8} />
                                                <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                                            </linearGradient>
                                        </defs>
                                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                                        <XAxis dataKey="year" tick={{ fontSize: 12, fill: '#64748b' }} axisLine={false} tickLine={false} />
                                        <YAxis tick={{ fontSize: 12, fill: '#64748b' }} axisLine={false} tickLine={false} tickFormatter={formatCurrency} />
                                        <RechartsTooltip
                                            contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                                            formatter={(value: any) => [formatCurrency(value), ""]}
                                        />
                                        <Area type="monotone" dataKey="Import" stroke="#8b5cf6" fillOpacity={1} fill="url(#colorImp)" />
                                        <Area type="monotone" dataKey="Export" stroke="#10b981" fillOpacity={1} fill="url(#colorExp)" />
                                    </AreaChart>
                                </ResponsiveContainer>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Visual Analytics 2: Top Competitors (Exporters) */}
                    <Card className="border-slate-200 shadow-sm overflow-hidden">
                        <CardHeader className="bg-slate-50/50 border-b border-slate-100 pb-4">
                            <div className="flex items-center gap-2">
                                <Globe2 className="h-5 w-5 text-blue-500" />
                                <CardTitle className="text-md">Competitor Mapping (Top Exporters)</CardTitle>
                            </div>
                        </CardHeader>
                        <CardContent className="p-6">
                            <div className="h-64 w-full">
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={competitorsData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }} layout="vertical">
                                        <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f1f5f9" />
                                        <XAxis type="number" tick={{ fontSize: 12, fill: '#64748b' }} axisLine={false} tickLine={false} tickFormatter={formatCurrency} />
                                        <YAxis dataKey="name" type="category" tick={{ fontSize: 12, fill: '#334155', fontWeight: 500 }} axisLine={false} tickLine={false} width={80} />
                                        <RechartsTooltip
                                            cursor={{ fill: '#f8fafc' }}
                                            contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                                            formatter={(value: any) => [formatCurrency(value), "Export Value"]}
                                        />
                                        <Bar dataKey="value" fill="#3b82f6" radius={[0, 4, 4, 0]} barSize={24} />
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            )}

            {/* Data Table */}
            <Card className="border-slate-200 shadow-sm overflow-hidden">
                <CardHeader className="bg-slate-50/50 border-b border-slate-100 pb-4">
                    <CardTitle className="text-md">Raw Data Feed</CardTitle>
                </CardHeader>
                <CardContent className="p-0">
                    <Table>
                        <TableHeader className="bg-slate-50">
                            <TableRow>
                                <TableHead className="font-semibold text-slate-600">Year</TableHead>
                                <TableHead className="font-semibold text-slate-600">Reporter</TableHead>
                                <TableHead className="font-semibold text-slate-600">Partner</TableHead>
                                <TableHead className="font-semibold text-slate-600">Flow</TableHead>
                                <TableHead className="font-semibold text-slate-600">HS Code</TableHead>
                                <TableHead className="text-right font-semibold text-slate-600">Value (USD)</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {results.length === 0 && !loading ? (
                                <TableRow>
                                    <TableCell colSpan={6} className="h-32 text-center text-slate-500">
                                        No data currently loaded. Enter an HS code and click Analyze.
                                    </TableCell>
                                </TableRow>
                            ) : (
                                results.map((row, i) => (
                                    <TableRow key={i} className="hover:bg-slate-50/50">
                                        <TableCell className="text-slate-600">{row.year}</TableCell>
                                        <TableCell className="font-medium text-slate-900">{row.reporter_country}</TableCell>
                                        <TableCell className="text-slate-600">{row.partner_country || "World"}</TableCell>
                                        <TableCell>
                                            <Badge variant="outline" className={row.trade_flow === "export" ? "border-emerald-200 text-emerald-700 bg-emerald-50" : "border-purple-200 text-purple-700 bg-purple-50"}>
                                                {row.trade_flow.toUpperCase()}
                                            </Badge>
                                        </TableCell>
                                        <TableCell className="font-mono text-sm text-slate-500">{row.hs_code}</TableCell>
                                        <TableCell className="text-right font-medium text-slate-700">
                                            ${row.trade_value_usd.toLocaleString()}
                                        </TableCell>
                                    </TableRow>
                                ))
                            )}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>
        </div>
    )
}
