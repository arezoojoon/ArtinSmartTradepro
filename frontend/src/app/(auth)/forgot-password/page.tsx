"use client";

import { useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import api from "@/lib/api";

export default function ForgotPasswordPage() {
    const [email, setEmail] = useState("");
    const [loading, setLoading] = useState(false);
    const [submitted, setSubmitted] = useState(false);
    const [error, setError] = useState("");

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError("");

        try {
            await api.post("/auth/forgot-password", { email });
            setSubmitted(true);
        } catch (err: any) {
            setError(err.response?.data?.detail || "Failed to send reset email");
        } finally {
            setLoading(false);
        }
    };

    if (submitted) {
        return (
            <Card className="border-navy-800 bg-navy-900 text-white">
                <CardHeader>
                    <CardTitle className="text-center text-xl text-gold-400">Check Your Email</CardTitle>
                    <CardDescription className="text-center text-gray-400">
                        If an account exists for {email}, you will receive a password reset link shortly.
                    </CardDescription>
                </CardHeader>
                <CardFooter className="justify-center">
                    <Link href="/login" className="text-sm text-gold-400 hover:text-gold-300">
                        Back to Login
                    </Link>
                </CardFooter>
            </Card>
        );
    }

    return (
        <Card className="border-navy-800 bg-navy-900 text-white">
            <CardHeader>
                <CardTitle className="text-center text-xl text-gold-400">Reset Password</CardTitle>
                <CardDescription className="text-center text-gray-400">
                    Enter your email address and we'll send you a link to reset your password.
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
                    {error && <p className="text-sm text-red-500 text-center">{error}</p>}
                    <Button type="submit" className="w-full bg-gold-500 text-navy-900 hover:bg-gold-600 font-bold" disabled={loading}>
                        {loading ? "Sending Link..." : "Send Reset Link"}
                    </Button>
                </form>
            </CardContent>
            <CardFooter className="justify-center">
                <Link href="/login" className="text-sm text-gold-400 hover:text-gold-300">
                    Back to Login
                </Link>
            </CardFooter>
        </Card>
    );
}
