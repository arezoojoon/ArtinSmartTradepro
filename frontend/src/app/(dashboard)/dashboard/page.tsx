"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getActiveTenantId, getMyTenants, type Tenant } from "@/lib/tenant";

export default function DashboardPage() {
    const router = useRouter();
    const [tenant, setTenant] = useState<Tenant | null>(null);

    useEffect(() => {
        const activeId = getActiveTenantId();
        if (!activeId) {
            router.push("/select-tenant");
            return;
        }

        // Hydrate tenant info (optional, or just rely on ID)
        getMyTenants().then(list => {
            const found = list.find(t => t.id === activeId);
            if (found) setTenant(found);
        });
    }, [router]);

    return (
        <div className="p-4 md:p-8 space-y-8">
            <div>
                <h1 className="text-3xl font-bold text-white">Dashboard</h1>
                <p className="text-white/60">
                    Overview for <span className="text-[#D4AF37]">{tenant?.name || "..."}</span>
                </p>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                {[
                    { label: "Active Deals", value: "0", desc: "No deals in pipeline" },
                    { label: "New Leads", value: "0", desc: "Start Hunter to find leads" },
                    { label: "Pending Tasks", value: "0", desc: "Inbox is clear" },
                    { label: "Revenue", value: "$0.00", desc: "No successful trades yet" },
                ].map((item) => (
                    <div
                        key={item.label}
                        className="rounded-xl border border-white/10 bg-white/5 p-6"
                    >
                        <div className="text-sm font-medium text-white/50">{item.label}</div>
                        <div className="mt-2 text-2xl font-bold text-white">{item.value}</div>
                        <div className="mt-1 text-xs text-white/40">{item.desc}</div>
                    </div>
                ))}
            </div>

            <div className="rounded-xl border border-white/10 bg-white/5 p-8 text-center bg-[url('/grid.svg')]">
                <h3 className="text-lg font-medium text-white">Connect Data Sources</h3>
                <p className="mt-2 text-sm text-white/60 max-w-md mx-auto">
                    Your dashboard is empty. Start by using the Hunter tool to find leads or import your existing contacts to populate this view.
                </p>
            </div>
        </div>
    );
}
