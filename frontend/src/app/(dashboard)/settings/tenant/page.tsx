"use client";

import { useEffect, useState } from "react";
import { getActiveTenantId, getMyTenants, type Tenant } from "@/lib/tenant";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function TenantSettingsPage() {
    const [tenant, setTenant] = useState<Tenant | null>(null);

    useEffect(() => {
        const activeId = getActiveTenantId();
        if (activeId) {
            getMyTenants().then(list => {
                const found = list.find(t => t.id === activeId);
                if (found) setTenant(found);
            });
        }
    }, []);

    if (!tenant) return <div className="p-8 text-white">Loading...</div>;

    return (
        <div className="p-4 md:p-8 space-y-8 max-w-2xl text-white">
            <div>
                <h1 className="text-2xl font-bold">Organization Settings</h1>
                <p className="text-white/60">Manage your organization details.</p>
            </div>

            <div className="space-y-6">
                <div className="grid gap-2">
                    <Label>Organization ID</Label>
                    <div className="font-mono text-sm text-white/40 bg-white/5 p-2 rounded">
                        {tenant.id}
                    </div>
                </div>

                <div className="grid gap-2">
                    <Label>Name</Label>
                    <Input value={tenant.name} disabled className="bg-white/5 border-white/10" />
                </div>

                <div className="grid gap-2">
                    <Label>Your Role</Label>
                    <div className="capitalize text-white/80">{tenant.role}</div>
                </div>

                <div className="pt-4 border-t border-white/10">
                    <h3 className="text-lg font-medium mb-4">Danger Zone</h3>
                    <Button variant="destructive" disabled>
                        Delete Organization (Coming Soon)
                    </Button>
                </div>
            </div>
        </div>
    );
}
