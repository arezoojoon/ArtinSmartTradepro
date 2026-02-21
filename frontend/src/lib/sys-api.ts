/**
 * Phase 6 — Sys Admin API Client
 * Uses sessionStorage['sys_token'] (separate from tenant token)
 */

const SYS_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

function getSysToken(): string | null {
    if (typeof window === 'undefined') return null;
    return sessionStorage.getItem('sys_token');
}

async function sysRequest<T = unknown>(
    path: string,
    options: RequestInit = {}
): Promise<T> {
    const token = getSysToken();
    const res = await fetch(`${SYS_BASE}${path}`, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
            ...(options.headers || {}),
        },
    });

    if (res.status === 401) {
        if (typeof window !== 'undefined') {
            sessionStorage.removeItem('sys_token');
            window.location.href = '/sys/login';
        }
        throw new Error('Unauthorized');
    }

    if (!res.ok) {
        const err = await res.json().catch(() => ({ error: { message: res.statusText } }));
        throw new Error(err?.error?.message || err?.detail || res.statusText);
    }

    return res.json();
}

// ─── Auth ─────────────────────────────────────────────────────────────────────

export async function sysLogin(email: string, password: string) {
    const data = await sysRequest<{
        access_token: string;
        sys_admin_id: string;
        email: string;
        name: string;
    }>('/sys/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
    });
    sessionStorage.setItem('sys_token', data.access_token);
    return data;
}

export async function sysGetMe() {
    return sysRequest<{ id: string; email: string; name: string }>('/sys/me');
}

export function sysLogout() {
    sessionStorage.removeItem('sys_token');
    window.location.href = '/sys/login';
}

// ─── Tenants ──────────────────────────────────────────────────────────────────

export async function listTenants(q = '', limit = 50, offset = 0) {
    const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
    if (q) params.set('q', q);
    return sysRequest<{ total: number; items: any[] }>(`/sys/tenants?${params}`);
}

export async function getTenant(tenantId: string) {
    return sysRequest<any>(`/sys/tenants/${tenantId}`);
}

export async function suspendTenant(tenantId: string) {
    return sysRequest(`/sys/tenants/${tenantId}/suspend`, { method: 'POST' });
}

export async function restoreTenant(tenantId: string) {
    return sysRequest(`/sys/tenants/${tenantId}/restore`, { method: 'POST' });
}

export async function impersonateTenant(tenantId: string) {
    return sysRequest<{ impersonation_token: string; expires_in_minutes: number }>(
        `/sys/tenants/${tenantId}/impersonate`,
        { method: 'POST' }
    );
}

export async function setTenantSubscription(tenantId: string, planCode: string) {
    return sysRequest(`/sys/tenants/${tenantId}/subscription`, {
        method: 'POST',
        body: JSON.stringify({ plan_code: planCode }),
    });
}

export async function getTenantUsers(tenantId: string) {
    return sysRequest<any[]>(`/sys/tenants/${tenantId}/users`);
}

export async function getTenantUsage(tenantId: string) {
    return sysRequest<any>(`/sys/tenants/${tenantId}/usage`);
}

// ─── Plans ────────────────────────────────────────────────────────────────────

export async function listPlans() {
    return sysRequest<any[]>('/sys/plans');
}

export async function upsertPlan(data: {
    code: string;
    name: string;
    description?: string;
    monthly_price_usd?: number;
    features: Record<string, any>;
    limits: Record<string, any>;
}) {
    return sysRequest('/sys/plans', { method: 'POST', body: JSON.stringify(data) });
}

// ─── Whitelabel ───────────────────────────────────────────────────────────────

export async function listWlDomains() {
    return sysRequest<any[]>('/sys/whitelabel/domains');
}

export async function activateDomain(domainId: string) {
    return sysRequest(`/sys/whitelabel/domains/${domainId}/activate`, { method: 'POST' });
}

// ─── Audit ────────────────────────────────────────────────────────────────────

export async function listAuditLogs(params: {
    tenant_id?: string;
    action?: string;
    limit?: number;
    offset?: number;
}) {
    const p = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => v != null && p.set(k, String(v)));
    return sysRequest<{ total: number; items: any[] }>(`/sys/audit?${p}`);
}

// ─── DLQ ──────────────────────────────────────────────────────────────────────

export async function listDlq(queueType?: string) {
    const p = queueType ? `?queue_type=${queueType}` : '';
    return sysRequest<{ total: number; items: any[] }>(`/sys/queues/dlq${p}`);
}

export async function retryDlqItem(itemId: string, queueType: string) {
    return sysRequest('/sys/queues/dlq/retry', {
        method: 'POST',
        body: JSON.stringify({ item_id: itemId, queue_type: queueType }),
    });
}

// ─── Prompt Ops ───────────────────────────────────────────────────────────────

export async function listPromptFamilies() {
    return sysRequest<any[]>('/sys/prompts/families');
}

export async function createPromptFamily(data: { name: string; description?: string; category?: string }) {
    return sysRequest('/sys/prompts/families', { method: 'POST', body: JSON.stringify(data) });
}

export async function listPromptVersions(familyId: string) {
    return sysRequest<any[]>(`/sys/prompts/families/${familyId}/versions`);
}

export async function createPromptVersion(familyId: string, data: {
    model_target: string;
    system_prompt: string;
    user_prompt_template: string;
    guardrails: Record<string, boolean>;
}) {
    return sysRequest(`/sys/prompts/families/${familyId}/versions`, {
        method: 'POST',
        body: JSON.stringify(data),
    });
}

export async function approveVersion(versionId: string) {
    return sysRequest(`/sys/prompts/versions/${versionId}/approve`, { method: 'POST' });
}

export async function deprecateVersion(versionId: string) {
    return sysRequest(`/sys/prompts/versions/${versionId}/deprecate`, { method: 'POST' });
}

export async function listPromptRuns(params: {
    tenant_id?: string;
    family?: string;
    status?: string;
    limit?: number;
}) {
    const p = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => v != null && p.set(k, String(v)));
    return sysRequest<{ total: number; items: any[] }>(`/sys/prompts/runs?${p}`);
}
