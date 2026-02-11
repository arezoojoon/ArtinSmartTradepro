"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Check, Star } from "lucide-react";

export default function CompareQuotesPage() {
    const params = useParams();
    const [quotes, setQuotes] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (params.id) {
            fetchComparison();
        }
    }, [params.id]);

    const fetchComparison = async () => {
        try {
            const res = await api.get(`/api/v1/sourcing/rfqs/${params.id}/compare`);
            setQuotes(res.data);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div className="p-8 text-white">Analyzing Quotes...</div>;

    return (
        <div className="p-8 space-y-8 bg-black min-h-screen text-white">
            <h1 className="text-3xl font-bold flex items-center gap-2">
                Quote Comparison Matrix
            </h1>
            <p className="text-gray-400">AI-Ranked offers based on Price + Reliability + Lead Time.</p>

            <Card className="bg-navy-900 border-navy-800">
                <CardContent className="p-0">
                    <Table>
                        <TableHeader>
                            <TableRow className="border-navy-700 bg-navy-950">
                                <TableHead className="text-gray-400">Rank</TableHead>
                                <TableHead className="text-gray-400">Supplier</TableHead>
                                <TableHead className="text-gray-400">Price (Unit)</TableHead>
                                <TableHead className="text-gray-400">Incoterm</TableHead>
                                <TableHead className="text-gray-400">Lead Time</TableHead>
                                <TableHead className="text-gray-400">Reliability Score</TableHead>
                                <TableHead className="text-gray-400 text-right">Decision</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {quotes.length === 0 ? (
                                <TableRow>
                                    <TableCell colSpan={7} className="text-center py-8 text-gray-500">
                                        No quotes received yet.
                                    </TableCell>
                                </TableRow>
                            ) : (
                                quotes.map((quote, index) => (
                                    <TableRow key={quote.quote_id} className={`border-navy-700 ${index === 0 ? "bg-gold-500/10" : ""}`}>
                                        <TableCell>
                                            <div className="flex items-center gap-2">
                                                <Badge className={`${quote.risk_adjusted_rank === 'A' ? 'bg-green-600' :
                                                        quote.risk_adjusted_rank === 'B' ? 'bg-yellow-600' : 'bg-red-600'
                                                    }`}>
                                                    Grade {quote.risk_adjusted_rank}
                                                </Badge>
                                                {index === 0 && <Star className="h-4 w-4 text-gold-500 fill-gold-500" />}
                                            </div>
                                        </TableCell>
                                        <TableCell className="font-bold text-white">{quote.supplier_name}</TableCell>
                                        <TableCell className="font-mono text-gold-400">${quote.price.toFixed(2)}</TableCell>
                                        <TableCell>{quote.incoterm}</TableCell>
                                        <TableCell>{quote.lead_time} days</TableCell>
                                        <TableCell>
                                            <div className="flex items-center gap-2">
                                                <div className={`h-2 w-2 rounded-full ${quote.reliability_score > 80 ? 'bg-green-500' : 'bg-red-500'
                                                    }`} />
                                                {quote.reliability_score} / 100
                                            </div>
                                        </TableCell>
                                        <TableCell className="text-right">
                                            <Button size="sm" className="bg-gold-500 text-black hover:bg-gold-400">
                                                Award Deal
                                            </Button>
                                        </TableCell>
                                    </TableRow>
                                ))
                            )}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>
        </div>
    );
}
