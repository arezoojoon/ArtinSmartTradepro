"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Search, Download, Loader2 } from "lucide-react"
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

            const res = await api.get(`/api/toolbox/trade-data?${params.toString()}`)
            setResults(res.data)
        } catch (error) {
            console.error("Search failed", error)
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h2 className="text-3xl font-bold tracking-tight">Global Trade Data 🌍</h2>
                <Button variant="outline">
                    <Download className="mr-2 h-4 w-4" /> Export CSV
                </Button>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>Search Filters</CardTitle>
                    <CardDescription>
                        Explore 50M+ records from UN Comtrade & TradeMap.
                    </CardDescription>
                </CardHeader>
                <CardContent className="flex gap-4">
                    <div className="grid w-full max-w-sm items-center gap-1.5">
                        <Input
                            placeholder="HS Code (e.g. 091091)"
                            value={hsCode}
                            onChange={(e) => setHsCode(e.target.value)}
                        />
                    </div>
                    <div className="grid w-full max-w-sm items-center gap-1.5">
                        <Input
                            placeholder="Country ISO3 (e.g. USA)"
                            value={country}
                            onChange={(e) => setCountry(e.target.value.toUpperCase())}
                        />
                    </div>
                    <Button onClick={handleSearch} disabled={loading}>
                        {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Search className="mr-2 h-4 w-4" />}
                        Search
                    </Button>
                </CardContent>
            </Card>

            <Card>
                <CardContent className="p-0">
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Year</TableHead>
                                <TableHead>Reporter</TableHead>
                                <TableHead>Partner</TableHead>
                                <TableHead>Flow</TableHead>
                                <TableHead>HS Code</TableHead>
                                <TableHead className="text-right">Value (USD)</TableHead>
                                <TableHead className="text-right">Qty</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {results.length === 0 ? (
                                <TableRow>
                                    <TableCell colSpan={7} className="h-24 text-center">
                                        No results found. Try searching for HS: 091091 (Saffron).
                                    </TableCell>
                                </TableRow>
                            ) : (
                                results.map((row, i) => (
                                    <TableRow key={i}>
                                        <TableCell>{row.year}</TableCell>
                                        <TableCell className="font-medium">{row.reporter_country}</TableCell>
                                        <TableCell>{row.partner_country || "World"}</TableCell>
                                        <TableCell>
                                            <Badge variant={row.trade_flow === "export" ? "default" : "secondary"}>
                                                {row.trade_flow}
                                            </Badge>
                                        </TableCell>
                                        <TableCell>{row.hs_code}</TableCell>
                                        <TableCell className="text-right">
                                            ${row.trade_value_usd.toLocaleString()}
                                        </TableCell>
                                        <TableCell className="text-right">
                                            {row.quantity?.toLocaleString()} {row.quantity_unit}
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
