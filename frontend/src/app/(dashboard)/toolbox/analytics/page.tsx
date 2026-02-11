"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { BarChart3, Clock, DollarSign, TrendingUp } from "lucide-react"
import api from "@/lib/api"

export default function AnalyticsPage() {
    const [kpis, setKpis] = useState<any>(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const fetchKpis = async () => {
            try {
                const res = await api.get("/api/toolbox/analytics")
                setKpis(res.data)
            } catch (error) {
                console.error("KPI fetch failed", error)
            } finally {
                setLoading(false)
            }
        }
        fetchKpis()
    }, [])

    if (loading) return <div>Loading Analytics...</div>

    return (
        <div className="space-y-6">
            <h2 className="text-3xl font-bold tracking-tight">Business Intelligence 📊</h2>

            <div className="grid gap-4 md:grid-cols-3">
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">DSO (Realized)</CardTitle>
                        <DollarSign className="h-4 w-4 text-green-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{kpis?.dso_realized} Days</div>
                        <p className="text-xs text-muted-foreground">
                            Avg time to get PAID
                        </p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">DSO (Projected)</CardTitle>
                        <Clock className="h-4 w-4 text-orange-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{kpis?.dso_projected} Days</div>
                        <p className="text-xs text-muted-foreground">
                            Avg age of OPEN invoices
                        </p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Pipeline Conversion</CardTitle>
                        <TrendingUp className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{kpis?.conversion_rate}%</div>
                        <p className="text-xs text-muted-foreground">
                            Deals Won / Total Closed
                        </p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Avg Response Time</CardTitle>
                        <Clock className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{kpis?.response_time_avg} Hours</div>
                        <p className="text-xs text-muted-foreground">
                            Time to reply to new leads
                        </p>
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}
