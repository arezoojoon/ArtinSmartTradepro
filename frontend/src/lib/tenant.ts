import { apiFetch } from "./api";
import { getAccessToken } from "./auth";

// Cache key for active tenant ID (local preference)
const ACTIVE_TENANT_KEY = "artin_active_tenant_id";

export interface Tenant {
    id: string;
    name: string;
    slug: string;
    plan: string;
    role: string;
    created_at: string;
}

export interface TenantListResponse {
    tenants: {
        tenant_id: string;
        tenant_name: string;
        role: string;
        created_at: string;
    }[];
    current_tenant_id: string | null;
}

export async function getMyTenants(): Promise<Tenant[]> {
    const token = getAccessToken();
    if (!token) return [];

    try {
        const data = await apiFetch<TenantListResponse>("/tenants", { token });
        // Map response to clean Tenant objects, ensuring we capture the ID correctly
        // The list response has `tenant_id`, `tenant_name` etc.
        return data.tenants.map(t => ({
            id: t.tenant_id,
            name: t.tenant_name,
            slug: t.tenant_name.toLowerCase().replace(/\s+/g, '-'), // fallback if slug not in list response
            plan: "professional", // fallback
            role: t.role,
            created_at: t.created_at
        }));
    } catch (error) {
        console.error("Failed to fetch tenants:", error);
        return [];
    }
}

export async function createTenant(name: string): Promise<any> {
    const token = getAccessToken();
    if (!token) throw new Error("Not authenticated");

    return apiFetch("/tenants", {
        method: "POST",
        token,
        body: { name, plan: "professional" }
    });
}

export async function switchTenant(tenantId: string): Promise<boolean> {
    const token = getAccessToken();
    if (!token) return false;

    try {
        await apiFetch(`/tenants/${tenantId}/switch`, {
            method: "POST",
            token
        });
        setActiveTenantId(tenantId);
        return true;
    } catch (error) {
        console.error("Failed to switch tenant:", error);
        return false;
    }
}

export function getActiveTenantId(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem(ACTIVE_TENANT_KEY);
}

// Internal helper to update local cache
function setActiveTenantId(id: string) {
    if (typeof window === "undefined") return;
    localStorage.setItem(ACTIVE_TENANT_KEY, id);
}

export function clearActiveTenantId() {
    if (typeof window === "undefined") return;
    localStorage.removeItem(ACTIVE_TENANT_KEY);
}
