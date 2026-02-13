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
import { Users, Building2, ShieldAlert } from "lucide-react";
import { useRouter } from "next/navigation";

// Types matching backend Pydantic models
interface TenantInfo {
    id: string;
    name: string;
    slug: string;
    is_active: boolean;
    balance: number;
}

interface UserInfo {
    id: string;
    email: string;
    full_name: string;
    role: string;
    is_active: boolean;
    tenant_id: string | null;
}

interface AdminStats {
    total_tenants: number;
    active_tenants: number;
    total_users: number;
}

export default function SuperAdminDashboard() {
    const { user, isAuthenticated } = useAuth();
    const router = useRouter();

    const [stats, setStats] = useState<AdminStats | null>(null);
    const [tenants, setTenants] = useState<TenantInfo[]>([]);
    const [users, setUsers] = useState<UserInfo[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Redundant check, middleware or layout should handle this ideally
        if (user && user.role !== "super_admin") {
            // router.push("/dashboard"); 
            // Commented out to prevent redirect loop during dev if role is not set correctly in context
        }

        const fetchData = async () => {
            try {
                const [statsRes, tenantsRes, usersRes] = await Promise.all([
                    api.get("/admin/stats"),
                    api.get("/admin/tenants"),
                    api.get("/admin/users")
                ]);

                setStats(statsRes.data);
                setTenants(tenantsRes.data);
                setUsers(usersRes.data);
            } catch (error) {
                console.error("Failed to fetch admin data", error);
            } finally {
                setLoading(false);
            }
        };

        if (isAuthenticated) {
            fetchData();
        }
    }, [user, isAuthenticated]);

    if (loading) {
        return <div className="p-8 text-white">Loading Admin Dashboard...</div>;
    }

    return (
        <div className="flex-1 space-y-4 p-8 pt-6">
            <div className="flex items-center justify-between space-y-2">
                <h2 className="text-3xl font-bold tracking-tight text-white">Super Admin Dashboard</h2>
            </div>

            {/* Stats Cards */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card className="bg-navy-800 border-navy-700">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-gray-200">Total Tenants</CardTitle>
                        <Building2 className="h-4 w-4 text-gold-400" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white">{stats?.total_tenants || 0}</div>
                    </CardContent>
                </Card>
                <Card className="bg-navy-800 border-navy-700">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-gray-200">Active Tenants</CardTitle>
                        <ShieldAlert className="h-4 w-4 text-green-400" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white">{stats?.active_tenants || 0}</div>
                    </CardContent>
                </Card>
                <Card className="bg-navy-800 border-navy-700">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-gray-200">Total Users</CardTitle>
                        <Users className="h-4 w-4 text-blue-400" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white">{stats?.total_users || 0}</div>
                    </CardContent>
                </Card>
            </div>

            {/* Tabs for Data */}
            <Tabs defaultValue="tenants" className="space-y-4">
                <TabsList className="bg-navy-900 border border-navy-700">
                    <TabsTrigger value="tenants" className="data-[state=active]:bg-gold-500 data-[state=active]:text-navy-900 text-gray-400">Tenants</TabsTrigger>
                    <TabsTrigger value="users" className="data-[state=active]:bg-gold-500 data-[state=active]:text-navy-900 text-gray-400">Users</TabsTrigger>
                </TabsList>

                <TabsContent value="tenants" className="space-y-4">
                    <Card className="bg-navy-900 border-navy-800">
                        <CardHeader>
                            <CardTitle className="text-white">All Tenants</CardTitle>
                            <CardDescription className="text-gray-400">Manage platform tenants.</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="relative overflow-x-auto">
                                <table className="w-full text-sm text-left text-gray-400">
                                    <thead className="text-xs text-gray-200 uppercase bg-navy-800">
                                        <tr>
                                            <th scope="col" className="px-6 py-3">Name</th>
                                            <th scope="col" className="px-6 py-3">Slug</th>
                                            <th scope="col" className="px-6 py-3">Status</th>
                                            <th scope="col" className="px-6 py-3">Balance</th>
                                            <th scope="col" className="px-6 py-3">ID</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {tenants.map((tenant) => (
                                            <tr key={tenant.id} className="bg-navy-900 border-b border-navy-800 hover:bg-navy-800">
                                                <td className="px-6 py-4 font-medium text-white">{tenant.name}</td>
                                                <td className="px-6 py-4">{tenant.slug}</td>
                                                <td className="px-6 py-4">
                                                    <span className={`px-2 py-1 rounded text-xs ${tenant.is_active ? 'bg-green-900 text-green-300' : 'bg-red-900 text-red-300'}`}>
                                                        {tenant.is_active ? 'Active' : 'Disabled'}
                                                    </span>
                                                </td>
                                                <td className="px-6 py-4">${tenant.balance.toFixed(2)}</td>
                                                <td className="px-6 py-4 font-mono text-xs">{tenant.id}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="users" className="space-y-4">
                    <Card className="bg-navy-900 border-navy-800">
                        <CardHeader>
                            <CardTitle className="text-white">All Users</CardTitle>
                            <CardDescription className="text-gray-400">System-wide user list.</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="relative overflow-x-auto">
                                <table className="w-full text-sm text-left text-gray-400">
                                    <thead className="text-xs text-gray-200 uppercase bg-navy-800">
                                        <tr>
                                            <th scope="col" className="px-6 py-3">Full Name</th>
                                            <th scope="col" className="px-6 py-3">Email</th>
                                            <th scope="col" className="px-6 py-3">Role</th>
                                            <th scope="col" className="px-6 py-3">Tenant ID</th>
                                            <th scope="col" className="px-6 py-3">Status</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {users.map((u) => (
                                            <tr key={u.id} className="bg-navy-900 border-b border-navy-800 hover:bg-navy-800">
                                                <td className="px-6 py-4 font-medium text-white">{u.full_name || "N/A"}</td>
                                                <td className="px-6 py-4">{u.email}</td>
                                                <td className="px-6 py-4 uppercase text-xs">{u.role}</td>
                                                <td className="px-6 py-4 font-mono text-xs">{u.tenant_id || "None"}</td>
                                                <td className="px-6 py-4">
                                                    <span className={`px-2 py-1 rounded text-xs ${u.is_active ? 'bg-green-900 text-green-300' : 'bg-red-900 text-red-300'}`}>
                                                        {u.is_active ? 'Active' : 'Disabled'}
                                                    </span>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>
    );
}
