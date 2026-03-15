"use client";

import { useEffect, useState, useCallback } from "react";
import { useAuth } from "@/context/AuthContext";
import api from "@/lib/api";
import {
    Card, CardContent, CardHeader, CardTitle, CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
    Users, Building2, ShieldCheck, CreditCard, Activity, Search,
    Power, PowerOff, TrendingUp, Crown, Zap, Shield, ChevronDown,
    Loader2, RefreshCw, Layers, UserCog
} from "lucide-react";

interface PlatformStats {
    total_tenants: number;
    active_tenants: number;
    total_users: number;
    active_users: number;
    total_revenue: number;
    plans_breakdown: Record<string, number>;
}

interface TenantInfo {
    id: string;
    name: string;
    slug: string;
    plan: string;
    mode: string;
    is_active: boolean;
    balance: number;
    user_count: number;
    created_at: string | null;
}

interface UserInfo {
    id: string;
    email: string;
    full_name: string | null;
    role: string;
    is_active: boolean;
    is_superuser: boolean;
    tenant_name: string | null;
    membership_role: string | null;
    created_at: string | null;
}

interface PlanInfo {
    id: string;
    name: string;
    display_name: string;
    price_monthly: number | null;
    currency: string;
    is_active: boolean;
    feature_count: number;
    features: string[];
}

const planColors: Record<string, string> = {
    professional: "text-blue-400 bg-blue-500/10 border-blue-500/30",
    enterprise: "text-amber-400 bg-amber-500/10 border-amber-500/30",
    whitelabel: "text-purple-400 bg-purple-500/10 border-purple-500/30",
};

const planIcons: Record<string, any> = {
    professional: Zap,
    enterprise: Crown,
    whitelabel: Shield,
};

export default function SuperAdminDashboard() {
    const { user } = useAuth();
    const [activeTab, setActiveTab] = useState<"overview" | "tenants" | "users" | "plans">("overview");
    const [stats, setStats] = useState<PlatformStats | null>(null);
    const [tenants, setTenants] = useState<TenantInfo[]>([]);
    const [users, setUsers] = useState<UserInfo[]>([]);
    const [plans, setPlans] = useState<PlanInfo[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState("");
    const [actionLoading, setActionLoading] = useState<string | null>(null);

    const fetchAll = useCallback(async () => {
        setLoading(true);
        try {
            const [statsRes, tenantsRes, usersRes, plansRes] = await Promise.allSettled([
                api.get("/admin/stats"),
                api.get("/admin/tenants"),
                api.get("/admin/users"),
                api.get("/admin/plans"),
            ]);
            if (statsRes.status === "fulfilled") setStats(statsRes.value.data);
            if (tenantsRes.status === "fulfilled") setTenants(tenantsRes.value.data);
            if (usersRes.status === "fulfilled") setUsers(usersRes.value.data);
            if (plansRes.status === "fulfilled") setPlans(plansRes.value.data);
        } catch (err) {
            console.error("Admin fetch error:", err);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { fetchAll(); }, [fetchAll]);

    const toggleTenant = async (tenantId: string, newState: boolean) => {
        setActionLoading(tenantId);
        try {
            await api.post("/admin/tenants/toggle", { tenant_id: tenantId, is_active: newState });
            setTenants(prev => prev.map(t => t.id === tenantId ? { ...t, is_active: newState } : t));
        } catch (err) { console.error(err); }
        finally { setActionLoading(null); }
    };

    const changePlan = async (tenantId: string, newPlan: string) => {
        setActionLoading(tenantId);
        try {
            await api.post("/admin/tenants/change-plan", { tenant_id: tenantId, plan: newPlan });
            setTenants(prev => prev.map(t => t.id === tenantId ? { ...t, plan: newPlan } : t));
        } catch (err) { console.error(err); }
        finally { setActionLoading(null); }
    };

    const toggleUser = async (userId: string) => {
        setActionLoading(userId);
        try {
            await api.post(`/admin/users/${userId}/toggle`);
            setUsers(prev => prev.map(u => u.id === userId ? { ...u, is_active: !u.is_active } : u));
        } catch (err) { console.error(err); }
        finally { setActionLoading(null); }
    };

    const seedFeatures = async () => {
        setActionLoading("seed");
        try {
            await api.post("/admin/plans/seed-features");
            await fetchAll();
        } catch (err) { console.error(err); }
        finally { setActionLoading(null); }
    };

    const filteredTenants = tenants.filter(t =>
        t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        t.slug.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const filteredUsers = users.filter(u =>
        u.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (u.full_name || "").toLowerCase().includes(searchQuery.toLowerCase())
    );

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-[60vh]">
                <Loader2 className="h-8 w-8 animate-spin text-[#D4AF37]" />
            </div>
        );
    }

    const tabs = [
        { key: "overview", label: "Overview", icon: Activity },
        { key: "tenants", label: "Tenants", icon: Building2 },
        { key: "users", label: "Users", icon: Users },
        { key: "plans", label: "Plans", icon: Layers },
    ];

    return (
        <div className="flex-1 space-y-6 p-8 pt-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
                        <div className="p-2 bg-[#D4AF37]/10 rounded-xl border border-[#D4AF37]/30">
                            <ShieldCheck className="h-6 w-6 text-[#D4AF37]" />
                        </div>
                        Super Admin Dashboard
                    </h2>
                    <p className="text-slate-400 mt-1">Manage all tenants, users, and plans across the platform.</p>
                </div>
                <Button onClick={fetchAll} variant="outline" size="sm" className="border-[#1E293B] text-slate-300 hover:bg-[#1E293B]">
                    <RefreshCw className="h-4 w-4 mr-2" /> Refresh
                </Button>
            </div>

            {/* Tabs */}
            <div className="flex gap-1 bg-[#0A0F1C] p-1 rounded-xl border border-[#1E293B]">
                {tabs.map(tab => (
                    <button
                        key={tab.key}
                        onClick={() => setActiveTab(tab.key as any)}
                        className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg text-sm font-semibold transition-all
                            ${activeTab === tab.key
                                ? "bg-[#1E293B] text-[#D4AF37] shadow-sm"
                                : "text-slate-500 hover:text-slate-300"
                            }`}
                    >
                        <tab.icon className="h-4 w-4" />
                        {tab.label}
                    </button>
                ))}
            </div>

            {/* ─── OVERVIEW TAB ─── */}
            {activeTab === "overview" && stats && (
                <div className="space-y-6 animate-in fade-in">
                    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                        <StatCard icon={Building2} label="Total Tenants" value={stats.total_tenants} sub={`${stats.active_tenants} active`} color="text-blue-400" />
                        <StatCard icon={Users} label="Total Users" value={stats.total_users} sub={`${stats.active_users} active`} color="text-emerald-400" />
                        <StatCard icon={CreditCard} label="Total Balance" value={`$${stats.total_revenue.toFixed(0)}`} sub="across all wallets" color="text-[#D4AF37]" />
                        <StatCard icon={TrendingUp} label="Plans Active" value={Object.values(stats.plans_breakdown).reduce((a, b) => a + b, 0)} sub="across all tiers" color="text-purple-400" />
                    </div>

                    {/* Plans Breakdown */}
                    <Card className="bg-[#0F172A] border-[#1E293B]">
                        <CardHeader>
                            <CardTitle className="text-white text-lg">Plan Distribution</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="grid grid-cols-3 gap-4">
                                {Object.entries(stats.plans_breakdown).map(([plan, count]) => {
                                    const Icon = planIcons[plan] || Zap;
                                    return (
                                        <div key={plan} className={`p-4 rounded-xl border ${planColors[plan] || "border-slate-600"} flex items-center gap-4`}>
                                            <div className="p-3 rounded-lg bg-black/20">
                                                <Icon className="h-6 w-6" />
                                            </div>
                                            <div>
                                                <p className="text-2xl font-bold text-white">{count}</p>
                                                <p className="text-xs font-medium uppercase tracking-wider opacity-70">{plan}</p>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </CardContent>
                    </Card>
                </div>
            )}

            {/* ─── TENANTS TAB ─── */}
            {activeTab === "tenants" && (
                <div className="space-y-4 animate-in fade-in">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                        <Input
                            placeholder="Search tenants..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="pl-10 bg-[#0A0F1C] border-[#1E293B] text-white"
                        />
                    </div>

                    <div className="space-y-3">
                        {filteredTenants.map(t => (
                            <Card key={t.id} className={`bg-[#0F172A] border-[#1E293B] ${!t.is_active ? 'opacity-50' : ''}`}>
                                <CardContent className="p-5">
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-4">
                                            <div className={`p-2.5 rounded-lg ${t.is_active ? 'bg-emerald-500/10' : 'bg-red-500/10'}`}>
                                                <Building2 className={`h-5 w-5 ${t.is_active ? 'text-emerald-400' : 'text-red-400'}`} />
                                            </div>
                                            <div>
                                                <h3 className="text-white font-semibold text-lg">{t.name}</h3>
                                                <p className="text-slate-500 text-sm">{t.slug} · {t.mode}</p>
                                            </div>
                                        </div>

                                        <div className="flex items-center gap-3">
                                            {/* Plan badge */}
                                            <Badge className={`${planColors[t.plan] || 'bg-slate-600'} border font-semibold uppercase text-xs px-3 py-1`}>
                                                {t.plan}
                                            </Badge>

                                            {/* User count */}
                                            <Badge variant="outline" className="border-[#1E293B] text-slate-400">
                                                <Users className="h-3 w-3 mr-1" /> {t.user_count}
                                            </Badge>

                                            {/* Balance */}
                                            <Badge variant="outline" className="border-[#1E293B] text-[#D4AF37]">
                                                ${t.balance.toFixed(0)}
                                            </Badge>

                                            {/* Plan Change */}
                                            <select
                                                value={t.plan}
                                                onChange={(e) => changePlan(t.id, e.target.value)}
                                                disabled={actionLoading === t.id}
                                                className="bg-[#0A0F1C] border border-[#1E293B] rounded-lg px-2 py-1.5 text-xs text-slate-300 cursor-pointer"
                                            >
                                                <option value="professional">Professional</option>
                                                <option value="enterprise">Enterprise</option>
                                                <option value="whitelabel">White Label</option>
                                            </select>

                                            {/* Toggle */}
                                            <Button
                                                size="sm"
                                                variant="outline"
                                                onClick={() => toggleTenant(t.id, !t.is_active)}
                                                disabled={actionLoading === t.id}
                                                className={`border-[#1E293B] ${t.is_active ? 'text-red-400 hover:bg-red-500/10' : 'text-emerald-400 hover:bg-emerald-500/10'}`}
                                            >
                                                {actionLoading === t.id ? <Loader2 className="h-4 w-4 animate-spin" /> :
                                                    t.is_active ? <><PowerOff className="h-4 w-4 mr-1" /> Disable</> :
                                                    <><Power className="h-4 w-4 mr-1" /> Enable</>
                                                }
                                            </Button>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                </div>
            )}

            {/* ─── USERS TAB ─── */}
            {activeTab === "users" && (
                <div className="space-y-4 animate-in fade-in">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                        <Input
                            placeholder="Search users..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="pl-10 bg-[#0A0F1C] border-[#1E293B] text-white"
                        />
                    </div>

                    <Card className="bg-[#0F172A] border-[#1E293B]">
                        <CardContent className="p-0">
                            <table className="w-full text-sm">
                                <thead className="text-xs text-slate-400 uppercase bg-[#0A0F1C]">
                                    <tr>
                                        <th className="px-5 py-3 text-left">User</th>
                                        <th className="px-5 py-3 text-left">Tenant</th>
                                        <th className="px-5 py-3 text-left">Role</th>
                                        <th className="px-5 py-3 text-left">Status</th>
                                        <th className="px-5 py-3 text-right">Action</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-[#1E293B]">
                                    {filteredUsers.map(u => (
                                        <tr key={u.id} className="hover:bg-[#1E293B]/30 transition-colors">
                                            <td className="px-5 py-4">
                                                <div>
                                                    <p className="text-white font-medium flex items-center gap-2">
                                                        {u.full_name || "N/A"}
                                                        {u.is_superuser && <Crown className="h-3.5 w-3.5 text-[#D4AF37]" />}
                                                    </p>
                                                    <p className="text-slate-500 text-xs">{u.email}</p>
                                                </div>
                                            </td>
                                            <td className="px-5 py-4 text-slate-400 text-xs">{u.tenant_name || "—"}</td>
                                            <td className="px-5 py-4">
                                                <Badge variant="outline" className="border-[#1E293B] text-slate-300 text-xs uppercase">
                                                    {u.membership_role || u.role}
                                                </Badge>
                                            </td>
                                            <td className="px-5 py-4">
                                                <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold ${
                                                    u.is_active ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'
                                                }`}>
                                                    <span className={`h-1.5 w-1.5 rounded-full ${u.is_active ? 'bg-emerald-400' : 'bg-red-400'}`} />
                                                    {u.is_active ? "Active" : "Disabled"}
                                                </span>
                                            </td>
                                            <td className="px-5 py-4 text-right">
                                                <Button
                                                    size="sm"
                                                    variant="ghost"
                                                    onClick={() => toggleUser(u.id)}
                                                    disabled={actionLoading === u.id || u.is_superuser}
                                                    className={`text-xs ${u.is_active ? 'text-red-400 hover:text-red-300' : 'text-emerald-400 hover:text-emerald-300'}`}
                                                >
                                                    {actionLoading === u.id ? <Loader2 className="h-3 w-3 animate-spin" /> :
                                                        u.is_active ? "Disable" : "Enable"
                                                    }
                                                </Button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </CardContent>
                    </Card>
                </div>
            )}

            {/* ─── PLANS TAB ─── */}
            {activeTab === "plans" && (
                <div className="space-y-6 animate-in fade-in">
                    <div className="flex justify-between items-center">
                        <p className="text-slate-400 text-sm">Manage plan definitions and seed feature mappings.</p>
                        <Button
                            onClick={seedFeatures}
                            disabled={actionLoading === "seed"}
                            className="bg-[#D4AF37] hover:bg-[#C5A035] text-black font-semibold"
                        >
                            {actionLoading === "seed" ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <RefreshCw className="h-4 w-4 mr-2" />}
                            Seed Default Features
                        </Button>
                    </div>

                    <div className="grid gap-4 md:grid-cols-3">
                        {plans.map(p => {
                            const Icon = planIcons[p.name] || Zap;
                            return (
                                <Card key={p.id} className={`bg-[#0F172A] border-[#1E293B] overflow-hidden`}>
                                    <div className={`h-1 ${p.name === "enterprise" ? "bg-[#D4AF37]" : p.name === "whitelabel" ? "bg-purple-500" : "bg-blue-500"}`} />
                                    <CardHeader>
                                        <div className="flex items-center gap-3">
                                            <div className={`p-2 rounded-lg ${planColors[p.name] || ''}`}>
                                                <Icon className="h-5 w-5" />
                                            </div>
                                            <div>
                                                <CardTitle className="text-white text-lg">{p.display_name}</CardTitle>
                                                <CardDescription className="text-slate-500">
                                                    {p.price_monthly ? `$${p.price_monthly}/mo` : "Custom pricing"} · {p.currency}
                                                </CardDescription>
                                            </div>
                                        </div>
                                    </CardHeader>
                                    <CardContent>
                                        <p className="text-xs font-semibold text-slate-500 uppercase mb-3">
                                            {p.feature_count} Features
                                        </p>
                                        <div className="flex flex-wrap gap-1.5">
                                            {p.features.map(f => (
                                                <Badge
                                                    key={f}
                                                    variant="outline"
                                                    className="border-[#1E293B] text-slate-400 text-[10px] px-2 py-0.5"
                                                >
                                                    {f === "*" ? "All Features" : f.replace(/_/g, " ")}
                                                </Badge>
                                            ))}
                                        </div>
                                    </CardContent>
                                </Card>
                            );
                        })}

                        {plans.length === 0 && (
                            <div className="col-span-3 text-center py-12 text-slate-500">
                                No plans found. Click &quot;Seed Default Features&quot; to create them.
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}

function StatCard({ icon: Icon, label, value, sub, color }: {
    icon: any; label: string; value: string | number; sub: string; color: string;
}) {
    return (
        <Card className="bg-[#0F172A] border-[#1E293B]">
            <CardContent className="p-5">
                <div className="flex items-center justify-between">
                    <div>
                        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{label}</p>
                        <p className="text-3xl font-bold text-white mt-1">{value}</p>
                        <p className="text-xs text-slate-500 mt-1">{sub}</p>
                    </div>
                    <div className={`p-3 rounded-xl bg-black/20 ${color}`}>
                        <Icon className="h-6 w-6" />
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}
