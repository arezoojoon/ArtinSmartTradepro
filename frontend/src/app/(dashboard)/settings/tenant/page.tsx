"use client";
import React from "react";
import { useAuth } from "@/context/AuthContext";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import TenantSwitcher from "@/components/layout/TenantSwitcher";
import { Building2, Users } from "lucide-react";

export default function TenantSettingsPage() {
    const { user } = useAuth();

    return (
        <div className="space-y-6">
            <h1 className="text-3xl font-bold text-white">Organization Settings</h1>

            <div className="grid gap-6 md:grid-cols-2">
                <Card className="bg-navy-900 border-navy-700 text-white">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Building2 className="h-5 w-5 text-gold-400" />
                            Current Organization
                        </CardTitle>
                        <CardDescription>Manage your active workspace context.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="p-4 bg-navy-950 rounded-lg border border-navy-800">
                            <p className="text-sm text-gray-400 mb-1">Active Context</p>
                            <p className="text-xl font-bold text-white">{user?.tenant?.name || "No Active Organization"}</p>
                            <p className="text-xs uppercase text-gold-500 mt-1 font-semibold tracking-wider">
                                {user?.tenant?.mode} Plan
                            </p>
                        </div>

                        <div>
                            <label className="text-sm font-medium mb-2 block">Switch Organization</label>
                            <TenantSwitcher />
                        </div>

                        <Button className="w-full bg-navy-800 hover:bg-navy-700 text-white border border-navy-600">
                            Create New Organization
                        </Button>
                    </CardContent>
                </Card>

                <Card className="bg-navy-900 border-navy-700 text-white">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Users className="h-5 w-5 text-blue-400" />
                            Team Members
                        </CardTitle>
                        <CardDescription>Invite and manage team access.</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="text-center py-8 text-gray-500 text-sm">
                            <p>Team management features coming in Phase 2.</p>
                            <Button variant="outline" className="mt-4 border-navy-600 text-gray-400 " disabled>
                                Invite Member
                            </Button>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
