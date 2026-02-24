"use client";

import { useState, useEffect, Suspense } from "react";
import Link from "next/link";
import Image from "next/image";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { CheckCircle2, Shield, Clock, ArrowLeft, Loader2, Eye, EyeOff } from "lucide-react";
import api from "@/lib/api";

const PLANS: Record<string, {
    name: string;
    price: number;
    period: string;
    features: string[];
    highlight: boolean;
}> = {
    professional: {
        name: "Professional",
        price: 299,
        period: "mo",
        features: [
            "Hunter (Lead Scraper)",
            "WhatsApp Bot (Single-channel)",
            "Basic CRM",
            "5 Users included",
            "Email Support",
        ],
        highlight: false,
    },
    enterprise: {
        name: "Enterprise",
        price: 999,
        period: "mo",
        features: [
            "Everything in Professional",
            "Full Trade Intelligence (Freight/FX/Risk)",
            "Omnichannel Bots (WhatsApp + Telegram)",
            "Broadcast Campaigns",
            "Competitor Tracking",
            "AI Brain (Arbitrage & Risk)",
            "Unlimited Users",
            "Priority Support",
        ],
        highlight: true,
    },
};

function CheckoutContent() {
    const searchParams = useSearchParams();
    const router = useRouter();
    const planCode = searchParams.get("plan") || "professional";
    const plan = PLANS[planCode] || PLANS.professional;

    const [formData, setFormData] = useState({
        full_name: "",
        email: "",
        password: "",
        confirmPassword: "",
        companyName: "",
    });
    const [tenantMode, setTenantMode] = useState("hybrid");
    const [persona, setPersona] = useState("trader");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [step, setStep] = useState<"form" | "processing" | "success">("form");

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setFormData({ ...formData, [e.target.id]: e.target.value });
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (formData.password !== formData.confirmPassword) {
            setError("Passwords do not match");
            return;
        }
        if (formData.password.length < 8) {
            setError("Password must be at least 8 characters");
            return;
        }
        setLoading(true);
        setError("");
        setStep("processing");

        try {
            // 1. Register account with selected plan
            await api.post("/auth/register", {
                email: formData.email,
                password: formData.password,
                full_name: formData.full_name,
                role: "admin",
                company_name: formData.companyName,
                tenant_mode: tenantMode,
                persona: persona,
                plan: planCode,
            });

            // 2. Auto-login
            const loginRes = await api.post("/auth/login", {
                email: formData.email,
                password: formData.password,
            });

            const { access_token, refresh_token } = loginRes.data;

            // 3. Store tokens
            if (typeof window !== "undefined") {
                localStorage.setItem("access_token", access_token);
                if (refresh_token) {
                    localStorage.setItem("refresh_token", refresh_token);
                }
            }

            setStep("success");

            // 4. Redirect to dashboard after brief success screen
            setTimeout(() => {
                window.location.href = "/dashboard";
            }, 2000);
        } catch (err: any) {
            setStep("form");
            let errorMessage = "Registration failed. Please try again.";

            if (err.data?.detail) {
                if (typeof err.data.detail === "string") {
                    errorMessage = err.data.detail;
                } else if (Array.isArray(err.data.detail)) {
                    errorMessage = err.data.detail
                        .map((d: any) => `${d.loc?.join(".") || ""}: ${d.msg}`)
                        .join(", ");
                }
            } else if (err.response?.data?.detail) {
                errorMessage = err.response.data.detail;
            }

            setError(errorMessage);
        } finally {
            setLoading(false);
        }
    };

    // Processing screen
    if (step === "processing") {
        return (
            <div className="min-h-screen bg-[#0a1628] flex items-center justify-center">
                <div className="text-center space-y-6">
                    <div className="relative mx-auto w-20 h-20">
                        <div className="absolute inset-0 rounded-full border-t-2 border-b-2 border-[#f5a623] animate-spin" />
                        <div className="absolute inset-0 flex items-center justify-center">
                            <Shield className="h-8 w-8 text-[#f5a623]" />
                        </div>
                    </div>
                    <div>
                        <h2 className="text-xl font-bold text-white">Setting up your workspace...</h2>
                        <p className="mt-2 text-sm text-gray-400">Creating your account and activating your free trial</p>
                    </div>
                </div>
            </div>
        );
    }

    // Success screen
    if (step === "success") {
        return (
            <div className="min-h-screen bg-[#0a1628] flex items-center justify-center">
                <div className="text-center space-y-6 max-w-md mx-auto px-4">
                    <div className="mx-auto w-16 h-16 rounded-full bg-emerald-500/20 flex items-center justify-center">
                        <CheckCircle2 className="h-8 w-8 text-emerald-400" />
                    </div>
                    <div>
                        <h2 className="text-2xl font-bold text-white">Welcome to Artin Smart Trade!</h2>
                        <p className="mt-2 text-sm text-gray-400">
                            Your <span className="text-[#f5a623] font-semibold">{plan.name}</span> plan is active with a 3-day free trial.
                        </p>
                    </div>
                    <div className="flex items-center justify-center gap-2 text-sm text-gray-500">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Redirecting to your dashboard...
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-[#0a1628] text-white">
            {/* Header */}
            <header className="border-b border-white/5 bg-[#0a1628]/80 backdrop-blur-md">
                <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
                    <Link href="/" className="flex items-center gap-2">
                        <div className="relative h-8 w-8 overflow-hidden rounded-lg bg-gradient-to-br from-[#f5a623] to-[#8C7211] p-[1px]">
                            <div className="flex h-full w-full items-center justify-center rounded-lg bg-[#071022]">
                                <span className="text-sm font-bold text-[#f5a623]">A</span>
                            </div>
                        </div>
                        <span className="text-lg font-bold text-white">
                            Artin<span className="text-[#f5a623]">Smart</span>Trade
                        </span>
                    </Link>
                    <div className="flex items-center gap-4 text-sm">
                        <span className="text-gray-400">Already have an account?</span>
                        <Link href="/login" className="text-[#f5a623] font-medium hover:underline">
                            Sign in
                        </Link>
                    </div>
                </div>
            </header>

            <main className="mx-auto max-w-6xl px-4 py-8 md:py-12">
                <Link href="/pricing" className="inline-flex items-center gap-2 text-sm text-gray-400 hover:text-white mb-8 transition-colors">
                    <ArrowLeft className="h-4 w-4" />
                    Back to pricing
                </Link>

                <div className="grid gap-8 lg:grid-cols-5">
                    {/* Left: Registration Form (3 cols) */}
                    <div className="lg:col-span-3">
                        <div className="rounded-2xl border border-[#1e3a5f] bg-[#0e1e33] p-6 md:p-8">
                            <h1 className="text-2xl font-bold text-white">Create your account</h1>
                            <p className="mt-1 text-sm text-gray-400">
                                Start your 3-day free trial of the <span className="text-[#f5a623] font-medium">{plan.name}</span> plan
                            </p>

                            <form onSubmit={handleSubmit} className="mt-6 space-y-5">
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="full_name">Full Name</Label>
                                        <Input
                                            id="full_name"
                                            placeholder="John Smith"
                                            value={formData.full_name}
                                            onChange={handleChange}
                                            className="border-[#1e3a5f] bg-[#0a1628] text-white placeholder:text-gray-600 focus:border-[#f5a623] focus:ring-[#f5a623]/20"
                                            required
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="companyName">Company Name</Label>
                                        <Input
                                            id="companyName"
                                            placeholder="Acme Trading Co."
                                            value={formData.companyName}
                                            onChange={handleChange}
                                            className="border-[#1e3a5f] bg-[#0a1628] text-white placeholder:text-gray-600 focus:border-[#f5a623] focus:ring-[#f5a623]/20"
                                            required
                                        />
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="email">Work Email</Label>
                                    <Input
                                        id="email"
                                        type="email"
                                        placeholder="john@company.com"
                                        value={formData.email}
                                        onChange={handleChange}
                                        className="border-[#1e3a5f] bg-[#0a1628] text-white placeholder:text-gray-600 focus:border-[#f5a623] focus:ring-[#f5a623]/20"
                                        required
                                    />
                                </div>

                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="password">Password</Label>
                                        <div className="relative">
                                            <Input
                                                id="password"
                                                type={showPassword ? "text" : "password"}
                                                placeholder="Min. 8 characters"
                                                value={formData.password}
                                                onChange={handleChange}
                                                className="border-[#1e3a5f] bg-[#0a1628] text-white placeholder:text-gray-600 focus:border-[#f5a623] focus:ring-[#f5a623]/20 pr-10"
                                                required
                                            />
                                            <button
                                                type="button"
                                                onClick={() => setShowPassword(!showPassword)}
                                                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white"
                                            >
                                                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                                            </button>
                                        </div>
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="confirmPassword">Confirm Password</Label>
                                        <Input
                                            id="confirmPassword"
                                            type="password"
                                            placeholder="Repeat password"
                                            value={formData.confirmPassword}
                                            onChange={handleChange}
                                            className="border-[#1e3a5f] bg-[#0a1628] text-white placeholder:text-gray-600 focus:border-[#f5a623] focus:ring-[#f5a623]/20"
                                            required
                                        />
                                    </div>
                                </div>

                                <div className="space-y-3">
                                    <Label>Business Mode</Label>
                                    <Tabs defaultValue="hybrid" onValueChange={setTenantMode} className="w-full">
                                        <TabsList className="grid w-full grid-cols-3 bg-[#0a1628] border border-[#1e3a5f]">
                                            <TabsTrigger value="buyer" className="data-[state=active]:bg-[#f5a623]/10 data-[state=active]:text-[#f5a623]">Buyer</TabsTrigger>
                                            <TabsTrigger value="seller" className="data-[state=active]:bg-[#f5a623]/10 data-[state=active]:text-[#f5a623]">Seller</TabsTrigger>
                                            <TabsTrigger value="hybrid" className="data-[state=active]:bg-[#f5a623]/10 data-[state=active]:text-[#f5a623]">Both</TabsTrigger>
                                        </TabsList>
                                    </Tabs>
                                    <p className="text-xs text-gray-500">
                                        {tenantMode === "buyer" && "Focus on Sourcing, Landed Cost, and Supplier Risk."}
                                        {tenantMode === "seller" && "Focus on Market Demand, Leads, and Competitor Pricing."}
                                        {tenantMode === "hybrid" && "Full access to both Sourcing and Sales engines."}
                                    </p>
                                </div>

                                <div className="space-y-2">
                                    <Label>Your Role</Label>
                                    <Select onValueChange={setPersona} defaultValue="trader">
                                        <SelectTrigger className="border-[#1e3a5f] bg-[#0a1628] text-white">
                                            <SelectValue placeholder="Select your role" />
                                        </SelectTrigger>
                                        <SelectContent className="bg-[#0e1e33] border-[#1e3a5f] text-white">
                                            <SelectItem value="trader">Trader / Owner</SelectItem>
                                            <SelectItem value="logistics">Logistics Manager</SelectItem>
                                            <SelectItem value="finance">Finance / CFO</SelectItem>
                                            <SelectItem value="admin">System Admin</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>

                                {error && (
                                    <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-400">
                                        {error}
                                    </div>
                                )}

                                <Button
                                    type="submit"
                                    className="w-full h-12 bg-[#f5a623] text-[#0a1628] hover:bg-[#e0951a] font-bold text-base"
                                    disabled={loading}
                                >
                                    {loading ? (
                                        <span className="flex items-center gap-2">
                                            <Loader2 className="h-4 w-4 animate-spin" />
                                            Creating account...
                                        </span>
                                    ) : (
                                        "Start Free Trial"
                                    )}
                                </Button>

                                <p className="text-center text-xs text-gray-500">
                                    By creating an account, you agree to our{" "}
                                    <Link href="/terms" className="text-[#f5a623] hover:underline">Terms</Link>{" "}
                                    and{" "}
                                    <Link href="/privacy" className="text-[#f5a623] hover:underline">Privacy Policy</Link>
                                </p>
                            </form>
                        </div>
                    </div>

                    {/* Right: Order Summary (2 cols) */}
                    <div className="lg:col-span-2 space-y-6">
                        {/* Plan Summary */}
                        <div className="rounded-2xl border border-[#1e3a5f] bg-[#0e1e33] p-6">
                            <div className="flex items-center justify-between mb-4">
                                <h2 className="text-lg font-bold text-white">Order Summary</h2>
                                <Link href="/pricing" className="text-xs text-[#f5a623] hover:underline">
                                    Change plan
                                </Link>
                            </div>

                            <div className="rounded-xl border border-[#1e3a5f] bg-[#0a1628] p-4">
                                <div className="flex items-center justify-between">
                                    <span className="font-semibold text-white">{plan.name} Plan</span>
                                    {plan.highlight && (
                                        <span className="rounded-full bg-[#f5a623] px-2 py-0.5 text-[9px] font-bold text-[#0a1628] uppercase">
                                            Popular
                                        </span>
                                    )}
                                </div>
                                <div className="mt-2 flex items-baseline gap-1">
                                    <span className="text-2xl font-bold text-white">${plan.price}</span>
                                    <span className="text-sm text-gray-400">/{plan.period}</span>
                                </div>
                            </div>

                            <ul className="mt-4 space-y-2">
                                {plan.features.map((f) => (
                                    <li key={f} className="flex items-start gap-2 text-sm text-gray-300">
                                        <CheckCircle2 className="h-4 w-4 text-[#f5a623] shrink-0 mt-0.5" />
                                        <span>{f}</span>
                                    </li>
                                ))}
                            </ul>

                            {/* Pricing breakdown */}
                            <div className="mt-6 border-t border-[#1e3a5f] pt-4 space-y-2">
                                <div className="flex justify-between text-sm">
                                    <span className="text-gray-400">Subtotal</span>
                                    <span className="text-white">${plan.price}/{plan.period}</span>
                                </div>
                                <div className="flex justify-between text-sm">
                                    <span className="text-gray-400">3-Day Free Trial</span>
                                    <span className="text-emerald-400 font-medium">-${plan.price}</span>
                                </div>
                                <div className="flex justify-between text-base font-bold border-t border-[#1e3a5f] pt-2 mt-2">
                                    <span className="text-white">Due today</span>
                                    <span className="text-emerald-400">$0.00</span>
                                </div>
                            </div>
                        </div>

                        {/* Free Trial Info */}
                        <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-5">
                            <div className="flex items-start gap-3">
                                <Clock className="h-5 w-5 text-emerald-400 shrink-0 mt-0.5" />
                                <div>
                                    <h3 className="font-semibold text-emerald-400">3-Day Free Trial</h3>
                                    <p className="mt-1 text-sm text-gray-400">
                                        Full access to all {plan.name} features. No charge until your trial ends.
                                        Cancel anytime before the trial period.
                                    </p>
                                </div>
                            </div>
                        </div>

                        {/* Trust Signals */}
                        <div className="rounded-2xl border border-[#1e3a5f] bg-[#0e1e33] p-5 space-y-3">
                            <div className="flex items-center gap-3 text-sm text-gray-300">
                                <Shield className="h-4 w-4 text-[#f5a623] shrink-0" />
                                <span>256-bit SSL encrypted</span>
                            </div>
                            <div className="flex items-center gap-3 text-sm text-gray-300">
                                <CheckCircle2 className="h-4 w-4 text-[#f5a623] shrink-0" />
                                <span>GDPR compliant</span>
                            </div>
                            <div className="flex items-center gap-3 text-sm text-gray-300">
                                <CheckCircle2 className="h-4 w-4 text-[#f5a623] shrink-0" />
                                <span>Cancel anytime — no lock-in</span>
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}

export default function CheckoutPage() {
    return (
        <Suspense
            fallback={
                <div className="min-h-screen bg-[#0a1628] flex items-center justify-center">
                    <Loader2 className="h-8 w-8 animate-spin text-[#f5a623]" />
                </div>
            }
        >
            <CheckoutContent />
        </Suspense>
    );
}
