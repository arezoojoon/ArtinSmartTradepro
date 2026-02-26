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
    const [monthlyPerformance, setMonthlyPerformance] = useState<any[]>([])
    const [showSchedule, setShowSchedule] = useState(false)
    const [scheduleForm, setScheduleForm] = useState({ email: "", frequency: "weekly" })
    const [scheduleSaved, setScheduleSaved] = useState(false)
    const [showAddMetric, setShowAddMetric] = useState(false)
    const [customMetrics, setCustomMetrics] = useState<string[]>(["Total Revenue", "Target Revenue"])
    const [newMetricName, setNewMetricName] = useState("")

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [kpiRes, monthlyRes] = await Promise.allSettled([
                    api.get("/toolbox/analytics"),
                    api.get("/toolbox/analytics/monthly"),
                ])
                if (kpiRes.status === "fulfilled") setKpis(kpiRes.value.data)
                if (monthlyRes.status === "fulfilled") setMonthlyPerformance(monthlyRes.value.data)
            } catch (error) {
                console.error("KPI fetch failed", error)
            } finally {
                setLoading(false)
            }
        }
        fetchData()
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
                    <h2 className="text-3xl font-bold tracking-tight text-white">Business Intelligence</h2>
                    <p className="text-slate-400 mt-1">Custom KPI Builder & Automated Reporting</p>
                </div>
                <div className="flex items-center gap-3">
                    <Button variant="outline" className="shadow-sm border-[#1e3a5f] text-slate-300 hover:bg-[#1e3a5f]" onClick={() => { setShowSchedule(true); setScheduleSaved(false); }}>
                        <PieChart className="mr-2 h-4 w-4 text-indigo-500" />
                        Schedule Reports
                    </Button>
                    <Button className="shadow-sm bg-[#f5a623] text-navy-950 hover:bg-gold-500" onClick={() => window.print()}>
                        <Download className="mr-2 h-4 w-4" />
                        Export PDF
                    </Button>
                </div>
            </div>

            {/* Core Health Metrics */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card className="bg-[#12253f]/80 border-[#1e3a5f] hover:border-[#f5a623]/30 transition-colors">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-semibold text-slate-400">DSO (Realized)</CardTitle>
                        <DollarSign className="h-4 w-4 text-emerald-500" />
                    </CardHeader>
                    <CardContent className="pt-4">
                        <div className="text-3xl font-bold text-white tracking-tight">{kpis?.dso_realized} <span className="text-sm font-medium text-slate-500 tracking-normal">Days</span></div>
                        <p className="text-xs text-slate-500 mt-2 font-medium">
                            Avg time to get PAID globally
                        </p>
                    </CardContent>
                </Card>

                <Card className="bg-[#12253f]/80 border-[#1e3a5f] hover:border-[#f5a623]/30 transition-colors">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-semibold text-slate-400">DSO (Projected)</CardTitle>
                        <Clock className="h-4 w-4 text-amber-500" />
                    </CardHeader>
                    <CardContent className="pt-4">
                        <div className="text-3xl font-bold text-white tracking-tight">{kpis?.dso_projected} <span className="text-sm font-medium text-slate-500 tracking-normal">Days</span></div>
                        <p className="text-xs text-slate-500 mt-2 font-medium">
                            Avg age of OPEN invoices
                        </p>
                    </CardContent>
                </Card>

                <Card className="bg-[#12253f]/80 border-[#1e3a5f] hover:border-[#f5a623]/30 transition-colors">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-semibold text-slate-400">Pipeline Conversion</CardTitle>
                        <TrendingUp className="h-4 w-4 text-blue-500" />
                    </CardHeader>
                    <CardContent className="pt-4">
                        <div className="text-3xl font-bold text-white tracking-tight">{kpis?.conversion_rate}<span className="text-xl">%</span></div>
                        <p className="text-xs text-slate-500 mt-2 font-medium">
                            Deals Won / Total Closed
                        </p>
                    </CardContent>
                </Card>

                <Card className="bg-[#12253f]/80 border-[#1e3a5f] hover:border-[#f5a623]/30 transition-colors">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-semibold text-slate-400">Avg Response Time</CardTitle>
                        <Clock className="h-4 w-4 text-purple-500" />
                    </CardHeader>
                    <CardContent className="pt-4">
                        <div className="text-3xl font-bold text-white tracking-tight">{kpis?.response_time_avg} <span className="text-sm font-medium text-slate-500 tracking-normal">Hours</span></div>
                        <p className="text-xs text-slate-500 mt-2 font-medium">
                            Time to reply to new leads
                        </p>
                    </CardContent>
                </Card>
            </div>

            {/* KPI Builder UI */}
            <Card className="bg-[#12253f]/80 border-[#1e3a5f]">
                <CardHeader className="border-b border-[#1e3a5f] pb-4 flex flex-row items-center justify-between">
                    <div>
                        <CardTitle className="text-lg flex items-center gap-2 text-white">
                            <SlidersHorizontal className="h-5 w-5 text-indigo-500" />
                            Custom KPI Builder
                        </CardTitle>
                        <CardDescription className="mt-1 text-slate-500">
                            Build, combine, and visualize multiple distinct data points across regions.
                        </CardDescription>
                    </div>
                    <Button variant="outline" size="sm" className="h-8 border-[#1e3a5f] text-slate-300 hover:bg-[#1e3a5f]" onClick={() => { setShowAddMetric(true); setNewMetricName(""); }}>
                        <Plus className="h-4 w-4 mr-1" /> Add Metric
                    </Button>
                </CardHeader>
                <CardContent className="p-6">
                    <div className="grid lg:grid-cols-3 gap-8">

                        {/* Builder Controls */}
                        <div className="col-span-1 space-y-6 border-r border-[#1e3a5f] pr-6">
                            <div>
                                <h4 className="text-sm font-semibold text-slate-400 mb-3 uppercase tracking-wider">Active Metrics</h4>
                                <div className="space-y-2">
                                    <div className="flex items-center justify-between p-2 rounded-md bg-blue-500/10 border border-blue-500/20">
                                        <div className="flex items-center gap-2">
                                            <div className="w-2 h-2 rounded-full bg-blue-500"></div>
                                            <span className="text-sm font-medium text-blue-300">Total Revenue</span>
                                        </div>
                                    </div>
                                    <div className="flex items-center justify-between p-2 rounded-md bg-[#0e1e33] border border-[#1e3a5f]">
                                        <div className="flex items-center gap-2">
                                            <div className="w-2 h-2 rounded-full bg-slate-400"></div>
                                            <span className="text-sm font-medium text-slate-300">Target Revenue</span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div>
                                <h4 className="text-sm font-semibold text-slate-400 mb-3 uppercase tracking-wider">Dimensions</h4>
                                <div className="flex flex-wrap gap-2">
                                    <Badge variant="secondary" className="bg-[#0e1e33] hover:bg-navy-800 text-slate-300 border border-[#1e3a5f] cursor-pointer">Date: Monthly</Badge>
                                    <Badge variant="secondary" className="bg-[#0e1e33] hover:bg-navy-800 text-slate-300 border border-[#1e3a5f] cursor-pointer">Region: All</Badge>
                                    <Badge variant="secondary" className="bg-[#0e1e33] hover:bg-navy-800 text-slate-300 border border-[#1e3a5f] cursor-pointer">Entity: Global</Badge>
                                </div>
                            </div>
                        </div>

                        {/* Chart Visualization */}
                        <div className="col-span-2 h-72">
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={monthlyPerformance} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#1e3a5f" />
                                    <XAxis dataKey="month" tick={{ fontSize: 12, fill: '#64748b' }} axisLine={false} tickLine={false} />
                                    <YAxis tick={{ fontSize: 12, fill: '#64748b' }} axisLine={false} tickLine={false} tickFormatter={(val) => `$${val / 1000}k`} />
                                    <RechartsTooltip
                                        cursor={{ fill: '#f8fafc' }}
                                        contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                                    />
                                    <Bar dataKey="target" fill="#1e3a5f" radius={[4, 4, 0, 0]} barSize={20} name="Target" />
                                    <Bar dataKey="revenue" fill="#3b82f6" radius={[4, 4, 0, 0]} barSize={20} name="Revenue" />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>

                    </div>
                </CardContent>
            </Card>

            {/* Schedule Reports Modal */}
            {showSchedule && (
                <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={() => setShowSchedule(false)}>
                    <div className="bg-[#0e1e33] border border-[#1e3a5f] rounded-2xl w-full max-w-md p-6 shadow-xl" onClick={e => e.stopPropagation()}>
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-lg font-bold text-white">Schedule Reports</h3>
                            <button onClick={() => setShowSchedule(false)} className="text-slate-400 hover:text-white text-xl">&times;</button>
                        </div>
                        {scheduleSaved ? (
                            <div className="text-center py-6">
                                <div className="h-12 w-12 bg-emerald-500/10 text-emerald-400 rounded-full flex items-center justify-center mx-auto mb-3"><PieChart className="h-6 w-6" /></div>
                                <p className="font-semibold text-white">Report Scheduled!</p>
                                <p className="text-sm text-slate-500 mt-1">You'll receive {scheduleForm.frequency} reports at {scheduleForm.email || "your email"}</p>
                            </div>
                        ) : (
                            <>
                                <div className="space-y-4">
                                    <div>
                                        <label className="block text-xs text-slate-400 mb-1">Email Address</label>
                                        <input value={scheduleForm.email} onChange={e => setScheduleForm(f => ({ ...f, email: e.target.value }))} placeholder="you@company.com" className="w-full px-3 py-2 bg-navy-950 border border-[#1e3a5f] rounded-lg text-sm text-white focus:border-[#f5a623] focus:outline-none" />
                                    </div>
                                    <div>
                                        <label className="block text-xs text-slate-400 mb-1">Frequency</label>
                                        <select value={scheduleForm.frequency} onChange={e => setScheduleForm(f => ({ ...f, frequency: e.target.value }))} className="w-full px-3 py-2 bg-navy-950 border border-[#1e3a5f] rounded-lg text-sm text-white focus:border-[#f5a623] focus:outline-none">
                                            <option value="daily">Daily</option>
                                            <option value="weekly">Weekly</option>
                                            <option value="monthly">Monthly</option>
                                        </select>
                                    </div>
                                </div>
                                <button onClick={() => setScheduleSaved(true)} disabled={!scheduleForm.email.trim()} className="mt-5 w-full py-2.5 bg-[#f5a623] text-navy-950 rounded-lg font-semibold hover:bg-gold-500 transition-all disabled:opacity-50">
                                    Schedule Report
                                </button>
                            </>
                        )}
                    </div>
                </div>
            )}

            {/* Add Metric Modal */}
            {showAddMetric && (
                <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={() => setShowAddMetric(false)}>
                    <div className="bg-[#0e1e33] border border-[#1e3a5f] rounded-2xl w-full max-w-sm p-6 shadow-xl" onClick={e => e.stopPropagation()}>
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-lg font-bold text-white">Add Metric</h3>
                            <button onClick={() => setShowAddMetric(false)} className="text-slate-400 hover:text-white text-xl">&times;</button>
                        </div>
                        <div className="mb-3">
                            <label className="block text-xs text-slate-500 mb-1">Metric Name</label>
                            <input value={newMetricName} onChange={e => setNewMetricName(e.target.value)} placeholder="e.g. Gross Margin, Lead Volume" className="w-full px-3 py-2 bg-navy-950 border border-[#1e3a5f] rounded-lg text-sm text-white focus:border-[#f5a623] focus:outline-none" />
                        </div>
                        <div className="mb-4">
                            <p className="text-xs text-slate-500">Active metrics:</p>
                            <div className="flex flex-wrap gap-1 mt-1">{customMetrics.map((m, i) => <span key={i} className="px-2 py-0.5 bg-[#1e3a5f] rounded text-xs text-slate-300">{m}</span>)}</div>
                        </div>
                        <button onClick={() => { if (newMetricName.trim()) { setCustomMetrics(prev => [...prev, newMetricName.trim()]); setShowAddMetric(false); } }} disabled={!newMetricName.trim()} className="w-full py-2.5 bg-[#f5a623] text-navy-950 rounded-lg font-semibold hover:bg-gold-500 transition-all disabled:opacity-50">
                            Add Metric
                        </button>
                    </div>
                </div>
            )}

        </div>
    )
}
