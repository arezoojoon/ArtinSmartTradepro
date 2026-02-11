"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle, TrendingUp, CheckCircle, Clock } from "lucide-react";
import { Progress } from "@/components/ui/progress";

export default function SupplierScorecard() {
    const params = useParams();
    const [data, setData] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (params.id) {
            fetchScorecard();
        }
    }, [params.id]);

    const fetchScorecard = async () => {
        try {
            const res = await api.get(`/api/v1/sourcing/suppliers/${params.id}/scorecard`);
            setData(res.data);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div className="p-8 text-white">Loading Scorecard...</div>;
    if (!data) return <div className="p-8 text-white">Supplier not found.</div>;

    const { supplier, reliability } = data;
    const score = reliability.overall_score;

    return (
        <div className="p-8 space-y-8 bg-black min-h-screen text-white">
            {/* Header */}
            <div className="flex justify-between items-start">
                <div>
                    <h1 className="text-3xl font-bold flex items-center gap-3">
                        {supplier.name}
                        <Badge variant="outline" className="text-gray-400 border-gray-600">
                            {supplier.country}
                        </Badge>
                    </h1>
                    <p className="text-gray-400 mt-1">Supplier Intelligence Scorecard</p>
                </div>
                <div className="text-right">
                    <div className={`text-5xl font-black ${score >= 80 ? "text-green-500" : score >= 50 ? "text-yellow-500" : "text-red-500"
                        }`}>
                        {score}
                    </div>
                    <div className="text-xs text-gray-400 uppercase tracking-widest">Reliability Score</div>
                </div>
            </div>

            {/* Metrics Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <Card className="bg-navy-900 border-navy-800">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm text-gray-400 font-medium flex items-center gap-2">
                            <Clock className="h-4 w-4" /> On-Time Performance
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white mb-2">{reliability.breakdown.on_time}%</div>
                        <Progress value={reliability.breakdown.on_time} className="h-2 bg-navy-800" indicatorClassName="bg-blue-500" />
                    </CardContent>
                </Card>

                <Card className="bg-navy-900 border-navy-800">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm text-gray-400 font-medium flex items-center gap-2">
                            <CheckCircle className="h-4 w-4" /> Quality Index
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white mb-2">{reliability.breakdown.quality}%</div>
                        <Progress value={reliability.breakdown.quality} className="h-2 bg-navy-800" indicatorClassName="bg-purple-500" />
                    </CardContent>
                </Card>

                <Card className="bg-navy-900 border-navy-800">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm text-gray-400 font-medium flex items-center gap-2">
                            <TrendingUp className="h-4 w-4" /> Capacity Index
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white mb-2">{supplier.capacity_index}%</div>
                        <Progress value={supplier.capacity_index} className="h-2 bg-navy-800" indicatorClassName="bg-gold-500" />
                    </CardContent>
                </Card>
            </div>

            {/* Explanations / Issues */}
            <Card className="bg-navy-900 border-navy-800">
                <CardHeader>
                    <CardTitle className="text-white flex items-center gap-2">
                        <AlertTriangle className="h-5 w-5 text-yellow-500" />
                        Risk Factors & Explanations
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    {reliability.explanations.length === 0 ? (
                        <div className="text-green-500 flex items-center gap-2">
                            <CheckCircle className="h-4 w-4" /> No negative issues recorded.
                        </div>
                    ) : (
                        <ul className="space-y-3">
                            {reliability.explanations.map((exp: string, i: number) => (
                                <li key={i} className="flex items-start gap-3 p-3 bg-navy-950 rounded border border-navy-800">
                                    <div className="mt-1 min-w-[6px] h-[6px] rounded-full bg-red-500" />
                                    <span className="text-gray-300 text-sm">{exp}</span>
                                </li>
                            ))}
                        </ul>
                    )}
                </CardContent>
            </Card>

            <div className="flex justify-end">
                <Button variant="destructive" onClick={() => alert("Report Issue Dialog (Stub)")}>
                    Report New Incident
                </Button>
            </div>
        </div>
    );
}
