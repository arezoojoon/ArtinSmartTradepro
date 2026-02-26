"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { ArrowUpRight, ArrowDownRight, RefreshCw, DollarSign, Activity, Calculator, AlertTriangle, TrendingDown } from "lucide-react"
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, ReferenceLine } from 'recharts'
import { Badge } from "@/components/ui/badge"
import api from "@/lib/api"

export default function FXPage() {
    const [base, setBase] = useState("USD")
    const [quote, setQuote] = useState("EUR")
    const [rate, setRate] = useState<any>(null)
    const [loading, setLoading] = useState(false)
    const [historicalData, setHistoricalData] = useState<any[]>([])

    // Scenario Planning State
    const [contractAmount, setContractAmount] = useState<number>(100000)
    const [targetMargin, setTargetMargin] = useState<number>(15) // %

    const fetchRate = async () => {
        setLoading(true)
        try {
            const [rateRes, histRes] = await Promise.allSettled([
                api.get(`/toolbox/fx?base=${base}&quote=${quote}`),
                api.get(`/toolbox/fx/history?base=${base}&quote=${quote}&days=30`),
            ])
            if (rateRes.status === "fulfilled") setRate(rateRes.value.data)
            if (histRes.status === "fulfilled") setHistoricalData(histRes.value.data)
        } catch (error) {
            console.error(error)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchRate()
    }, [base, quote])

    // Derived Scenario Metrics
    const currentCostQuote = contractAmount * (rate?.rate || 1);
    const requiredCostQuote = contractAmount * (rate?.rate || 1) * (1 - (targetMargin / 100));
    const requiredRate = requiredCostQuote / contractAmount;

    const isRateFavorable = rate?.rate <= requiredRate;

    return (
        <div className="space-y-6 max-w-6xl mx-auto">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">FX & Volatility Hub 💱</h2>
                    <p className="text-muted-foreground dark:text-slate-400 mt-1">Live Rates, Volatility Bands, and Scenario Planning</p>
                </div>
                <div className="flex items-center gap-2">
                    <Badge variant="outline" className="bg-emerald-50 text-emerald-700 border-emerald-200 py-1">
                        <span className="flex h-2 w-2 rounded-full bg-emerald-500 mr-2 animate-pulse"></span>
                        Live Markets
                    </Badge>
                </div>
            </div>

            <div className="grid gap-6 md:grid-cols-12">

                {/* Left Column: Selector & Live Rate */}
                <div className="md:col-span-4 space-y-6">
                    <Card className="shadow-sm">
                        <CardHeader className="bg-slate-50 border-b pb-4">
                            <CardTitle className="text-lg">Currency Pair</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4 pt-4">
                            <div className="space-y-4">
                                <div className="space-y-2">
                                    <label className="text-sm font-semibold text-slate-700">Base Currency</label>
                                    <Select value={base} onValueChange={setBase}>
                                        <SelectTrigger className="bg-slate-50">
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="USD">USD ($)</SelectItem>
                                            <SelectItem value="EUR">EUR (€)</SelectItem>
                                            <SelectItem value="GBP">GBP (£)</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                                <div className="space-y-2">
                                    <label className="text-sm font-semibold text-slate-700">Quote Currency</label>
                                    <Select value={quote} onValueChange={setQuote}>
                                        <SelectTrigger className="bg-slate-50">
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="EUR">EUR (€)</SelectItem>
                                            <SelectItem value="CNY">CNY (¥)</SelectItem>
                                            <SelectItem value="AED">AED (د.إ)</SelectItem>
                                            <SelectItem value="INR">INR (₹)</SelectItem>
                                            <SelectItem value="JPY">JPY (¥)</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    <Card className="flex flex-col justify-center items-center py-8 shadow-sm relative overflow-hidden">
                        {loading && (
                            <div className="absolute inset-0 bg-white/80 z-10 flex items-center justify-center backdrop-blur-sm">
                                <RefreshCw className="h-6 w-6 animate-spin text-blue-500" />
                            </div>
                        )}
                        <div className="text-5xl font-bold flex items-center tracking-tighter text-slate-800 dark:text-white">
                            {rate ? Number(rate.rate).toFixed(4) : "—"}
                        </div>
                        <div className="text-slate-500 dark:text-slate-400 font-medium mt-2 flex items-center">
                            1 {base} = {rate ? Number(rate.rate).toFixed(4) : "—"} {quote}
                        </div>
                        <div className="mt-6 flex items-center space-x-2 bg-slate-50 px-3 py-1.5 rounded-full border border-slate-100">
                            <Activity className="h-3 w-3 text-blue-500" />
                            <span className="text-xs font-medium text-slate-500">Source: {rate?.provider || "API"}</span>
                        </div>
                    </Card>
                </div>

                {/* Right Column: Volatility & Scenario Planning */}
                <div className="md:col-span-8 space-y-6">

                    {/* Volatility Band Chart */}
                    <Card className="shadow-sm overflow-hidden">
                        <CardHeader className="bg-slate-50/80 border-b pb-4">
                            <div className="flex items-center justify-between">
                                <CardTitle className="text-base flex items-center gap-2 text-slate-900 dark:text-white">
                                    <Activity className="h-5 w-5 text-indigo-500" />
                                    30-Day Volatility Band
                                </CardTitle>
                                <Badge variant="secondary" className="bg-indigo-50 text-indigo-700 border-indigo-200">2% Risk Band</Badge>
                            </div>
                        </CardHeader>
                        <CardContent className="p-6">
                            <div className="h-64 w-full">
                                {historicalData.length > 0 ? (
                                    <ResponsiveContainer width="100%" height="100%">
                                        <AreaChart data={historicalData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                                            <defs>
                                                <linearGradient id="colorRate" x1="0" y1="0" x2="0" y2="1">
                                                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                                                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                                                </linearGradient>
                                            </defs>
                                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                                            <XAxis dataKey="date" tick={{ fontSize: 12, fill: '#64748b' }} axisLine={false} tickLine={false} minTickGap={20} />
                                            <YAxis domain={['auto', 'auto']} tick={{ fontSize: 12, fill: '#64748b' }} axisLine={false} tickLine={false} />
                                            <RechartsTooltip
                                                contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                                            />
                                            {/* Volatility Bands */}
                                            <Area type="monotone" dataKey="upper" stroke="none" fill="#fef2f2" />
                                            <Area type="monotone" dataKey="lower" stroke="none" fill="#ffffff" />

                                            {/* Actual Rate */}
                                            <Area type="monotone" dataKey="rate" stroke="#3b82f6" strokeWidth={2} fillOpacity={1} fill="url(#colorRate)" />
                                        </AreaChart>
                                    </ResponsiveContainer>
                                ) : (
                                    <div className="h-full flex items-center justify-center text-slate-400">Loading chart data...</div>
                                )}
                            </div>
                        </CardContent>
                    </Card>

                    {/* Scenario Planning Calculator */}
                    <Card className="shadow-sm">
                        <CardHeader className="bg-slate-50/80 border-b pb-4">
                            <CardTitle className="text-base flex items-center gap-2 text-slate-900 dark:text-white">
                                <Calculator className="h-5 w-5 text-amber-500" />
                                Cost Scenario Planning
                            </CardTitle>
                            <CardDescription>
                                Calculate how FX fluctuations impact your local landed cost and margins.
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="p-6">
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-8">
                                <div className="space-y-4">
                                    <div className="space-y-2">
                                        <label className="text-sm font-semibold text-slate-700">Contract Subtotal ({base})</label>
                                        <div className="relative">
                                            <DollarSign className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                                            <Input
                                                type="number"
                                                className="pl-9 bg-slate-50"
                                                value={contractAmount}
                                                onChange={(e) => setContractAmount(Number(e.target.value) || 0)}
                                            />
                                        </div>
                                    </div>
                                    <div className="space-y-2">
                                        <label className="text-sm font-semibold text-slate-700">Target Profit Margin (%)</label>
                                        <Input
                                            type="number"
                                            className="bg-slate-50"
                                            value={targetMargin}
                                            onChange={(e) => setTargetMargin(Number(e.target.value) || 0)}
                                        />
                                    </div>
                                </div>

                                <div className="bg-slate-50 rounded-xl p-5 border border-slate-100 flex flex-col justify-center">
                                    <div className="space-y-4">
                                        <div className="flex justify-between items-center">
                                            <span className="text-sm text-slate-500">Current Est. Cost:</span>
                                            <span className="font-semibold text-slate-800">{currentCostQuote.toLocaleString(undefined, { maximumFractionDigits: 0 })} {quote}</span>
                                        </div>
                                        <div className="flex justify-between items-center">
                                            <span className="text-sm text-slate-500">Max Permissible Cost (for {targetMargin}% margin):</span>
                                            <span className="font-semibold text-slate-800">{requiredCostQuote.toLocaleString(undefined, { maximumFractionDigits: 0 })} {quote}</span>
                                        </div>
                                        <div className="h-px bg-slate-200 my-2"></div>
                                        <div>
                                            <div className="flex justify-between items-center mb-2">
                                                <span className="text-sm font-semibold text-slate-700">Required Exchange Rate:</span>
                                                <span className={`font-bold ${isRateFavorable ? 'text-emerald-600' : 'text-rose-600'}`}>
                                                    ≤ {requiredRate.toFixed(4)}
                                                </span>
                                            </div>
                                            {!isRateFavorable ? (
                                                <div className="flex items-start gap-2 text-xs text-amber-700 bg-amber-50 p-2 rounded border border-amber-200">
                                                    <AlertTriangle className="h-4 w-4 shrink-0" />
                                                    <p>Current rate ({rate?.rate.toFixed(4)}) is too high to achieve a {targetMargin}% margin. Consider forward contracts or renegotiating subtotal.</p>
                                                </div>
                                            ) : (
                                                <div className="flex items-start gap-2 text-xs text-emerald-700 bg-emerald-50 p-2 rounded border border-emerald-200">
                                                    <TrendingDown className="h-4 w-4 shrink-0" />
                                                    <p>Current rate ({rate?.rate.toFixed(4)}) is favorable. You are positioned to hit your target margin.</p>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                </div>
            </div>
        </div>
    )
}
