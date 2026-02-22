"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { BarChart3, Clock, DollarSign, TrendingUp, Download, PieChart, Activity, SlidersHorizontal, Plus } from "lucide-react"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, Cell } from 'recharts'
import api from "@/lib/api"

export default function AnalyticsPage() {
    const [kpis, setKpis] = useState<any>(null)
    const [loading, setLoading] = useState(true)

    // Mock data for the Custom KPI Builder chart
    const monthlyPerformance = [
        { month: 'Jan', revenue: 45000, target: 40000 },
        { month: 'Feb', revenue: 52000, target: 42000 },
        { month: 'Mar', revenue: 48000, target: 45000 },
        { month: 'Apr', revenue: 61000, target: 48000 },
        { month: 'May', revenue: 59000, target: 50000 },
        { month: 'Jun', revenue: 72000, target: 55000 },
    ]

    useEffect(() => {
        const fetchKpis = async () => {
            try {
                const res = await api.get("/toolbox/analytics")
                setKpis(res.data)
            } catch (error) {
                console.error("KPI fetch failed", error)
            } finally {
                setLoading(false)
            }
        }
        fetchKpis()
    }, [])

    if (loading) return (
        <div className="flex items-center justify-center p-12 text-slate-400">
            <Activity className="h-6 w-6 animate-spin mr-2" />
            Generating Analytics...
        </div>
    )

    return (
        <div className="space-y-6 max-w-7xl mx-auto">
            {/* Header with Report Exporter */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">Business Intelligence 📊</h2>
                    <p className="text-muted-foreground mt-1">Custom KPI Builder & Automated Reporting</p>
                </div>
                <div className="flex items-center gap-3">
                    <Button variant="outline" className="shadow-sm border-slate-200">
                        <PieChart className="mr-2 h-4 w-4 text-indigo-500" />
                        Schedule Reports
                    </Button>
                    <Button className="shadow-sm" onClick={() => window.print()}>
                        <Download className="mr-2 h-4 w-4" />
                        Export PDF
                    </Button>
                </div>
            </div>

            {/* Core Health Metrics */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card className="shadow-sm border-slate-200 hover:border-slate-300 transition-colors">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 bg-slate-50/50">
                        <CardTitle className="text-sm font-semibold text-slate-600">DSO (Realized)</CardTitle>
                        <DollarSign className="h-4 w-4 text-emerald-500" />
                    </CardHeader>
                    <CardContent className="pt-4">
                        <div className="text-3xl font-bold text-slate-800 tracking-tight">{kpis?.dso_realized} <span className="text-sm font-medium text-slate-500 tracking-normal">Days</span></div>
                        <p className="text-xs text-slate-500 mt-2 font-medium">
                            Avg time to get PAID globally
                        </p>
                    </CardContent>
                </Card>

                <Card className="shadow-sm border-slate-200 hover:border-slate-300 transition-colors">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 bg-slate-50/50">
                        <CardTitle className="text-sm font-semibold text-slate-600">DSO (Projected)</CardTitle>
                        <Clock className="h-4 w-4 text-amber-500" />
                    </CardHeader>
                    <CardContent className="pt-4">
                        <div className="text-3xl font-bold text-slate-800 tracking-tight">{kpis?.dso_projected} <span className="text-sm font-medium text-slate-500 tracking-normal">Days</span></div>
                        <p className="text-xs text-slate-500 mt-2 font-medium">
                            Avg age of OPEN invoices
                        </p>
                    </CardContent>
                </Card>

                <Card className="shadow-sm border-slate-200 hover:border-slate-300 transition-colors">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 bg-slate-50/50">
                        <CardTitle className="text-sm font-semibold text-slate-600">Pipeline Conversion</CardTitle>
                        <TrendingUp className="h-4 w-4 text-blue-500" />
                    </CardHeader>
                    <CardContent className="pt-4">
                        <div className="text-3xl font-bold text-slate-800 tracking-tight">{kpis?.conversion_rate}<span className="text-xl">%</span></div>
                        <p className="text-xs text-slate-500 mt-2 font-medium">
                            Deals Won / Total Closed
                        </p>
                    </CardContent>
                </Card>

                <Card className="shadow-sm border-slate-200 hover:border-slate-300 transition-colors">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 bg-slate-50/50">
                        <CardTitle className="text-sm font-semibold text-slate-600">Avg Response Time</CardTitle>
                        <Clock className="h-4 w-4 text-purple-500" />
                    </CardHeader>
                    <CardContent className="pt-4">
                        <div className="text-3xl font-bold text-slate-800 tracking-tight">{kpis?.response_time_avg} <span className="text-sm font-medium text-slate-500 tracking-normal">Hours</span></div>
                        <p className="text-xs text-slate-500 mt-2 font-medium">
                            Time to reply to new leads
                        </p>
                    </CardContent>
                </Card>
            </div>

            {/* KPI Builder UI */}
            <Card className="shadow-sm border-slate-200">
                <CardHeader className="bg-slate-50/80 border-b pb-4 flex flex-row items-center justify-between">
                    <div>
                        <CardTitle className="text-lg flex items-center gap-2">
                            <SlidersHorizontal className="h-5 w-5 text-indigo-500" />
                            Custom KPI Builder
                        </CardTitle>
                        <CardDescription className="mt-1">
                            Build, combine, and visualize multiple distinct data points across regions.
                        </CardDescription>
                    </div>
                    <Button variant="outline" size="sm" className="h-8">
                        <Plus className="h-4 w-4 mr-1" /> Add Metric
                    </Button>
                </CardHeader>
                <CardContent className="p-6">
                    <div className="grid lg:grid-cols-3 gap-8">

                        {/* Builder Controls */}
                        <div className="col-span-1 space-y-6 border-r border-slate-100 pr-6">
                            <div>
                                <h4 className="text-sm font-semibold text-slate-700 mb-3 uppercase tracking-wider">Active Metrics</h4>
                                <div className="space-y-2">
                                    <div className="flex items-center justify-between p-2 rounded-md bg-blue-50 border border-blue-100">
                                        <div className="flex items-center gap-2">
                                            <div className="w-2 h-2 rounded-full bg-blue-500"></div>
                                            <span className="text-sm font-medium text-blue-900">Total Revenue</span>
                                        </div>
                                    </div>
                                    <div className="flex items-center justify-between p-2 rounded-md bg-slate-50 border border-slate-200">
                                        <div className="flex items-center gap-2">
                                            <div className="w-2 h-2 rounded-full bg-slate-400"></div>
                                            <span className="text-sm font-medium text-slate-700">Target Revenue</span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div>
                                <h4 className="text-sm font-semibold text-slate-700 mb-3 uppercase tracking-wider">Dimensions</h4>
                                <div className="flex flex-wrap gap-2">
                                    <Badge variant="secondary" className="bg-slate-100 hover:bg-slate-200 text-slate-700 cursor-pointer">Date: Monthly</Badge>
                                    <Badge variant="secondary" className="bg-slate-100 hover:bg-slate-200 text-slate-700 cursor-pointer">Region: All</Badge>
                                    <Badge variant="secondary" className="bg-slate-100 hover:bg-slate-200 text-slate-700 cursor-pointer">Entity: Global</Badge>
                                </div>
                            </div>
                        </div>

                        {/* Chart Visualization */}
                        <div className="col-span-2 h-72">
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={monthlyPerformance} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                                    <XAxis dataKey="month" tick={{ fontSize: 12, fill: '#64748b' }} axisLine={false} tickLine={false} />
                                    <YAxis tick={{ fontSize: 12, fill: '#64748b' }} axisLine={false} tickLine={false} tickFormatter={(val) => `$${val / 1000}k`} />
                                    <RechartsTooltip
                                        cursor={{ fill: '#f8fafc' }}
                                        contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                                    />
                                    <Bar dataKey="target" fill="#cbd5e1" radius={[4, 4, 0, 0]} barSize={20} name="Target" />
                                    <Bar dataKey="revenue" fill="#3b82f6" radius={[4, 4, 0, 0]} barSize={20} name="Revenue" />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>

                    </div>
                </CardContent>
            </Card>

        </div>
    )
}
