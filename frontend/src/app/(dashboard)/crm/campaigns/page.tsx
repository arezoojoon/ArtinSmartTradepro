"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Plus, Search, Calendar, Mail, Target, TrendingUp } from "lucide-react"
import Link from "next/link"

export default function CampaignsPage() {
    const [campaigns, setCampaigns] = useState<any[]>([])
    const [searchTerm, setSearchTerm] = useState("")

    useEffect(() => {
        // Dummy data for now
        setCampaigns([
            {
                id: 1,
                name: "Spring Collection Launch",
                status: "active",
                type: "email",
                leads: 1250,
                conversion: 3.2,
                date: "2024-03-15"
            },
            {
                id: 2,
                name: "VIP Customer Follow-up",
                status: "draft",
                type: "sms",
                leads: 450,
                conversion: 0,
                date: "2024-03-20"
            }
        ])
    }, [])

    const filteredCampaigns = campaigns.filter(campaign =>
        campaign.name.toLowerCase().includes(searchTerm.toLowerCase())
    )

    return (
        <div className="flex flex-col gap-6 p-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold">Campaigns</h1>
                    <p className="text-muted-foreground">Manage your marketing campaigns</p>
                </div>
                <Link href="/dashboard/crm/campaigns/new">
                    <Button>
                        <Plus className="h-4 w-4 mr-2" />
                        New Campaign
                    </Button>
                </Link>
            </div>

            <div className="flex gap-4">
                <div className="relative flex-1 max-w-sm">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                        placeholder="Search campaigns..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="pl-10"
                    />
                </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {filteredCampaigns.map((campaign) => (
                    <Card key={campaign.id} className="hover:shadow-lg transition-shadow">
                        <CardHeader>
                            <div className="flex justify-between items-start">
                                <CardTitle className="text-lg">{campaign.name}</CardTitle>
                                <Badge variant={campaign.status === 'active' ? 'default' : 'secondary'}>
                                    {campaign.status}
                                </Badge>
                            </div>
                            <CardDescription className="flex items-center gap-2">
                                <Mail className="h-4 w-4" />
                                {campaign.type.toUpperCase()} • {campaign.date}
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-2">
                                <div className="flex justify-between text-sm">
                                    <span className="text-muted-foreground">Leads</span>
                                    <span className="font-medium">{campaign.leads.toLocaleString()}</span>
                                </div>
                                <div className="flex justify-between text-sm">
                                    <span className="text-muted-foreground">Conversion</span>
                                    <span className="font-medium">{campaign.conversion}%</span>
                                </div>
                                <div className="flex gap-2 pt-2">
                                    <Button variant="outline" size="sm" className="flex-1">
                                        View
                                    </Button>
                                    <Button size="sm" className="flex-1">
                                        Edit
                                    </Button>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>

            {filteredCampaigns.length === 0 && (
                <div className="text-center py-12">
                    <Target className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <h3 className="text-lg font-semibold mb-2">No campaigns found</h3>
                    <p className="text-muted-foreground mb-4">
                        {searchTerm ? "Try adjusting your search terms" : "Create your first campaign to get started"}
                    </p>
                    {!searchTerm && (
                        <Link href="/dashboard/crm/campaigns/new">
                            <Button>
                                <Plus className="h-4 w-4 mr-2" />
                                Create Campaign
                            </Button>
                        </Link>
                    )}
                </div>
            )}
        </div>
    )
}