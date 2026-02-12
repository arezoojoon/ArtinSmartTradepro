"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Plus, Search, Users, TrendingUp, Clock, Target } from "lucide-react"

export default function PipelinesPage() {
    const [pipelines, setPipelines] = useState<any[]>([])
    const [searchTerm, setSearchTerm] = useState("")

    useEffect(() => {
        // Dummy data for now
        setPipelines([
            {
                id: 1,
                name: "Sales Pipeline",
                description: "Track leads from initial contact to closing",
                stages: ["Lead", "Qualified", "Proposal", "Negotiation", "Closed"],
                totalDeals: 45,
                activeDeals: 12,
                value: 2500000,
                conversion: 23.5
            },
            {
                id: 2,
                name: "Procurement Pipeline",
                description: "Manage supplier relationships and purchasing process",
                stages: ["RFQ", "Quote", "Review", "Order", "Delivery"],
                totalDeals: 28,
                activeDeals: 8,
                value: 1800000,
                conversion: 67.8
            },
            {
                id: 3,
                name: "Partnership Pipeline",
                description: "Track strategic partnerships and collaborations",
                stages: ["Prospect", "Discussion", "Due Diligence", "Agreement", "Active"],
                totalDeals: 15,
                activeDeals: 4,
                value: 5000000,
                conversion: 40.0
            }
        ])
    }, [])

    const filteredPipelines = pipelines.filter(pipeline =>
        pipeline.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        pipeline.description.toLowerCase().includes(searchTerm.toLowerCase())
    )

    return (
        <div className="flex flex-col gap-6 p-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold">Pipelines</h1>
                    <p className="text-muted-foreground">Manage your business pipelines</p>
                </div>
                <Button>
                    <Plus className="h-4 w-4 mr-2" />
                    Create Pipeline
                </Button>
            </div>

            <div className="flex gap-4">
                <div className="relative flex-1 max-w-sm">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                        placeholder="Search pipelines..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="pl-10"
                    />
                </div>
            </div>

            <div className="grid gap-6 md:grid-cols-1 lg:grid-cols-1">
                {filteredPipelines.map((pipeline) => (
                    <Card key={pipeline.id} className="hover:shadow-lg transition-shadow">
                        <CardHeader>
                            <div className="flex justify-between items-start">
                                <div>
                                    <CardTitle className="text-xl">{pipeline.name}</CardTitle>
                                    <CardDescription className="mt-1">
                                        {pipeline.description}
                                    </CardDescription>
                                </div>
                                <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                                    Active
                                </Badge>
                            </div>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-6">
                                {/* Pipeline Stages */}
                                <div>
                                    <h4 className="text-sm font-medium text-muted-foreground mb-3">Pipeline Stages</h4>
                                    <div className="flex gap-2 flex-wrap">
                                        {pipeline.stages.map((stage: string, index: number) => (
                                            <div key={stage} className="flex items-center gap-2">
                                                <Badge variant="outline" className="text-xs">
                                                    {stage}
                                                </Badge>
                                                {index < pipeline.stages.length - 1 && (
                                                    <div className="w-4 h-0.5 bg-border" />
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                {/* Metrics */}
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                    <div className="text-center">
                                        <div className="flex items-center justify-center gap-1 text-2xl font-bold text-blue-600">
                                            <Users className="h-5 w-5" />
                                            {pipeline.totalDeals}
                                        </div>
                                        <div className="text-xs text-muted-foreground">Total Deals</div>
                                    </div>
                                    <div className="text-center">
                                        <div className="flex items-center justify-center gap-1 text-2xl font-bold text-green-600">
                                            <Target className="h-5 w-5" />
                                            {pipeline.activeDeals}
                                        </div>
                                        <div className="text-xs text-muted-foreground">Active Deals</div>
                                    </div>
                                    <div className="text-center">
                                        <div className="flex items-center justify-center gap-1 text-2xl font-bold text-purple-600">
                                            <TrendingUp className="h-5 w-5" />
                                            {pipeline.conversion}%
                                        </div>
                                        <div className="text-xs text-muted-foreground">Conversion</div>
                                    </div>
                                    <div className="text-center">
                                        <div className="flex items-center justify-center gap-1 text-2xl font-bold text-orange-600">
                                            ${((pipeline.value) / 1000000).toFixed(1)}M
                                        </div>
                                        <div className="text-xs text-muted-foreground">Pipeline Value</div>
                                    </div>
                                </div>

                                {/* Progress Visualization */}
                                <div>
                                    <div className="flex justify-between items-center mb-2">
                                        <span className="text-sm text-muted-foreground">Pipeline Progress</span>
                                        <span className="text-sm text-muted-foreground">
                                            {pipeline.activeDeals} of {pipeline.totalDeals} active
                                        </span>
                                    </div>
                                    <div className="w-full bg-gray-200 rounded-full h-2">
                                        <div
                                            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                                            style={{ width: `${(pipeline.activeDeals / pipeline.totalDeals) * 100}%` }}
                                        />
                                    </div>
                                </div>

                                {/* Actions */}
                                <div className="flex gap-2 pt-2">
                                    <Button variant="outline" size="sm" className="flex-1">
                                        View Details
                                    </Button>
                                    <Button variant="outline" size="sm" className="flex-1">
                                        Edit Pipeline
                                    </Button>
                                    <Button size="sm" className="flex-1">
                                        Add Deal
                                    </Button>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>

            {filteredPipelines.length === 0 && (
                <div className="text-center py-12">
                    <Target className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <h3 className="text-lg font-semibold mb-2">No pipelines found</h3>
                    <p className="text-muted-foreground mb-4">
                        {searchTerm ? "Try adjusting your search terms" : "Create your first pipeline to get started"}
                    </p>
                    {!searchTerm && (
                        <Button>
                            <Plus className="h-4 w-4 mr-2" />
                            Create Pipeline
                        </Button>
                    )}
                </div>
            )}
        </div>
    )
}