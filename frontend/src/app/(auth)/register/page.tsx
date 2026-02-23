"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import api from "@/lib/api";

export default function RegisterPage() {
    const [formData, setFormData] = useState({
        full_name: "",
        email: "",
        password: "",
        confirmPassword: "",
        companyName: ""
    });
    const [tenantMode, setTenantMode] = useState("hybrid");
    const [persona, setPersona] = useState("trader");

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
                role: "admin", // Creator is Admin
                company_name: formData.companyName,
                tenant_mode: tenantMode,
                persona: persona
            });
            // Redirect to login with success flag
            router.push("/login?registered=true");
        } catch (err: any) {
            console.error("Registration error:", err);
            let errorMessage = "Failed to register";

            if (err.data?.detail) {
                if (typeof err.data.detail === 'string') {
                    errorMessage = err.data.detail;
                } else if (Array.isArray(err.data.detail)) {
                    // Handle FastAPI 422 validation errors
                    errorMessage = err.data.detail.map((d: any) => `${d.loc.join('.')}: ${d.msg}`).join(', ');
                }
            } else if (err.data?.error?.message) {
                errorMessage = err.data.error.message;
            }

            setError(errorMessage);
        } finally {
            setLoading(false);
        }
    };

    return (
        <Card className="border-[#1e3a5f] bg-[#0e1e33] text-white w-full max-w-lg">
            <CardHeader>
                <CardTitle className="text-center text-xl text-[#f5a623]">Create Account</CardTitle>
                <CardDescription className="text-center text-gray-400">
                    Join the AI Trade Operating System
                </CardDescription>
            </CardHeader>
            <CardContent>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
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
                    </div>

                    <div className="space-y-3 pt-2">
                        <Label>Primary Business Mode</Label>
                        <Tabs defaultValue="hybrid" onValueChange={setTenantMode} className="w-full">
                            <TabsList className="grid w-full grid-cols-3 bg-navy-950">
                                <TabsTrigger value="buyer">Buyer</TabsTrigger>
                                <TabsTrigger value="seller">Seller</TabsTrigger>
                                <TabsTrigger value="hybrid">Both</TabsTrigger>
                            </TabsList>
                        </Tabs>
                        <p className="text-xs text-gray-500">
                            {tenantMode === 'buyer' && "Focus on Sourcing, Landed Cost, and Supplier Risk."}
                            {tenantMode === 'seller' && "Focus on Market Demand, Leads, and Competitor Pricing."}
                            {tenantMode === 'hybrid' && "Full access to both Sourcing and Sales engines."}
                        </p>
                    </div>

                    <div className="space-y-2">
                        <Label>Your Role</Label>
                        <Select onValueChange={setPersona} defaultValue="trader">
                            <SelectTrigger className="border-navy-700 bg-navy-800 text-white">
                                <SelectValue placeholder="Select your role" />
                            </SelectTrigger>
                            <SelectContent className="bg-navy-800 border-navy-700 text-white">
                                <SelectItem value="trader">Trader / Owner</SelectItem>
                                <SelectItem value="logistics">Logistics Manager</SelectItem>
                                <SelectItem value="finance">Finance / CFO</SelectItem>
                                <SelectItem value="admin">System Admin</SelectItem>
                            </SelectContent>
                        </Select>
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
                            <div className="flex justify-between items-center">
                                <Label htmlFor="password">Password</Label>
                                <span className="text-[10px] text-gray-500">Min. 10 chars</span>
                            </div>
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
                        {loading ? "Initializing Brain..." : "Create Account"}
                    </Button>
                </form>
            </CardContent>
            <CardFooter className="justify-center">
                <p className="text-sm text-gray-400">
                    Already have an account?{" "}
                    <Link href="/login" className="text-[#f5a623] hover:text-gold-300">
                        Sign in
                    </Link>
                </p>
            </CardFooter>
        </Card>
    );
}
