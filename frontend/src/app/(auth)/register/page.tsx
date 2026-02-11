"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import api from "@/lib/api";

export default function RegisterPage() {
    const [formData, setFormData] = useState({
        full_name: "",
        email: "",
        password: "",
        confirmPassword: "",
        companyName: ""
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const router = useRouter();

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setFormData({ ...formData, [e.target.id]: e.target.value });
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (formData.password !== formData.confirmPassword) {
            setError("Passwords do not match");
            return;
        }
        setLoading(true);
        setError("");

        try {
            await api.post("/auth/register", {
                email: formData.email,
                password: formData.password,
                full_name: formData.full_name,
                role: "user", // Default role
                company_name: formData.companyName // Passed but might need backend update to handle tenant creation
            });
            router.push("/login?registered=true");
        } catch (err: any) {
            setError(err.response?.data?.detail || "Failed to register");
        } finally {
            setLoading(false);
        }
    };

    return (
        <Card className="border-navy-800 bg-navy-900 text-white">
            <CardHeader>
                <CardTitle className="text-center text-xl text-gold-400">Create Account</CardTitle>
                <CardDescription className="text-center text-gray-400">
                    Start your AI Trading Journey
                </CardDescription>
            </CardHeader>
            <CardContent>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="space-y-2">
                        <Label htmlFor="full_name">Full Name</Label>
                        <Input
                            id="full_name"
                            value={formData.full_name}
                            onChange={handleChange}
                            className="border-navy-700 bg-navy-800 text-white focus:border-gold-400 focus:ring-gold-400"
                            required
                        />
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="companyName">Company Name</Label>
                        <Input
                            id="companyName"
                            value={formData.companyName}
                            onChange={handleChange}
                            className="border-navy-700 bg-navy-800 text-white focus:border-gold-400 focus:ring-gold-400"
                            required
                        />
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="email">Email</Label>
                        <Input
                            id="email"
                            type="email"
                            value={formData.email}
                            onChange={handleChange}
                            className="border-navy-700 bg-navy-800 text-white focus:border-gold-400 focus:ring-gold-400"
                            required
                        />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label htmlFor="password">Password</Label>
                            <Input
                                id="password"
                                type="password"
                                value={formData.password}
                                onChange={handleChange}
                                className="border-navy-700 bg-navy-800 text-white focus:border-gold-400 focus:ring-gold-400"
                                required
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="confirmPassword">Confirm</Label>
                            <Input
                                id="confirmPassword"
                                type="password"
                                value={formData.confirmPassword}
                                onChange={handleChange}
                                className="border-navy-700 bg-navy-800 text-white focus:border-gold-400 focus:ring-gold-400"
                                required
                            />
                        </div>
                    </div>

                    {error && <p className="text-sm text-red-500 text-center">{error}</p>}
                    <Button type="submit" className="w-full bg-gold-500 text-navy-900 hover:bg-gold-600 font-bold" disabled={loading}>
                        {loading ? "Creating Account..." : "Sign Up"}
                    </Button>
                </form>
            </CardContent>
            <CardFooter className="justify-center">
                <p className="text-sm text-gray-400">
                    Already have an account?{" "}
                    <Link href="/login" className="text-gold-400 hover:text-gold-300">
                        Sign in
                    </Link>
                </p>
            </CardFooter>
        </Card>
    );
}
