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

    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const fetchCampaigns = async () => {
            try {
                const token = localStorage.getItem("token")
                const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/campaigns/`, {
                    headers: { Authorization: `Bearer ${token}` }
                })
                if (res.ok) {
                    const data = await res.json()
                    setCampaigns(Array.isArray(data) ? data : data.items || [])
                }
            } catch (e) {
                console.error("Failed to fetch campaigns:", e)
            } finally {
                setLoading(false)
            }
        }
        fetchCampaigns()
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
                                {(campaign.channel || "whatsapp").toUpperCase()} • {campaign.created_at ? new Date(campaign.created_at).toLocaleDateString() : ""}
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-2">
                                <div className="flex justify-between text-sm">
                                    <span className="text-muted-foreground">Channel</span>
                                    <span className="font-medium">{campaign.channel || "whatsapp"}</span>
                                </div>
                                <div className="flex justify-between text-sm">
                                    <span className="text-muted-foreground">Status</span>
                                    <span className="font-medium capitalize">{campaign.status}</span>
                                </div>
                                <div className="flex gap-2 pt-2">
                                    <Link href={`/crm/campaigns/${campaign.id}`} className="flex-1">
                                        <Button variant="outline" size="sm" className="w-full">
                                            View
                                        </Button>
                                    </Link>
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
