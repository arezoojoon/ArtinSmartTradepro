"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Users, UserPlus, Shield, Mail } from "lucide-react";

const ROLES = [
    { value: "owner", label: "Owner", desc: "Full access + Billing" },
    { value: "trade_manager", label: "Trade Manager", desc: "Hunter/Brain/CRM + Reports" },
    { value: "sales_agent", label: "Sales Agent", desc: "CRM + Inbox + Campaigns" },
    { value: "sourcing_agent", label: "Sourcing Agent", desc: "Supplier + RFQ + Risk" },
    { value: "finance", label: "Finance", desc: "Wallet + Cash Flow + Invoices" },
    { value: "ops_logistics", label: "Ops/Logistics", desc: "Freight + Shipment + Docs" },
    { value: "viewer", label: "Viewer", desc: "Read-only access" },
];

export default function TeamSettingsPage() {
    const [inviteEmail, setInviteEmail] = useState("");
    const [inviteRole, setInviteRole] = useState("viewer");

    return (
        <div className="p-4 md:p-8 space-y-8 max-w-4xl text-white">
            <div>
                <h1 className="text-2xl font-bold flex items-center gap-2">
                    <Users className="h-6 w-6 text-[#f5a623]" /> Team Management
                </h1>
                <p className="text-white/60">Invite members and manage roles (RBAC).</p>
            </div>

            {/* Invite */}
            <Card className="bg-[#0e1e33] border-[#1e3a5f]">
                <CardHeader>
                    <CardTitle className="text-white flex items-center gap-2">
                        <UserPlus className="h-5 w-5 text-[#f5a623]" /> Invite Team Member
                    </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="flex gap-4">
                        <div className="flex-1">
                            <Label className="text-white/70">Email</Label>
                            <Input
                                type="email"
                                placeholder="colleague@company.com"
                                value={inviteEmail}
                                onChange={(e) => setInviteEmail(e.target.value)}
                                className="bg-navy-950 border-navy-700 text-white mt-1"
                            />
                        </div>
                        <div className="w-48">
                            <Label className="text-white/70">Role</Label>
                            <select
                                value={inviteRole}
                                onChange={(e) => setInviteRole(e.target.value)}
                                className="w-full mt-1 bg-navy-950 border border-navy-700 text-white rounded-md p-2 text-sm"
                            >
                                {ROLES.map((r) => (
                                    <option key={r.value} value={r.value}>{r.label}</option>
                                ))}
                            </select>
                        </div>
                    </div>
                    <Button className="bg-gold-500 hover:bg-gold-600 text-navy-900 font-bold">
                        <Mail className="h-4 w-4 mr-2" /> Send Invitation
                    </Button>
                </CardContent>
            </Card>

            {/* Roles Reference */}
            <Card className="bg-[#0e1e33] border-[#1e3a5f]">
                <CardHeader>
                    <CardTitle className="text-white flex items-center gap-2">
                        <Shield className="h-5 w-5 text-[#f5a623]" /> Available Roles
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid gap-3">
                        {ROLES.map((role) => (
                            <div key={role.value} className="flex items-center justify-between p-3 bg-navy-950 rounded-lg border border-[#1e3a5f]">
                                <div>
                                    <span className="font-semibold text-white">{role.label}</span>
                                    <p className="text-xs text-white/50">{role.desc}</p>
                                </div>
                                <Badge variant="outline" className="text-[#f5a623] border-gold-500/30">
                                    {role.value}
                                </Badge>
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
