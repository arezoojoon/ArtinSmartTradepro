"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Ship, Plane, Calendar, DollarSign, Loader2 } from "lucide-react"
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
            const res = await api.get(`/api/toolbox/freight?${params.toString()}`)
            setResult(res.data)
        } catch (error) {
            console.error("Freight quote failed", error)
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="space-y-6 max-w-4xl mx-auto">
            <div className="flex items-center justify-between">
                <h2 className="text-3xl font-bold tracking-tight">Freight Calculator 🚢</h2>
            </div>

            <div className="grid gap-6 md:grid-cols-2">
                <Card>
                    <CardHeader>
                        <CardTitle>Route Details</CardTitle>
                        <CardDescription>
                            Get instant estimates for standard routes.
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Origin (ISO3)</label>
                                <Input value={origin} onChange={(e) => setOrigin(e.target.value.toUpperCase())} maxLength={3} />
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Destination (ISO3)</label>
                                <Input value={dest} onChange={(e) => setDest(e.target.value.toUpperCase())} maxLength={3} />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <label className="text-sm font-medium">Equipment</label>
                            <Select value={equipment} onValueChange={setEquipment}>
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="20GP">20ft General Purpose</SelectItem>
                                    <SelectItem value="40HC">40ft High Cube</SelectItem>
                                    <SelectItem value="AIR">Air Freight (kg)</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                        <Button className="w-full" onClick={handleQuote} disabled={loading}>
                            {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Ship className="mr-2 h-4 w-4" />}
                            Get Quote
                        </Button>
                    </CardContent>
                </Card>

                {result && (
                    <Card className="bg-slate-50 border-blue-100">
                        <CardHeader>
                            <CardTitle className="text-blue-600">Estimate: ${result.rate_amount.toLocaleString()}</CardTitle>
                            <CardDescription>
                                {result.origin_country} ➔ {result.destination_country} • {result.equipment_type}
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="flex items-center justify-between p-3 bg-white rounded-lg border">
                                <div className="flex items-center text-muted-foreground">
                                    <Calendar className="mr-2 h-4 w-4" /> Transit Time
                                </div>
                                <span className="font-semibold">{result.transit_days_estimate} Days</span>
                            </div>
                            <div className="flex items-center justify-between p-3 bg-white rounded-lg border">
                                <div className="flex items-center text-muted-foreground">
                                    <Ship className="mr-2 h-4 w-4" /> Incoterm
                                </div>
                                <span className="font-semibold">{result.incoterm}</span>
                            </div>
                            <div className="text-xs text-muted-foreground text-center">
                                Provider: {result.provider} • Valid until: 7 days
                            </div>
                        </CardContent>
                    </Card>
                )}
            </div>
        </div>
    )
}
