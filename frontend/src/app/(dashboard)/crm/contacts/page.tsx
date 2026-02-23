"use client";

import { useState, useEffect } from "react";
import {
    Plus, Search, Filter, MoreHorizontal, User, Mail,
    Phone, MapPin, Building2, Linkedin, MessageSquare,
    Clock, ShieldCheck, MailPlus, UserPlus, Info
} from "lucide-react";
import { BASE_URL } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
    Table, TableBody, TableCell, TableHead, TableHeader, TableRow
} from "@/components/ui/table";
import {
    DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
    Tooltip, TooltipContent, TooltipProvider, TooltipTrigger
} from "@/components/ui/tooltip";

export default function ContactsPage() {
    const [contacts, setContacts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState("");

    useEffect(() => {
        fetchContacts();
    }, [search]);

    const fetchContacts = async () => {
        setLoading(true);
        try {
            const token = localStorage.getItem("access_token");
            const query = search ? `?search=${search}` : "";
            const res = await fetch(`${BASE_URL}/crm/contacts${query}`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setContacts(data.contacts || []);
            }
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-7xl mx-auto space-y-6">
            {/* Header Section */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-slate-900">Contacts</h1>
                    <p className="text-muted-foreground mt-1">Manage individual trade relationships and key stakeholders.</p>
                </div>
                <div className="flex items-center gap-3">
                    <Button variant="outline" className="hidden sm:flex border-slate-200">
                        <MailPlus className="h-4 w-4 mr-2" />
                        Bulk Invite
                    </Button>
                    <Button className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold shadow-sm">
                        <UserPlus className="h-4 w-4 mr-2" />
                        Add Contact
                    </Button>
                </div>
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
                {[
                    { label: "Total Contacts", val: contacts.length, icon: User, color: "indigo" },
                    { label: "WhatsApp Verified", val: contacts.filter((c: any) => c.whatsapp_verified).length, icon: MessageSquare, color: "emerald" },
                    { label: "Avg Sentiment", val: "High", icon: ShieldCheck, color: "sky" },
                    { label: "Recent Comm.", val: "12 Today", icon: Clock, color: "rose" }
                ].map((stat, i) => (
                    <Card key={i} className="shadow-sm border-slate-200 bg-white">
                        <CardContent className="p-4 flex items-center justify-between">
                            <div>
                                <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">{stat.label}</p>
                                <p className="text-xl font-black text-slate-900 mt-1">{loading ? "..." : stat.val}</p>
                            </div>
                            <div className={`p-2 rounded-lg bg-${stat.color}-50`}>
                                <stat.icon className={`h-4 w-4 text-${stat.color}-600`} />
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>

            {/* Search and Filters */}
            <div className="flex flex-col sm:flex-row gap-4 items-center justify-between bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                <div className="relative w-full sm:max-w-md">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                    <Input
                        placeholder="Search by name, email, or phone..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        className="pl-10 bg-slate-50 border-slate-200"
                    />
                </div>
                <div className="flex items-center gap-2 w-full sm:w-auto">
                    <Button variant="outline" className="flex-1 sm:flex-none border-slate-200 bg-white">
                        <Filter className="h-4 w-4 mr-2" />
                        Filters
                    </Button>
                </div>
            </div>

            {/* Contacts Table */}
            <Card className="shadow-sm border-slate-200 overflow-hidden bg-white">
                <Table>
                    <TableHeader className="bg-slate-50/50">
                        <TableRow>
                            <TableHead className="w-[300px] font-bold text-slate-700">Contact Details</TableHead>
                            <TableHead className="font-bold text-slate-700">Company & Role</TableHead>
                            <TableHead className="font-bold text-slate-700">Payment Behavior</TableHead>
                            <TableHead className="font-bold text-slate-700">Verified</TableHead>
                            <TableHead className="text-right font-bold text-slate-700">Actions</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {loading ? (
                            Array.from({ length: 5 }).map((_, i) => (
                                <TableRow key={i}>
                                    <TableCell colSpan={5} className="h-16 animate-pulse bg-slate-50/20" />
                                </TableRow>
                            ))
                        ) : contacts.length === 0 ? (
                            <TableRow>
                                <TableCell colSpan={5} className="h-64 text-center">
                                    <div className="flex flex-col items-center justify-center text-slate-400">
                                        <User className="h-12 w-12 mb-4 opacity-20" />
                                        <p className="text-lg font-medium">No contacts found</p>
                                        <p className="text-sm">Grow your network to start trading</p>
                                    </div>
                                </TableCell>
                            </TableRow>
                        ) : (
                            contacts.map((contact: any) => (
                                <TableRow key={contact.id} className="hover:bg-slate-50/50 transition-colors group">
                                    <TableCell>
                                        <div className="flex items-center gap-3">
                                            <Avatar className="h-10 w-10 border-2 border-slate-100 shadow-sm">
                                                <AvatarImage src={`https://ui-avatars.com/api/?name=${contact.first_name}+${contact.last_name}&background=6366f1&color=fff`} />
                                                <AvatarFallback>{contact.first_name[0]}{contact.last_name?.[0]}</AvatarFallback>
                                            </Avatar>
                                            <div className="flex flex-col">
                                                <div className="font-bold text-slate-900">{contact.first_name} {contact.last_name}</div>
                                                <div className="text-xs text-slate-500 flex items-center gap-2">
                                                    <span className="flex items-center gap-1"><Mail className="h-3 w-3" /> {contact.email || "No Email"}</span>
                                                    <span className="opacity-30">•</span>
                                                    <span className="flex items-center gap-1"><Phone className="h-3 w-3" /> {contact.phone || "No Phone"}</span>
                                                </div>
                                            </div>
                                        </div>
                                    </TableCell>
                                    <TableCell>
                                        <div className="space-y-1">
                                            <div className="flex items-center gap-1.5 text-sm font-bold text-slate-700">
                                                <Building2 className="h-3 w-3 text-indigo-500" />
                                                {contact.company?.name || "Independent"}
                                            </div>
                                            <div className="text-xs text-slate-500 font-medium">{contact.position || "Stakeholder"}</div>
                                        </div>
                                    </TableCell>
                                    <TableCell>
                                        <TooltipProvider>
                                            <Tooltip>
                                                <TooltipTrigger asChild>
                                                    <div className="flex items-center gap-2 cursor-help">
                                                        <div className={`h-2 w-2 rounded-full ${contact.payment_behavior_notes ? 'bg-amber-400' : 'bg-emerald-400'}`} />
                                                        <span className="text-sm font-medium text-slate-600 truncate max-w-[150px]">
                                                            {contact.payment_behavior_notes || "Prompt Payment"}
                                                        </span>
                                                    </div>
                                                </TooltipTrigger>
                                                <TooltipContent>
                                                    <p className="max-w-xs">{contact.payment_behavior_notes || "No negative payment behavior reported for this contact."}</p>
                                                </TooltipContent>
                                            </Tooltip>
                                        </TooltipProvider>
                                    </TableCell>
                                    <TableCell>
                                        <div className="flex items-center gap-2">
                                            {contact.whatsapp_verified ? (
                                                <Badge className="bg-emerald-50 text-emerald-700 border-emerald-100 shadow-none px-2 py-0">
                                                    <ShieldCheck className="h-3 w-3 mr-1" />
                                                    WhatsApp
                                                </Badge>
                                            ) : (
                                                <Badge variant="outline" className="text-slate-400 border-slate-200 font-normal px-2 py-0">
                                                    Unverified
                                                </Badge>
                                            )}
                                        </div>
                                    </TableCell>
                                    <TableCell className="text-right">
                                        <div className="flex items-center justify-end gap-2">
                                            <div className="hidden group-hover:flex items-center gap-1">
                                                {contact.linkedin_url && (
                                                    <a href={contact.linkedin_url} target="_blank" className="p-2 hover:bg-slate-100 rounded-lg text-slate-400 hover:text-blue-600 transition-colors">
                                                        <Linkedin className="h-4 w-4" />
                                                    </a>
                                                )}
                                                <button className="p-2 hover:bg-slate-100 rounded-lg text-slate-400 hover:text-emerald-600 transition-colors">
                                                    <MessageSquare className="h-4 w-4" />
                                                </button>
                                            </div>
                                            <DropdownMenu>
                                                <DropdownMenuTrigger asChild>
                                                    <Button variant="ghost" size="icon" className="h-8 w-8 hover:bg-slate-100">
                                                        <MoreHorizontal className="h-4 w-4" />
                                                    </Button>
                                                </DropdownMenuTrigger>
                                                <DropdownMenuContent align="end">
                                                    <DropdownMenuItem className="font-medium">View Intelligence</DropdownMenuItem>
                                                    <DropdownMenuItem>Assign to Sequence</DropdownMenuItem>
                                                    <DropdownMenuItem>Log Manual Activity</DropdownMenuItem>
                                                    <DropdownMenuItem className="text-rose-600">Archive Contact</DropdownMenuItem>
                                                </DropdownMenuContent>
                                            </DropdownMenu>
                                        </div>
                                    </TableCell>
                                </TableRow>
                            ))
                        )}
                    </TableBody>
                </Table>
            </Card>

            <div className="flex items-center justify-between text-xs text-slate-500 font-medium px-2">
                <p>Total {loading ? "..." : contacts.length} contacts across your trade network.</p>
                <div className="flex items-center gap-1.5 bg-indigo-50 border border-indigo-100 rounded-lg p-1.5 px-3">
                    <Info className="h-3 w-3 text-indigo-500" />
                    Contacts with trade history are prioritized in Hunter scoring.
                </div>
            </div>
        </div>
    );
}
