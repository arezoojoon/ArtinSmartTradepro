"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { ArrowUpRight, ArrowDownRight, RefreshCw, DollarSign } from "lucide-react"
import api from "@/lib/api"

export default function FXPage() {
    const [base, setBase] = useState("USD")
    const [quote, setQuote] = useState("EUR")
    const [rate, setRate] = useState<any>(null)
    const [loading, setLoading] = useState(false)

    const fetchRate = async () => {
        setLoading(true)
        try {
            const res = await api.get(`/api/toolbox/fx?base=${base}&quote=${quote}`)
            setRate(res.data)
        } catch (error) {
            console.error(error)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchRate()
    }, [base, quote])

    return (
        <div className="space-y-6 max-w-4xl mx-auto">
            <div className="flex items-center justify-between">
                <h2 className="text-3xl font-bold tracking-tight">FX Center 💱</h2>
            </div>

            <div className="grid gap-6 md:grid-cols-2">
                <Card>
                    <CardHeader>
                        <CardTitle>Currency Pair</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Base</label>
                                <Select value={base} onValueChange={setBase}>
                                    <SelectTrigger>
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="USD">USD ($)</SelectItem>
                                        <SelectItem value="EUR">EUR (€)</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Quote</label>
                                <Select value={quote} onValueChange={setQuote}>
                                    <SelectTrigger>
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="EUR">EUR (€)</SelectItem>
                                        <SelectItem value="CNY">CNY (¥)</SelectItem>
                                        <SelectItem value="AED">AED (د.إ)</SelectItem>
                                        <SelectItem value="INR">INR (₹)</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {rate && (
                    <Card className="flex flex-col justify-center items-center py-8">
                        <div className="text-5xl font-bold flex items-center tracking-tighter">
                            {Number(rate.rate).toFixed(4)}
                        </div>
                        <div className="text-muted-foreground mt-2 flex items-center">
                            1 {rate.base_currency} = {Number(rate.rate).toFixed(4)} {rate.quote_currency}
                        </div>
                        <div className="mt-6 flex items-center space-x-2">
                            <span className="flex h-2 w-2 rounded-full bg-green-500" />
                            <span className="text-xs text-muted-foreground">Live Rate from {rate.provider}</span>
                        </div>
                    </Card>
                )}
            </div>
        </div>
    )
}
