export const BASE_URL = process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

interface ApiOptions extends RequestInit {
    token?: string;
    body?: any;
}

export class ApiError extends Error {
    status: number;
    data: any;

    constructor(status: number, data: any) {
        super(`API Error: ${status}`);
        this.status = status;
        this.data = data;
    }
}

export async function apiFetch<T>(path: string, options: ApiOptions = {}): Promise<T> {
    const { token, body, headers, ...rest } = options;

    const isFormData = typeof FormData !== 'undefined' && body instanceof FormData;

    const config: RequestInit = {
        ...rest,
        headers: {
            // Don't set Content-Type for FormData — browser sets it with boundary
            ...(!isFormData ? { "Content-Type": "application/json" } : {}),
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
            ...(headers as any),
        },
    };

    if (body) {
        config.body = isFormData ? body : JSON.stringify(body);
    }

    // Ensure path starts with /
    const endpoint = path.startsWith("/") ? path : `/${path}`;
    const url = `${BASE_URL}${endpoint}`;

    const response = await fetch(url, config);

    let data;
    try {
        data = await response.json();
    } catch (e) {
        data = null;
    }

    if (!response.ok) {
        if (response.status === 401 && typeof window !== 'undefined') {
            // Token expired or invalid — redirect to login
            const currentPath = window.location.pathname;
            if (!currentPath.startsWith('/login') && !currentPath.startsWith('/register') && !currentPath.startsWith('/forgot')) {
                localStorage.removeItem('token');
                window.location.href = '/login';
                return undefined as any;
            }
        }
        // BUG-14 FIX: 403 (permission denied) no longer force-logs out the user
        throw new ApiError(response.status, data);
    }

    return data as T;
}

// Legacy support for AuthContext and other components
const api = {
    get: async <T = any>(path: string, config?: any) => {
        const token = localStorage.getItem("token");
        const data = await apiFetch<T>(path, { method: "GET", token: token || undefined, ...config });
        return { data };
    },
    post: async <T = any>(path: string, body?: any, config?: any) => {
        const token = localStorage.getItem("token");
        const data = await apiFetch<T>(path, { method: "POST", body, token: token || undefined, ...config });
        return { data };
    },
    put: async <T = any>(path: string, body?: any, config?: any) => {
        const token = localStorage.getItem("token");
        const data = await apiFetch<T>(path, { method: "PUT", body, token: token || undefined, ...config });
        return { data };
    },
    patch: async <T = any>(path: string, body?: any, config?: any) => {
        const token = localStorage.getItem("token");
        const data = await apiFetch<T>(path, { method: "PATCH", body, token: token || undefined, ...config });
        return { data };
    },
    delete: async <T = any>(path: string, config?: any) => {
        const token = localStorage.getItem("token");
        const data = await apiFetch<T>(path, { method: "DELETE", token: token || undefined, ...config });
        return { data };
    }
};

export { api };
export default api;
