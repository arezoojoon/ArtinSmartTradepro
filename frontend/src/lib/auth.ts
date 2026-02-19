import { redirect } from "next/navigation";

const TOKEN_KEY = "token"; // Matching the key used in login page

export function getAccessToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem(TOKEN_KEY);
}

export function setAccessToken(token: string) {
    if (typeof window === "undefined") return;
    localStorage.setItem(TOKEN_KEY, token);
}

export function removeAccessToken() {
    if (typeof window === "undefined") return;
    localStorage.removeItem(TOKEN_KEY);
}

export function requireAuth() {
    const token = getAccessToken();
    if (!token) {
        redirect("/login");
    }
    return token;
}

export function isAuthenticated(): boolean {
    return !!getAccessToken();
}
