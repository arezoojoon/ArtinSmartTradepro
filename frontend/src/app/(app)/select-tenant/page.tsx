"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
    type Tenant,
    getMyTenants,
    createTenant,
    switchTenant,
    getActiveTenantId
} from "@/lib/tenant";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Loader2, PlusCircle, Building2 } from "lucide-react";

export default function SelectTenantPage() {
    const router = useRouter();
    const [loading, setLoading] = useState(true);
    const [tenants, setTenants] = useState<Tenant[]>([]);
    const [newTenantName, setNewTenantName] = useState("");
    const [creating, setCreating] = useState(false);

    useEffect(() => {
        const init = async () => {
            const activeId = getActiveTenantId();
            const list = await getMyTenants();
            setTenants(list);
            setLoading(false);

            // If already has active tenant and it exists in list, redirect
            if (activeId && list.find(t => t.id === activeId)) {
                router.push("/dashboard");
            }
        };
        init();
    }, [router]);

    const handleCreate = async () => {
        if (!newTenantName.trim()) return;
        setCreating(true);
        try {
            const newTenant = await createTenant(newTenantName);
            // Automatically switch to it
            await switchTenant(newTenant.id); // Assuming response has id at top level or we refetch
            // Actually createTenant returns the Tenant object usually
            // Just to be safe, fetch list again or rely on response
            const list = await getMyTenants();
            const created = list.find(t => t.slug === newTenant.slug || t.name === newTenantName);
            if (created) {
                await switchTenant(created.id);
                router.push("/dashboard");
            }
        } catch (e) {
            console.error(e);
        } finally {
            setCreating(false);
        }
    };

    const handleSelect = async (id: string) => {
        await switchTenant(id);
        router.push("/dashboard");
    };

    if (loading) {
        return (
            <div className="flex h-screen items-center justify-center bg-[#071022] text-white">
                <Loader2 className="h-8 w-8 animate-spin text-[#f5a623]" />
            </div>
        );
    }

    return (
        <div className="flex min-h-screen items-center justify-center bg-[#071022] p-4 text-white">
            <Card className="w-full max-w-md border-white/10 bg-[#0B1B3A] text-white">
                <CardHeader>
                    <CardTitle className="text-2xl text-[#f5a623]">
                        {tenants.length === 0 ? "Welcome! Let's get started." : "Select Organization"}
                    </CardTitle>
                    <CardDescription className="text-white/60">
                        {tenants.length === 0
                            ? "Create your first organization to begin trading."
                            : "Choose an organization to continue."}
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                    {tenants.length > 0 && (
                        <div className="space-y-2">
                            {tenants.map((t) => (
                                <button
                                    key={t.id}
                                    onClick={() => handleSelect(t.id)}
                                    className="flex w-full items-center justify-between rounded-xl border border-white/10 p-4 hover:border-[#f5a623]/50 hover:bg-white/5 transition-all"
                                >
                                    <div className="flex items-center gap-3">
                                        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-white/10 text-white">
                                            <Building2 className="h-5 w-5" />
                                        </div>
                                        <div className="text-left">
                                            <div className="font-medium text-white">{t.name}</div>
                                            <div className="text-xs text-white/50 capitalize">{t.role}</div>
                                        </div>
                                    </div>
                                    <div className="text-xs text-white/40">Select →</div>
                                </button>
                            ))}

                            <div className="relative my-4">
                                <div className="absolute inset-0 flex items-center">
                                    <span className="w-full border-t border-white/10" />
                                </div>
                                <div className="relative flex justify-center text-xs uppercase">
                                    <span className="bg-[#0B1B3A] px-2 text-white/40">Or create new</span>
                                </div>
                            </div>
                        </div>
                    )}

                    <div className="space-y-3">
                        <div className="space-y-1">
                            <label className="text-sm font-medium leading-none text-white/80">
                                Organization Name
                            </label>
                            <Input
                                value={newTenantName}
                                onChange={(e) => setNewTenantName(e.target.value)}
                                placeholder="e.g. Global Exports Ltd."
                                className="bg-white/5 border-white/10 text-white"
                            />
                        </div>
                        <Button
                            onClick={handleCreate}
                            disabled={creating || !newTenantName.trim()}
                            className="w-full bg-[#f5a623] text-[#0B1B3A] hover:bg-[#f5a623]/90"
                        >
                            {creating ? (
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            ) : (
                                <PlusCircle className="mr-2 h-4 w-4" />
                            )}
                            Create Organization
                        </Button>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
