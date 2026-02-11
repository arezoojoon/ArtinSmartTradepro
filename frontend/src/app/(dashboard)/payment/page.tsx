"use client";

import { Check, X, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import { useState } from "react";

export default function PaymentPage() {
    const [loading, setLoading] = useState<string | null>(null);

    const handleSubscribe = async (plan: string) => {
        setLoading(plan);
        try {
            const { data } = await api.post("/stripe/create-checkout", {
                plan_name: plan.toLowerCase(),
                billing_cycle: plan === "Enterprise" ? "yearly" : "monthly"
            });
            if (data.checkout_url) {
                window.location.href = data.checkout_url;
            }
        } catch (error) {
            console.error("Subscription error:", error);
            alert("Failed to start subscription flow.");
        } finally {
            setLoading(null);
        }
    };

    return (
        <div className="min-h-screen bg-black text-white p-6 md:p-12">
            <div className="max-w-7xl mx-auto space-y-12">
                {/* Header */}
                <div className="text-center space-y-4">
                    <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight text-white mb-4">
                        <span className="text-gold-400">Artin Smart Trade</span> Plans
                    </h1>
                    <p className="text-gray-400 text-lg max-w-2xl mx-auto">
                        Scale your trade intelligence with AI-driven insights and automation.
                        <br />
                        <span className="text-gold-500/80 text-sm">Use your corporate code at checkout for exclusive benefits.</span>
                    </p>
                </div>

                {/* Pricing Cards */}
                <div className="grid md:grid-cols-3 gap-8">

                    {/* Professional */}
                    <Card className="bg-navy-900 border-navy-800 text-white relative overflow-hidden flex flex-col">
                        <CardHeader>
                            <div className="flex items-center gap-2 mb-2">
                                <span className="text-blue-400">⚡</span>
                                <CardTitle className="text-xl">Professional</CardTitle>
                            </div>
                            <CardDescription className="text-gray-400">
                                Essential tools for individual traders and small teams.
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-6 flex-1">
                            <div className="flex items-baseline">
                                <span className="text-4xl font-bold text-white">999</span>
                                <span className="text-lg text-gray-400 ml-2">AED / mo</span>
                            </div>
                            <p className="text-xs text-gray-500">Billed Annually: 9,000 AED</p>

                            <ul className="space-y-3 pt-4 text-sm">
                                <li className="flex items-center gap-2"><Check className="h-4 w-4 text-blue-400" /> One Click Manual Send</li>
                                <li className="flex items-center gap-2"><Check className="h-4 w-4 text-blue-400" /> Limited Lead Hunter View</li>
                                <li className="flex items-center gap-2"><Check className="h-4 w-4 text-blue-400" /> Simple Drag & Drop CRM</li>
                                <li className="flex items-center gap-2"><Check className="h-4 w-4 text-blue-400" /> Email Ticket Support (48h)</li>
                                <li className="flex items-center gap-2 text-gray-600"><X className="h-4 w-4" /> No Gap Analysis</li>
                                <li className="flex items-center gap-2 text-gray-600"><X className="h-4 w-4" /> No Auto-Follow Up</li>
                            </ul>
                        </CardContent>
                        <CardFooter>
                            <Button
                                className="w-full bg-white text-black hover:bg-gray-200"
                                onClick={() => handleSubscribe("Professional")}
                                disabled={loading === "Professional"}
                            >
                                Get Started <ArrowRight className="ml-2 h-4 w-4" />
                            </Button>
                        </CardFooter>
                    </Card>

                    {/* Enterprise */}
                    <Card className="bg-navy-900 border-gold-500/50 text-white relative overflow-hidden flex flex-col shadow-2xl shadow-gold-900/10">
                        <div className="absolute top-0 right-0">
                            <Badge className="bg-gold-500 text-black rounded-bl-lg rounded-tr-none px-3 py-1 text-xs font-bold">
                                MOST POPULAR
                            </Badge>
                        </div>
                        <CardHeader>
                            <div className="flex items-center gap-2 mb-2">
                                <span className="text-gold-400">🛡️</span>
                                <CardTitle className="text-xl text-white">Enterprise</CardTitle>
                            </div>
                            <CardDescription className="text-gray-400">
                                Full corporate suite for maximum ROI and automation.
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-6 flex-1">
                            <div className="flex items-baseline">
                                <span className="text-5xl font-bold text-white">19,000</span>
                                <span className="text-lg text-gray-400 ml-2">AED / yr</span>
                            </div>
                            <p className="text-xs text-green-400 font-medium">Save 45% vs Monthly</p>

                            <ul className="space-y-3 pt-4 text-sm">
                                <li className="flex items-center gap-2"><Check className="h-4 w-4 text-green-500" /> Automated Follow up Bot</li>
                                <li className="flex items-center gap-2"><Check className="h-4 w-4 text-green-500" /> Full Database Access</li>
                                <li className="flex items-center gap-2"><Check className="h-4 w-4 text-green-500" /> Trade Opportunity Reports</li>
                                <li className="flex items-center gap-2"><Check className="h-4 w-4 text-green-500" /> Advanced CRM + Forecasting</li>
                                <li className="flex items-center gap-2"><Check className="h-4 w-4 text-green-500" /> Dedicated Account Manager</li>
                            </ul>
                        </CardContent>
                        <CardFooter>
                            <Button
                                className="w-full bg-gold-500 text-black hover:bg-gold-400 font-bold"
                                onClick={() => handleSubscribe("Enterprise")}
                                disabled={loading === "Enterprise"}
                            >
                                Subscribe Now <ArrowRight className="ml-2 h-4 w-4" />
                            </Button>
                            <p className="text-xs text-center text-gray-500 mt-2 w-full">Corporate invoices available.</p>
                        </CardFooter>
                    </Card>

                    {/* White Label */}
                    <Card className="bg-navy-900 border-navy-800 text-white relative overflow-hidden flex flex-col">
                        <CardHeader>
                            <div className="flex items-center gap-2 mb-2">
                                <span className="text-purple-400">🌐</span>
                                <CardTitle className="text-xl">White Label</CardTitle>
                            </div>
                            <CardDescription className="text-gray-400">
                                Your own brand, infrastructure, and custom API.
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-6 flex-1">
                            <div className="flex items-baseline">
                                <span className="text-lg text-gray-400">Starts from</span>
                            </div>
                            <div className="flex items-baseline -mt-2">
                                <span className="text-4xl font-bold text-white">45,000</span>
                                <span className="text-lg text-gray-400 ml-2">AED</span>
                            </div>

                            <ul className="space-y-3 pt-4 text-sm">
                                <li className="flex items-center gap-2"><Check className="h-4 w-4 text-purple-400" /> Your Own Logo, Domain & App</li>
                                <li className="flex items-center gap-2"><Check className="h-4 w-4 text-purple-400" /> Automated Bot + Custom API</li>
                                <li className="flex items-center gap-2"><Check className="h-4 w-4 text-purple-400" /> Big Data & Macro Reports</li>
                                <li className="flex items-center gap-2"><Check className="h-4 w-4 text-purple-400" /> ERP Integration</li>
                                <li className="flex items-center gap-2"><Check className="h-4 w-4 text-purple-400" /> 24/7 Priority + Dedicated Server</li>
                            </ul>
                        </CardContent>
                        <CardFooter>
                            <Button
                                className="w-full bg-transparent border border-gray-600 hover:bg-gray-800 text-white"
                                onClick={() => window.location.href = "mailto:sales@artin.com"}
                            >
                                Contact Sales
                            </Button>
                        </CardFooter>
                    </Card>

                </div>

                <div className="text-center text-xs text-navy-500">
                    <p>By subscribing, you agree to our Terms of Service.</p>
                    <p>Artin Smart Trade branding applies to Professional and Enterprise plans.</p>
                </div>
            </div>
        </div>
    );
}
