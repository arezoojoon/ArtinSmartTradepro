"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Plus, Search, Phone, Mail, Building, MapPin, Star } from "lucide-react"
import Link from "next/link"

export default function ContactsPage() {
    const [contacts, setContacts] = useState<any[]>([])
    const [searchTerm, setSearchTerm] = useState("")

    useEffect(() => {
        // Dummy data for now
        setContacts([
            {
                id: 1,
                name: "Ahmed Hassan",
                email: "ahmed@example.com",
                phone: "+971 50 123 4567",
                company: "Gulf Trading Co",
                location: "Dubai, UAE",
                status: "active",
                rating: 4.5,
                tags: ["VIP", "Supplier"]
            },
            {
                id: 2,
                name: "Sarah Johnson",
                email: "sarah@globalcorp.com",
                phone: "+971 55 987 6543",
                company: "Global Corporation",
                location: "Abu Dhabi, UAE",
                status: "lead",
                rating: 3.8,
                tags: ["Potential Client"]
            },
            {
                id: 3,
                name: "Mohammed Ali",
                email: "mohammed@logistics.ae",
                phone: "+971 56 456 7890",
                company: "Fast Logistics",
                location: "Sharjah, UAE",
                status: "active",
                rating: 4.2,
                tags: ["Partner", "Logistics"]
            }
        ])
    }, [])

    const filteredContacts = contacts.filter(contact =>
        contact.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        contact.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
        contact.company.toLowerCase().includes(searchTerm.toLowerCase())
    )

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'active': return 'default'
            case 'lead': return 'secondary'
            default: return 'outline'
        }
    }

    const renderStars = (rating: number) => {
        return Array.from({ length: 5 }, (_, i) => (
            <Star
                key={i}
                className={`h-3 w-3 ${
                    i < Math.floor(rating) ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300'
                }`}
            />
        ))
    }

    return (
        <div className="flex flex-col gap-6 p-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold">Contacts</h1>
                    <p className="text-muted-foreground">Manage your business contacts</p>
                </div>
                <Button>
                    <Plus className="h-4 w-4 mr-2" />
                    Add Contact
                </Button>
            </div>

            <div className="flex gap-4">
                <div className="relative flex-1 max-w-sm">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                        placeholder="Search contacts..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="pl-10"
                    />
                </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {filteredContacts.map((contact) => (
                    <Card key={contact.id} className="hover:shadow-lg transition-shadow">
                        <CardHeader>
                            <div className="flex justify-between items-start">
                                <div>
                                    <CardTitle className="text-lg">{contact.name}</CardTitle>
                                    <CardDescription className="flex items-center gap-1">
                                        <Building className="h-3 w-3" />
                                        {contact.company}
                                    </CardDescription>
                                </div>
                                <Badge variant={getStatusColor(contact.status)}>
                                    {contact.status}
                                </Badge>
                            </div>
                            <div className="flex items-center gap-1">
                                {renderStars(contact.rating)}
                                <span className="text-xs text-muted-foreground ml-1">
                                    {contact.rating}
                                </span>
                            </div>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-3">
                                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                    <Mail className="h-4 w-4" />
                                    <span>{contact.email}</span>
                                </div>
                                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                    <Phone className="h-4 w-4" />
                                    <span>{contact.phone}</span>
                                </div>
                                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                    <MapPin className="h-4 w-4" />
                                    <span>{contact.location}</span>
                                </div>
                                <div className="flex flex-wrap gap-1 pt-2">
                                    {contact.tags.map((tag: string) => (
                                        <Badge key={tag} variant="outline" className="text-xs">
                                            {tag}
                                        </Badge>
                                    ))}
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

            {filteredContacts.length === 0 && (
                <div className="text-center py-12">
                    <Building className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <h3 className="text-lg font-semibold mb-2">No contacts found</h3>
                    <p className="text-muted-foreground mb-4">
                        {searchTerm ? "Try adjusting your search terms" : "Add your first contact to get started"}
                    </p>
                    {!searchTerm && (
                        <Button>
                            <Plus className="h-4 w-4 mr-2" />
                            Add Contact
                        </Button>
                    )}
                </div>
            )}
        </div>
    )
}