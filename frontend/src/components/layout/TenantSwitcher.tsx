"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/context/AuthContext";
import api from "@/lib/api";
import {
    Select,
    SelectContent,
    SelectGroup,
    SelectItem,
    SelectLabel,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { Building2, Plus } from "lucide-react";

interface Tenant {
    id: string;
    name: string;
    slug: string;
    mode: string;
}

export default function TenantSwitcher() {
    const { user, switchTenant } = useAuth();
    const [tenants, setTenants] = useState<Tenant[]>([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        const fetchTenants = async () => {
            if (!user) return;
            try {
                const res = await api.get("/tenants");
                setTenants(res.data);
            } catch (err) {
                console.error("Failed to fetch tenants", err);
            }
        };
        fetchTenants();
    }, [user]);

    const currentTenant = tenants.find(t => user?.tenant_id === t.id) || tenants[0];

    const handleSwitch = async (tenantId: string) => {
        if (tenantId === "create_new") {
            // Redirect to create tenant page or open modal
            // TODO: Implement create tenant flow
            console.log("Create tenant clicked");
            return;
        }

        setLoading(true);
        try {
            await switchTenant(tenantId);
        } finally {
            setLoading(false);
        }
    };

    if (!user) return null;

    return (
        <Select
            value={user.tenant_id}
            onValueChange={handleSwitch}
            disabled={loading}
        >
            <SelectTrigger className="w-full h-12 bg-navy-900 border-navy-700 text-white hover:bg-navy-800 transition-colors focus:ring-gold-500">
                <div className="flex items-center gap-2 overflow-hidden text-left w-full">
                    <div className="h-6 w-6 rounded bg-navy-800 flex items-center justify-center border border-navy-600 shrink-0">
                        <Building2 className="h-3 w-3 text-gold-400" />
                    </div>
                    <div className="flex-1 overflow-hidden">
                        <SelectValue placeholder="Select Organization">
                            {currentTenant?.name || "Select Org"}
                        </SelectValue>
                    </div>
                </div>
            </SelectTrigger>
            <SelectContent className="bg-navy-900 border-navy-700 text-white">
                <SelectGroup>
                    <SelectLabel className="text-navy-400 text-xs uppercase tracking-wider pl-2">My Organizations</SelectLabel>
                    {tenants.map((tenant) => (
                        <SelectItem
                            key={tenant.id}
                            value={tenant.id}
                            className="cursor-pointer focus:bg-navy-800 focus:text-gold-400"
                        >
                            <span className="flex items-center gap-2">
                                <span>{tenant.name}</span>
                                <span className="text-xs text-navy-400 uppercase border border-navy-700 px-1 rounded ml-auto">
                                    {tenant.mode}
                                </span>
                            </span>
                        </SelectItem>
                    ))}
                </SelectGroup>
                {/* 
                <SelectGroup>
                     <SelectItem value="create_new" className="text-gold-400 font-medium cursor-pointer focus:bg-navy-800">
                        <span className="flex items-center gap-2">
                            <Plus className="h-3 w-3" /> Create Organization
                        </span>
                     </SelectItem>
                </SelectGroup>
                */}
            </SelectContent>
        </Select>
    );
}
