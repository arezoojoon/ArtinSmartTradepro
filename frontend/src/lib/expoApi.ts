/**
 * Expo API Abstraction Layer
 * 
 * All Acquisition / Expo pages should use this module instead of
 * importing from `@/lib/api` directly.
 * 
 * Right now the Expo backend is a **separate service** running on its
 * own port / URL.  This adapter gives us a single place to:
 *   1. Swap the base URL when we later merge backends.
 *   2. Translate between the Expo auth model (Zustand token in
 *      `auth-storage`) and the main platform token (localStorage `token`).
 *   3. Cache / transform responses if needed.
 *
 * Environment variable:
 *   NEXT_PUBLIC_EXPO_API_URL — e.g. "http://localhost:8001/api"
 *   Falls back to the main API URL if not set.
 */

import { ApiError } from "@/lib/api";

export const EXPO_BASE_URL =
    process.env.NEXT_PUBLIC_EXPO_API_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    "http://localhost:8000/api/v1";

interface ExpoApiOptions extends RequestInit {
    body?: any;
}

/** Low-level fetch wrapper for the Expo service. */
async function expoFetch<T>(path: string, options: ExpoApiOptions = {}): Promise<T> {
    const { body, headers, ...rest } = options;
    const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
    const isFormData = typeof FormData !== "undefined" && body instanceof FormData;

    const config: RequestInit = {
        ...rest,
        headers: {
            ...(!isFormData ? { "Content-Type": "application/json" } : {}),
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
            ...(headers as Record<string, string>),
        },
    };

    if (body) {
        config.body = isFormData ? body : JSON.stringify(body);
    }

    const endpoint = path.startsWith("/") ? path : `/${path}`;
    const response = await fetch(`${EXPO_BASE_URL}${endpoint}`, config);

    let data: any;
    try {
        data = await response.json();
    } catch {
        data = null;
    }

    if (!response.ok) {
        if (response.status === 401 && typeof window !== "undefined") {
            const cur = window.location.pathname;
            if (!cur.startsWith("/login") && !cur.startsWith("/register")) {
                localStorage.removeItem("token");
                window.location.href = "/login";
                return undefined as any;
            }
        }
        throw new ApiError(response.status, data);
    }

    return data as T;
}

// ── Convenience wrapper matching the main `api` shape ──
const expoApi = {
    get: async <T = any>(path: string, config?: any) => {
        const data = await expoFetch<T>(path, { method: "GET", ...config });
        return { data };
    },
    post: async <T = any>(path: string, body?: any, config?: any) => {
        const data = await expoFetch<T>(path, { method: "POST", body, ...config });
        return { data };
    },
    put: async <T = any>(path: string, body?: any, config?: any) => {
        const data = await expoFetch<T>(path, { method: "PUT", body, ...config });
        return { data };
    },
    patch: async <T = any>(path: string, body?: any, config?: any) => {
        const data = await expoFetch<T>(path, { method: "PATCH", body, ...config });
        return { data };
    },
    delete: async <T = any>(path: string, config?: any) => {
        const data = await expoFetch<T>(path, { method: "DELETE", ...config });
        return { data };
    },
};

export { expoApi };
export default expoApi;
