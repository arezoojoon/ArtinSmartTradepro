"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Mail, Search, Reply, Forward, Star, Trash2, Archive } from "lucide-react"

export default function InboxPage() {
    const [emails, setEmails] = useState<any[]>([])
    const [searchTerm, setSearchTerm] = useState("")

    useEffect(() => {
        // Dummy data for now
        setEmails([
            {
                id: 1,
                from: "Ahmed Hassan",
                fromEmail: "ahmed@example.com",
                subject: "RFQ for Steel Pipes - Project #1234",
                preview: "We need quotation for 500 tons of steel pipes for our Dubai project...",
                date: "2024-03-15",
                time: "10:30 AM",
                read: false,
                starred: true,
                category: "RFQ"
            },
            {
                id: 2,
                from: "Sarah Johnson",
                fromEmail: "sarah@globalcorp.com",
                subject: "Meeting Confirmation - Next Week",
                preview: "Confirming our meeting for Tuesday at 2 PM to discuss partnership...",
                date: "2024-03-15",
                time: "9:15 AM",
                read: true,
                starred: false,
                category: "Meeting"
            },
            {
                id: 3,
                from: "Mohammed Ali",
                fromEmail: "mohammed@logistics.ae",
                subject: "Shipping Update - Order #5678",
                preview: "Your shipment has been dispatched and will arrive by Friday...",
                date: "2024-03-14",
                time: "4:45 PM",
                read: true,
                starred: false,
                category: "Shipping"
            }
        ])
    }, [])

    const filteredEmails = emails.filter(email =>
        email.subject.toLowerCase().includes(searchTerm.toLowerCase()) ||
        email.from.toLowerCase().includes(searchTerm.toLowerCase()) ||
        email.preview.toLowerCase().includes(searchTerm.toLowerCase())
    )

    const getCategoryColor = (category: string) => {
        switch (category) {
            case 'RFQ': return 'default'
            case 'Meeting': return 'secondary'
            case 'Shipping': return 'outline'
            default: return 'outline'
        }
    }

    return (
        <div className="flex flex-col gap-6 p-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold">Inbox</h1>
                    <p className="text-muted-foreground">Manage your emails and communications</p>
                </div>
                <Button>
                    <Mail className="h-4 w-4 mr-2" />
                    Compose
                </Button>
            </div>

            <div className="flex gap-4">
                <div className="relative flex-1 max-w-sm">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                        placeholder="Search emails..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="pl-10"
                    />
                </div>
            </div>

            <div className="space-y-2">
                {filteredEmails.map((email) => (
                    <Card key={email.id} className={`hover:shadow-md transition-shadow cursor-pointer ${!email.read ? 'border-l-4 border-l-blue-500' : ''}`}>
                        <CardHeader className="pb-3">
                            <div className="flex justify-between items-start">
                                <div className="flex-1">
                                    <div className="flex items-center gap-2 mb-1">
                                        <span className={`font-semibold ${!email.read ? 'text-black' : 'text-muted-foreground'}`}>
                                            {email.from}
                                        </span>
                                        <span className="text-sm text-muted-foreground">
                                            &lt;{email.fromEmail}&gt;
                                        </span>
                                        <Badge variant={getCategoryColor(email.category)} className="text-xs">
                                            {email.category}
                                        </Badge>
                                    </div>
                                    <CardTitle className={`text-base mb-1 ${!email.read ? 'text-black' : 'text-muted-foreground'}`}>
                                        {email.subject}
                                    </CardTitle>
                                    <CardDescription className="text-sm">
                                        {email.preview}
                                    </CardDescription>
                                </div>
                                <div className="flex flex-col items-end gap-2">
                                    <div className="text-xs text-muted-foreground">
                                        {email.date}
                                    </div>
                                    <div className="text-xs text-muted-foreground">
                                        {email.time}
                                    </div>
                                    <div className="flex gap-1">
                                        <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                                            <Star className={`h-3 w-3 ${email.starred ? 'fill-yellow-400 text-yellow-400' : 'text-gray-400'}`} />
                                        </Button>
                                        <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                                            <Archive className="h-3 w-3 text-gray-400" />
                                        </Button>
                                        <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                                            <Trash2 className="h-3 w-3 text-gray-400" />
                                        </Button>
                                    </div>
                                </div>
                            </div>
                        </CardHeader>
                        <CardContent className="pt-0">
                            <div className="flex gap-2">
                                <Button variant="outline" size="sm">
                                    <Reply className="h-3 w-3 mr-1" />
                                    Reply
                                </Button>
                                <Button variant="outline" size="sm">
                                    <Forward className="h-3 w-3 mr-1" />
                                    Forward
                                </Button>
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>

            {filteredEmails.length === 0 && (
                <div className="text-center py-12">
                    <Mail className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <h3 className="text-lg font-semibold mb-2">No emails found</h3>
                    <p className="text-muted-foreground mb-4">
                        {searchTerm ? "Try adjusting your search terms" : "Your inbox is empty"}
                    </p>
                    {!searchTerm && (
                        <Button>
                            <Mail className="h-4 w-4 mr-2" />
                            Compose Email
                        </Button>
                    )}
                </div>
            )}
        </div>
    )
}