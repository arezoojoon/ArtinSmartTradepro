"use client";

import { useState, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import api from "@/lib/api";

function ResetPasswordForm() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const token = searchParams.get("token");

    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError("");

        if (password !== confirmPassword) {
            setError("Passwords do not match");
            setLoading(false);
            return;
        }

        if (password.length < 10) {
            setError("Password must be at least 10 characters long");
            setLoading(false);
            return;
        }

        if (!token) {
            setError("Missing reset token");
            setLoading(false);
            return;
        }

        try {
            await api.post("/auth/reset-password", { token, password });
            setSuccess(true);
            setTimeout(() => {
                router.push("/login");
            }, 3000);
        } catch (err: any) {
            setError(err.response?.data?.detail || "Failed to reset password");
        } finally {
            setLoading(false);
        }
    };

    if (!token) {
        return (
            <Card className="border-navy-800 bg-navy-900 text-white">
                <CardHeader>
                    <CardTitle className="text-center text-xl text-red-400">Invalid Link</CardTitle>
                    <CardDescription className="text-center text-gray-400">
                        This password reset link is invalid or has expired.
                    </CardDescription>
                </CardHeader>
                <CardFooter className="justify-center">
                    <Link href="/forgot-password" className="text-sm text-gold-400 hover:text-gold-300">
                        Request a new link
                    </Link>
                </CardFooter>
            </Card>
        );
    }

    if (success) {
        return (
            <Card className="border-navy-800 bg-navy-900 text-white">
                <CardHeader>
                    <CardTitle className="text-center text-xl text-green-400">Password Reset Successful</CardTitle>
                    <CardDescription className="text-center text-gray-400">
                        Your password has been successfully updated. Redirecting to login...
                    </CardDescription>
                </CardHeader>
                <CardFooter className="justify-center">
                    <Link href="/login" className="text-sm text-gold-400 hover:text-gold-300">
                        Go to Login
                    </Link>
                </CardFooter>
            </Card>
        );
    }

    return (
        <Card className="border-navy-800 bg-navy-900 text-white">
            <CardHeader>
                <CardTitle className="text-center text-xl text-gold-400">Set New Password</CardTitle>
                <CardDescription className="text-center text-gray-400">
                    Create a new, strong password for your account.
                </CardDescription>
            </CardHeader>
            <CardContent>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="space-y-2">
                        <Label htmlFor="password">New Password</Label>
                        <Input
                            id="password"
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="border-navy-700 bg-navy-800 text-white placeholder:text-gray-500 focus:border-gold-400 focus:ring-gold-400"
                            required
                        />
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="confirmPassword">Confirm Password</Label>
                        <Input
                            id="confirmPassword"
                            type="password"
                            value={confirmPassword}
                            onChange={(e) => setConfirmPassword(e.target.value)}
                            className="border-navy-700 bg-navy-800 text-white placeholder:text-gray-500 focus:border-gold-400 focus:ring-gold-400"
                            required
                        />
                    </div>
                    {error && <p className="text-sm text-red-500 text-center">{error}</p>}
                    <Button type="submit" className="w-full bg-gold-500 text-navy-900 hover:bg-gold-600 font-bold" disabled={loading}>
                        {loading ? "Resetting..." : "Reset Password"}
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

export default function ResetPasswordPage() {
    return (
        <Suspense fallback={<div className="text-center text-white">Loading...</div>}>
            <ResetPasswordForm />
        </Suspense>
    );
}
