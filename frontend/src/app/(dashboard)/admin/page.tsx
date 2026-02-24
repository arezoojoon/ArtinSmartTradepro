"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/context/AuthContext";
import api from "@/lib/api";
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Users, Building2, ShieldAlert, Settings, CreditCard, Activity } from "lucide-react";
import { useRouter } from "next/navigation";
import Link from "next/link";

interface TeamMember {
    id: string;
    email: string;
    full_name: string;
    role: string;
    is_active: boolean;
}

export default function TenantAdminDashboard() {
    const { user, isAuthenticated } = useAuth();
    const router = useRouter();

    const [members, setMembers] = useState<TeamMember[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                // Fetch current tenant's team members
                const res = await api.get("/admin/users");
                setMembers(res.data || []);
            } catch (error) {
                console.error("Failed to fetch admin data", error);
            } finally {
                setLoading(false);
            }
        };

        if (isAuthenticated) {
            fetchData();
        }
    }, [isAuthenticated]);

    if (loading) {
        return <div className="p-8 text-white">Loading Admin Panel...</div>;
    }

    return (
        <div className="flex-1 space-y-6 p-8 pt-6">
            <div>
                <h2 className="text-3xl font-bold tracking-tight text-white">Organization Admin</h2>
                <p className="text-slate-400 mt-1">Manage your team, billing, and settings.</p>
            </div>

            {/* Quick Stats */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card className="bg-[#0F172A] border-[#1E293B]">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-slate-400">Team Members</CardTitle>
                        <Users className="h-4 w-4 text-[#D4AF37]" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white">{members.length}</div>
                    </CardContent>
                </Card>
                <Card className="bg-[#0F172A] border-[#1E293B]">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-slate-400">Plan</CardTitle>
                        <CreditCard className="h-4 w-4 text-emerald-400" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white capitalize">{user?.tenant?.mode || "hybrid"}</div>
                    </CardContent>
                </Card>
                <Card className="bg-[#0F172A] border-[#1E293B]">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-slate-400">Status</CardTitle>
                        <Activity className="h-4 w-4 text-emerald-400" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-emerald-400">Active</div>
                    </CardContent>
                </Card>
                <Link href="/settings">
                    <Card className="bg-[#0F172A] border-[#1E293B] hover:border-[#D4AF37]/50 transition-colors cursor-pointer h-full">
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium text-slate-400">Settings</CardTitle>
                            <Settings className="h-4 w-4 text-slate-400" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-sm font-medium text-[#D4AF37]">Manage Settings →</div>
                        </CardContent>
                    </Card>
                </Link>
            </div>

            {/* Team Members */}
            <Card className="bg-[#0F172A] border-[#1E293B]">
                <CardHeader>
                    <CardTitle className="text-white">Team Members</CardTitle>
                    <CardDescription className="text-slate-400">Manage your organization&apos;s team.</CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="relative overflow-x-auto">
                        <table className="w-full text-sm text-left text-slate-400">
                            <thead className="text-xs text-slate-300 uppercase bg-[#0A0F1C]">
                                <tr>
                                    <th scope="col" className="px-6 py-3">Full Name</th>
                                    <th scope="col" className="px-6 py-3">Email</th>
                                    <th scope="col" className="px-6 py-3">Role</th>
                                    <th scope="col" className="px-6 py-3">Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                {members.length === 0 ? (
                                    <tr>
                                        <td colSpan={4} className="px-6 py-8 text-center text-slate-500">
                                            No team members found. Invite your team from Settings → Team.
                                        </td>
                                    </tr>
                                ) : (
                                    members.map((m) => (
                                        <tr key={m.id} className="bg-[#0F172A] border-b border-[#1E293B] hover:bg-[#1E293B]/50">
                                            <td className="px-6 py-4 font-medium text-white">{m.full_name || "N/A"}</td>
                                            <td className="px-6 py-4">{m.email}</td>
                                            <td className="px-6 py-4 uppercase text-xs font-semibold">{m.role}</td>
                                            <td className="px-6 py-4">
                                                <span className={`px-2 py-1 rounded text-xs ${m.is_active ? 'bg-emerald-900/50 text-emerald-400' : 'bg-red-900/50 text-red-400'}`}>
                                                    {m.is_active ? 'Active' : 'Inactive'}
                                                </span>
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                </CardContent>
            </Card>

            {/* Quick Links */}
            <div className="grid gap-4 md:grid-cols-3">
                <Link href="/settings/team">
                    <Card className="bg-[#0F172A] border-[#1E293B] hover:border-[#D4AF37]/50 transition-colors cursor-pointer">
                        <CardContent className="p-5 flex items-center gap-3">
                            <Users className="h-5 w-5 text-[#D4AF37]" />
                            <div>
                                <p className="text-white font-semibold">Invite Team Members</p>
                                <p className="text-xs text-slate-500">Add users and assign roles</p>
                            </div>
                        </CardContent>
                    </Card>
                </Link>
                <Link href="/settings/billing">
                    <Card className="bg-[#0F172A] border-[#1E293B] hover:border-[#D4AF37]/50 transition-colors cursor-pointer">
                        <CardContent className="p-5 flex items-center gap-3">
                            <CreditCard className="h-5 w-5 text-[#D4AF37]" />
                            <div>
                                <p className="text-white font-semibold">Billing & Plans</p>
                                <p className="text-xs text-slate-500">Manage subscription and invoices</p>
                            </div>
                        </CardContent>
                    </Card>
                </Link>
                <Link href="/settings/integrations">
                    <Card className="bg-[#0F172A] border-[#1E293B] hover:border-[#D4AF37]/50 transition-colors cursor-pointer">
                        <CardContent className="p-5 flex items-center gap-3">
                            <Settings className="h-5 w-5 text-[#D4AF37]" />
                            <div>
                                <p className="text-white font-semibold">Integrations</p>
                                <p className="text-xs text-slate-500">Connect WhatsApp, Stripe & more</p>
                            </div>
                        </CardContent>
                    </Card>
                </Link>
            </div>
        </div>
    );
}
