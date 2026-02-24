"use client";

import { useState } from "react";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Eye, EyeOff } from "lucide-react";
import api from "@/lib/api";

export default function LoginPage() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const { login } = useAuth();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError("");

        try {
            // Send plain object as API expects JSON
            const payload = {
                email,
                password
            };

            const response = await api.post("/auth/login", payload);
            login(response.data.access_token, response.data.refresh_token);
        } catch (err: any) {
            setError(err?.data?.error?.message || err?.data?.detail || err?.message || "Failed to login");
        } finally {
            setLoading(false);
        }
    };

    return (
        <Card className="border-[#1e3a5f] bg-[#0e1e33] text-white">
            <CardHeader>
                <CardTitle className="text-center text-xl text-[#f5a623]">Sign In</CardTitle>
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
                            <Link href="/forgot-password" className="text-xs text-[#f5a623] hover:text-gold-300">
                                Forgot password?
                            </Link>
                        </div>
                        <div className="relative">
                            <Input
                                id="password"
                                type={showPassword ? "text" : "password"}
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="border-navy-700 bg-navy-800 text-white placeholder:text-gray-500 focus:border-gold-400 focus:ring-gold-400 pr-10"
                                required
                            />
                            <button
                                type="button"
                                onClick={() => setShowPassword(!showPassword)}
                                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white focus:outline-none"
                            >
                                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                            </button>
                        </div>
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
                    <Link href="/register" className="text-[#f5a623] hover:text-gold-300">
                        Sign up
                    </Link>
                </p>
            </CardFooter>
        </Card>
    );
}
