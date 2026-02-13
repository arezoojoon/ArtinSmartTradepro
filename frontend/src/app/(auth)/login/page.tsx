"use client";

import { useState } from "react";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import api from "@/lib/api";

export default function LoginPage() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const { login } = useAuth();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError("");

        try {
            // Create form data as expected by OAuth2PasswordRequestForm
            const formData = new FormData();
            formData.append("username", email);
            formData.append("password", password);

            const response = await api.post("/auth/login", formData);
            login(response.data.access_token, response.data.refresh_token);
        } catch (err: any) {
            setError(err.response?.data?.detail || "Failed to login");
        } finally {
            setLoading(false);
        }
    };

    return (
        <Card className="border-navy-800 bg-navy-900 text-white">
            <CardHeader>
                <CardTitle className="text-center text-xl text-gold-400">Sign In</CardTitle>
                <CardDescription className="text-center text-gray-400">
                    Access your AI Trading Dashboard
                </CardDescription>
            </CardHeader>
            <CardContent>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="space-y-2">
                        <Label htmlFor="email">Email</Label>
                        <Input
                            id="email"
                            type="email"
                            placeholder="name@company.com"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className="border-navy-700 bg-navy-800 text-white placeholder:text-gray-500 focus:border-gold-400 focus:ring-gold-400"
                            required
                        />
                    </div>
                    <div className="space-y-2">
                        <div className="flex items-center justify-between">
                            <Label htmlFor="password">Password</Label>
                            <Link href="/forgot-password" className="text-xs text-gold-400 hover:text-gold-300">
                                Forgot password?
                            </Link>
                        </div>
                        <Input
                            id="password"
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="border-navy-700 bg-navy-800 text-white placeholder:text-gray-500 focus:border-gold-400 focus:ring-gold-400"
                            required
                        />
                    </div>
                    {error && <p className="text-sm text-red-500 text-center">{error}</p>}
                    <Button type="submit" className="w-full bg-gold-500 text-navy-900 hover:bg-gold-600 font-bold" disabled={loading}>
                        {loading ? "Signing in..." : "Sign In"}
                    </Button>
                </form>
            </CardContent>
            <CardFooter className="justify-center">
                <p className="text-sm text-gray-400">
                    Don't have an account?{" "}
                    <Link href="/register" className="text-gold-400 hover:text-gold-300">
                        Sign up
                    </Link>
                </p>
            </CardFooter>
        </Card>
    );
}
