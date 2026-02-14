"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";

type UserRole = "super_admin" | "admin" | "user";
type TenantMode = "buyer" | "seller" | "hybrid";
type UserPersona = "trader" | "logistics" | "finance" | "admin";

interface Tenant {
    id: string;
    name: string;
    mode: TenantMode;
    is_active: boolean;
}

interface User {
    id: string;
    email: string;
    full_name: string;
    role: UserRole;
    tenant_id?: string;
    tenant?: Tenant;
    persona?: UserPersona;
}

interface AuthContextType {
    user: User | null;
    loading: boolean;
    isAuthenticated: boolean;
    login: (token: string, refresh_token: string) => Promise<void>;
    logout: () => void;
    switchTenant: (tenantId: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
    user: null,
    loading: true,
    isAuthenticated: false,
    login: async () => { },
    logout: () => { },
    switchTenant: async () => { },
});

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);
    const router = useRouter();

    useEffect(() => {
        checkAuth();
    }, []);

    const checkAuth = async () => {
        const token = localStorage.getItem("token");
        if (!token) {
            setLoading(false);
            return;
        }

        try {
            // Fetch comprehensive user profile
            // This endpoint must return user + tenant details
            const userData = await api.get("/users/me");
            setUser(userData.data);
        } catch (error) {
            console.error("Auth check failed:", error);
            // If 401, clear token
            localStorage.removeItem("token");
            localStorage.removeItem("refresh_token");
        } finally {
            setLoading(false);
        }
    };

    const login = async (token: string, refresh_token: string) => {
        localStorage.setItem("token", token);
        localStorage.setItem("refresh_token", refresh_token);

        try {
            // Fetch user data immediately to decide redirect
            const response = await api.get("/users/me");
            const userData = response.data;
            setUser(userData);

            // V3 Redirect Logic
            const mode = userData.tenant?.mode || "hybrid";
            console.log(`[Auth] Redirecting for mode: ${mode}`);

            if (mode === "buyer") {
                router.push("/buyer");
            } else if (mode === "seller") {
                router.push("/seller");
            } else {
                router.push("/dashboard");
            }

        } catch (error) {
            console.error("Login profile fetch failed:", error);
            // Fallback
            router.push("/dashboard");
        }
    };

    const logout = async () => {
        try {
            await api.post("/auth/logout");
        } catch (e) {
            console.error("Logout API failed", e);
        }
        localStorage.removeItem("token");
        localStorage.removeItem("refresh_token");
        setUser(null);
        router.push("/login");
    };

    const switchTenant = async (tenantId: string) => {
        setLoading(true);
        try {
            const res = await api.post(`/tenants/${tenantId}/switch`);
            const { access_token } = res.data;

            // Store new token (scoped to new tenant)
            localStorage.setItem("token", access_token);

            // Refresh User
            const userRes = await api.get("/users/me");
            const userData = userRes.data;
            setUser(userData);

            // Redirect
            const mode = userData.tenant?.mode || "hybrid";
            console.log(`[Auth] Switched to tenant mode: ${mode}`);

            if (mode === "buyer") {
                router.push("/buyer");
            } else if (mode === "seller") {
                router.push("/seller");
            } else {
                router.push("/dashboard");
            }
        } catch (error) {
            console.error("Switch tenant failed", error);
            // Stay put or show error toast
        } finally {
            setLoading(false);
        }
    };

    return (
        <AuthContext.Provider value={{ user, loading, isAuthenticated: !!user, login, logout, switchTenant }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);
