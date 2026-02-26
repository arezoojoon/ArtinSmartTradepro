"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Ship, Plane, Calendar, DollarSign, Loader2, Anchor, ShieldAlert, CheckCircle2, AlertTriangle, Info } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import api from "@/lib/api"

export default function FreightPage() {
    const [loading, setLoading] = useState(false)
    const [result, setResult] = useState<any>(null)

    const [origin, setOrigin] = useState("CHN")
    const [dest, setDest] = useState("USA")
    const [equipment, setEquipment] = useState("20GP")

    const handleQuote = async () => {
        setLoading(true)
        setResult(null)
        try {
            const params = new URLSearchParams({ origin, dest, equipment })
            const res = await api.get(`/toolbox/freight?${params.toString()}`)
            setResult(res.data)
        } catch (error) {
            console.error("Freight quote failed", error)
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="space-y-6 max-w-6xl mx-auto">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">Freight & Logistics Hub 🚢</h2>
                    <p className="text-muted-foreground mt-1">Sea/Air Rates, Port Risks, and Landed Cost Calculators</p>
                </div>
            </div>

            <div className="grid gap-6 md:grid-cols-12">
                {/* Search Panel */}
                <Card className="md:col-span-5 h-fit shadow-sm">
                    <CardHeader className="bg-slate-50 border-b">
                        <CardTitle className="text-xl flex items-center gap-2">
                            <Anchor className="h-5 w-5 text-blue-500" />
                            Route Search
                        </CardTitle>
                        <CardDescription>
                            Get instant spot rates from global carriers.
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-5 pt-6">
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <label className="text-sm font-semibold text-slate-700">Origin (ISO3)</label>
                                <Input value={origin} onChange={(e) => setOrigin(e.target.value.toUpperCase())} maxLength={3} className="bg-slate-50" />
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-semibold text-slate-700">Destination (ISO3)</label>
                                <Input value={dest} onChange={(e) => setDest(e.target.value.toUpperCase())} maxLength={3} className="bg-slate-50" />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <label className="text-sm font-semibold text-slate-700">Equipment Type</label>
                            <Select value={equipment} onValueChange={setEquipment}>
                                <SelectTrigger className="bg-slate-50">
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="20GP">20ft General Purpose</SelectItem>
                                    <SelectItem value="40HC">40ft High Cube</SelectItem>
                                    <SelectItem value="AIR">Air Freight (per kg)</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                        <Button className="w-full h-12 text-md mt-2 shadow-sm" onClick={handleQuote} disabled={loading}>
                            {loading ? <Loader2 className="mr-2 h-5 w-5 animate-spin" /> : (equipment === "AIR" ? <Plane className="mr-2 h-5 w-5" /> : <Ship className="mr-2 h-5 w-5" />)}
                            Calculate Route Rates
                        </Button>
                    </CardContent>
                </Card>

                {/* Results Panel */}
                <div className="md:col-span-7 space-y-6">
                    {!result && !loading && (
                        <div className="h-full min-h-[400px] flex flex-col items-center justify-center text-slate-400 border-2 border-dashed border-slate-200 rounded-xl bg-slate-50/50">
                            <Ship className="h-12 w-12 mb-4 text-slate-300" />
                            <p>Enter route details to view freight rates, port risks, and hidden costs.</p>
                        </div>
                    )}

                    {loading && (
                        <div className="h-full min-h-[400px] flex flex-col items-center justify-center text-slate-400 border border-slate-200 rounded-xl bg-slate-50">
                            <Loader2 className="h-8 w-8 animate-spin mb-4 text-blue-500" />
                            <p>Querying global carrier databases...</p>
                        </div>
                    )}

                    {result && !loading && (
                        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                            {/* Primary Rate Card */}
                            <Card className="border-blue-100 shadow-md overflow-hidden">
                                <div className="bg-blue-600 p-6 text-white flex justify-between items-end">
                                    <div>
                                        <p className="text-blue-100 text-sm font-medium mb-1 uppercase tracking-wider">{result.provider} • Spot Rate</p>
                                        <h3 className="text-4xl font-bold tracking-tight">${result.rate_amount.toLocaleString()}</h3>
                                    </div>
                                    <div className="text-right">
                                        <div className="text-xl font-semibold">{result.origin_country} <span className="text-blue-300 opacity-70 px-2">➔</span> {result.destination_country}</div>
                                        <p className="text-blue-200 text-sm mt-1">{result.equipment_type} • {result.incoterm}</p>
                                    </div>
                                </div>
                                <div className="bg-white flex grid-cols-3 divide-x text-center border-b">
                                    <div className="p-4 flex-1">
                                        <div className="text-sm font-medium text-slate-500 flex items-center justify-center gap-2 mb-1">
                                            <Calendar className="h-4 w-4" /> Transit Time
                                        </div>
                                        <div className="font-semibold text-lg text-slate-800">{result.transit_days_estimate} Days</div>
                                    </div>
                                    <div className="p-4 flex-1">
                                        <div className="text-sm font-medium text-slate-500 flex items-center justify-center gap-2 mb-1">
                                            <Ship className="h-4 w-4" /> Mode
                                        </div>
                                        <div className="font-semibold text-lg text-slate-800">{equipment === "AIR" ? "Air" : "Sea"} Freight</div>
                                    </div>
                                    <div className="p-4 flex-1">
                                        <div className="text-sm font-medium text-slate-500 flex items-center justify-center gap-2 mb-1">
                                            <DollarSign className="h-4 w-4" /> Validity
                                        </div>
                                        <div className="font-semibold text-lg text-slate-800">7 Days</div>
                                    </div>
                                </div>
                            </Card>

                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                                {/* Port Risks */}
                                <Card className="shadow-sm border-slate-200">
                                    <CardHeader className="bg-slate-50/80 border-b pb-4">
                                        <CardTitle className="text-base flex items-center gap-2">
                                            <ShieldAlert className="h-5 w-5 text-rose-500" />
                                            Route & Port Risks
                                        </CardTitle>
                                    </CardHeader>
                                    <CardContent className="p-0">
                                        <div className="divide-y">
                                            {result.port_risks.map((risk: any, i: number) => (
                                                <div key={i} className="p-4 flex items-start gap-4 hover:bg-slate-50 transition-colors">
                                                    <div className="mt-0.5">
                                                        {risk.level === "High" ? <AlertTriangle className="h-5 w-5 text-rose-500" /> :
                                                            risk.level === "Moderate" ? <AlertTriangle className="h-5 w-5 text-amber-500" /> :
                                                                <CheckCircle2 className="h-5 w-5 text-emerald-500" />}
                                                    </div>
                                                    <div>
                                                        <div className="flex items-center gap-2">
                                                            <span className="font-semibold text-sm text-slate-800">{risk.port}</span>
                                                            <Badge variant="outline" className={`text-[10px] uppercase ${risk.level === "High" ? "bg-rose-50 text-rose-700 border-rose-200" : risk.level === "Moderate" ? "bg-amber-50 text-amber-700 border-amber-200" : "bg-emerald-50 text-emerald-700 border-emerald-200"}`}>{risk.level}</Badge>
                                                        </div>
                                                        <p className="text-xs text-slate-500 mt-1">{risk.issue}</p>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </CardContent>
                                </Card>

                                {/* Hidden Costs Checklist */}
                                <Card className="shadow-sm border-slate-200">
                                    <CardHeader className="bg-slate-50/80 border-b pb-4">
                                        <CardTitle className="text-base flex items-center gap-2">
                                            <Info className="h-5 w-5 text-indigo-500" />
                                            Hidden Costs Checklist
                                        </CardTitle>
                                    </CardHeader>
                                    <CardContent className="p-0">
                                        <div className="divide-y relative">
                                            {result.hidden_costs.map((cost: any, i: number) => (
                                                <div key={i} className="p-4 flex items-center justify-between hover:bg-slate-50 transition-colors">
                                                    <div>
                                                        <div className="font-medium text-sm text-slate-800">{cost.item}</div>
                                                        <div className="text-xs text-slate-500 mt-0.5">{cost.type} Fee</div>
                                                    </div>
                                                    <div className="font-mono text-sm text-slate-600 bg-slate-100 px-2 py-1 rounded">
                                                        +${cost.est}
                                                    </div>
                                                </div>
                                            ))}
                                            <div className="bg-slate-50 p-4 border-t border-slate-200 flex justify-between items-center">
                                                <span className="text-sm font-bold text-slate-700">Estimated Total Landed (CIF)</span>
                                                <span className="font-bold text-indigo-600 text-lg">${(result.rate_amount + result.hidden_costs.reduce((sum: number, c: any) => sum + c.est, 0)).toLocaleString()}</span>
                                            </div>
                                        </div>
                                    </CardContent>
                                </Card>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
