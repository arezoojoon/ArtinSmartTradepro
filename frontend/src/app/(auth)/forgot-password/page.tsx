"use client";

import { useState } from "react";
import Link from "next/link";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowLeft, Mail, CheckCircle2 } from "lucide-react";

export default function ForgotPasswordPage() {
    const [email, setEmail] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [isSubmitted, setIsSubmitted] = useState(false);
    const [error, setError] = useState("");

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError("");

        try {
            await api.post("/auth/forgot-password", { email });
            setIsSubmitted(true);
        } catch (err: any) {
            console.error(err);
            // Even if failed, for security we might want to say sent, but here we show error if it's strictly technical
            // If it's 404, the backend usually hides it (returns 200). 
            // If network error:
            setError(err.response?.data?.detail || "Something went wrong. Please try again.");
        } finally {
            setIsLoading(false);
        }
    };

    if (isSubmitted) {
        return (
            <Card className="w-full max-w-md bg-navy-900 border-navy-800 shadow-2xl">
                <CardHeader className="text-center">
                    <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-green-900/50 border border-green-700">
                        <CheckCircle2 className="h-8 w-8 text-green-400" />
                    </div>
                    <CardTitle className="text-2xl font-bold text-white">Check your email</CardTitle>
                    <CardDescription className="text-gray-400">
                        We have sent a password reset link to <span className="font-medium text-white">{email}</span>
                    </CardDescription>
                </CardHeader>
                <CardFooter className="flex flex-col space-y-4">
                    <Link href="/login" className="w-full">
                        <Button variant="outline" className="w-full border-navy-700 hover:bg-navy-800 hover:text-white">
                            <ArrowLeft className="mr-2 h-4 w-4" /> Back to Login
                        </Button>
                    </Link>
                </CardFooter>
            </Card>
        );
    }

    return (
        <Card className="w-full max-w-md bg-navy-900 border-navy-800 shadow-2xl">
            <CardHeader className="space-y-1">
                <CardTitle className="text-2xl font-bold text-white">Forgot password?</CardTitle>
                <CardDescription className="text-gray-400">
                    Enter your email address and we'll send you a link to reset your password.
                </CardDescription>
            </CardHeader>
            <CardContent>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="space-y-2">
                        <Label htmlFor="email" className="text-gray-300">Email</Label>
                        <div className="relative">
                            <Mail className="absolute left-3 top-3 h-4 w-4 text-gray-500" />
                            <Input
                                id="email"
                                type="email"
                                placeholder="name@example.com"
                                className="pl-9 bg-navy-950 border-navy-700 text-white placeholder:text-gray-600 focus-visible:ring-gold-500"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                            />
                        </div>
                    </div>

                    {error && (
                        <div className="p-3 text-sm text-red-400 bg-red-900/20 border border-red-900 rounded-md">
                            {error}
                        </div>
                    )}

                    <Button
                        type="submit"
                        className="w-full bg-gold-500 text-navy-900 hover:bg-gold-600 font-bold"
                        disabled={isLoading}
                    >
                        {isLoading ? "Sending Link..." : "Send Reset Link"}
                    </Button>
                </form>
            </CardContent>
            <CardFooter>
                <Link href="/login" className="w-full flex items-center justify-center text-sm text-gray-400 hover:text-gold-400">
                    <ArrowLeft className="mr-2 h-4 w-4" /> Back to Login
                </Link>
            </CardFooter>
        </Card>
    );
}
