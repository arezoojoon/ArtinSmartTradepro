"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";

interface User {
    email: string;
    full_name?: string;
    role: string;
    tenant_id?: number;
}

interface AuthContextType {
    user: User | null;
    login: (token: string) => void;
    logout: () => void;
    loading: boolean;
    isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType>({
    user: null,
    login: () => { },
    logout: () => { },
    loading: true,
    isAuthenticated: false,
});

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);
    const router = useRouter();

    useEffect(() => {
        const token = localStorage.getItem("token");
        if (token) {
            // In a real app, verify token validity or fetch user profile
            // For now, decode if possible or just assume valid until 401
            // simplified:
            setUser({ email: "user@example.com", role: "user" }); // Placeholder until profile fetch implemented
        }
        setLoading(false);
    }, []);

    const login = (token: string) => {
        localStorage.setItem("token", token);
        // Decode token to get user info
        setUser({ email: "user@example.com", role: "user" });
        router.push("/dashboard");
    };

    const logout = () => {
        localStorage.removeItem("token");
        setUser(null);
        router.push("/login");
    };

    return (
        <AuthContext.Provider value={{ user, login, logout, loading, isAuthenticated: !!user }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);
