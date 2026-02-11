"use client";

import { Check, X, Zap, Shield, Crown, ArrowRight } from "lucide-react";
import Link from "next/link";

const plans = [
    {
        name: "Professional",
        icon: Zap,
        description: "Essential tools for individual traders and small teams.",
        priceMonthly: "999",
        priceYearly: "9,990",
        currency: "AED",
        badge: null,
        cta: "Get Started",
        ctaLink: "/auth/register?plan=professional",
        highlighted: false,
        features: [
            { name: "One Click Manual Send", included: true },
            { name: "Limited Lead Hunter View", included: true },
            { name: "Simple Drag & Drop CRM", included: true },
            { name: "CSV Lead Import", included: true },
            { name: "Email Ticket Support (48h)", included: true },
            { name: "Trade Intelligence", included: false },
            { name: "AI Vision & Voice", included: false },
            { name: "Auto-Follow Up", included: false },
            { name: "Campaigns", included: false },
            { name: "Gap Analysis", included: false },
        ],
    },
    {
        name: "Enterprise",
        icon: Shield,
        description: "Full corporate suite for maximum ROI and automation.",
        priceMonthly: null,
        priceYearly: "19,000",
        currency: "AED",
        badge: "MOST POPULAR",
        cta: "Subscribe Now",
        ctaLink: "/auth/register?plan=enterprise",
        highlighted: true,
        features: [
            { name: "Automated Follow-up Bot", included: true },
            { name: "Full Database Access", included: true },
            { name: "Trade Opportunity Reports", included: true },
            { name: "Advanced CRM + Forecasting", included: true },
            { name: "Dedicated Account Manager", included: true },
            { name: "AI Vision (Business Card Scan)", included: true },
            { name: "AI Voice Analysis", included: true },
            { name: "AI Brain Insights", included: true },
            { name: "WhatsApp Broadcast", included: true },
            { name: "Campaigns & Analytics", included: true },
        ],
    },
    {
        name: "White Label",
        icon: Crown,
        description: "Your own brand, infrastructure, and custom API.",
        priceMonthly: null,
        priceYearly: "45,000",
        currency: "AED",
        badge: null,
        cta: "Contact Sales",
        ctaLink: "mailto:sales@artinsmartagent.com?subject=White%20Label%20Inquiry",
        highlighted: false,
        features: [
            { name: "Your Own Logo, Domain & App", included: true },
            { name: "Automated Bot + Custom API", included: true },
            { name: "Big Data & Macro Reports", included: true },
            { name: "ERP Integration", included: true },
            { name: "24/7 Priority + Dedicated Server", included: true },
            { name: "Everything in Enterprise", included: true },
            { name: "Custom Feature Development", included: true },
            { name: "White-Glove Onboarding", included: true },
            { name: "SLA Guarantee", included: true },
            { name: "Source Code Access", included: true },
        ],
    },
];

export default function PricingPage() {
    return (
        <div className="min-h-screen bg-navy-950 text-white">
            {/* Header */}
            <header className="border-b border-navy-800/50 px-6 py-4">
                <div className="mx-auto max-w-7xl flex items-center justify-between">
                    <Link href="/" className="text-2xl font-bold">
                        <span className="text-gold-400">Artin</span> Smart Trade
                    </Link>
                    <nav className="flex items-center gap-6">
                        <Link href="/about" className="text-navy-300 hover:text-white transition-colors">About Us</Link>
                        <Link href="/auth/login" className="px-4 py-2 rounded-lg border border-navy-600 text-navy-200 hover:border-gold-400 hover:text-gold-400 transition-all">
                            Sign In
                        </Link>
                    </nav>
                </div>
            </header>

            {/* Hero */}
            <section className="pt-16 pb-8 text-center px-6">
                <h1 className="text-4xl md:text-5xl font-bold mb-4">
                    <span className="text-gold-400">Artin Smart Trade</span> Plans
                </h1>
                <p className="text-lg text-navy-300 mb-2">
                    Scale your trade intelligence with AI-driven insights and automation.
                </p>
                <p className="text-gold-400 text-sm">
                    Use your corporate code at checkout for exclusive benefits.
                </p>
            </section>

            {/* Plans Grid */}
            <section className="px-6 pb-20">
                <div className="mx-auto max-w-7xl grid grid-cols-1 md:grid-cols-3 gap-6">
                    {plans.map((plan) => (
                        <div
                            key={plan.name}
                            className={`
                relative rounded-2xl p-8 flex flex-col transition-all duration-300
                ${plan.highlighted
                                    ? "bg-gradient-to-b from-navy-800 to-navy-900 border-2 border-gold-400 shadow-xl shadow-gold-400/10 scale-[1.02]"
                                    : "bg-navy-900/50 border border-navy-700/50 hover:border-navy-600"
                                }
              `}
                        >
                            {/* Badge */}
                            {plan.badge && (
                                <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1 bg-gold-400 text-navy-950 text-xs font-bold rounded-full uppercase tracking-wider">
                                    {plan.badge}
                                </div>
                            )}

                            {/* Plan Header */}
                            <div className="mb-6">
                                <div className="flex items-center gap-2 mb-2">
                                    <plan.icon className={`h-5 w-5 ${plan.highlighted ? "text-gold-400" : "text-navy-400"}`} />
                                    <h2 className="text-xl font-bold">{plan.name}</h2>
                                </div>
                                <p className="text-sm text-navy-400">{plan.description}</p>
                            </div>

                            {/* Price */}
                            <div className="mb-6">
                                {plan.priceMonthly ? (
                                    <>
                                        <div className="flex items-baseline gap-1">
                                            <span className="text-4xl font-bold">{plan.priceMonthly}</span>
                                            <span className="text-navy-400 text-sm">{plan.currency} / mo</span>
                                        </div>
                                        <p className="text-xs text-navy-500 mt-1">Billed Annually: {plan.priceYearly} {plan.currency}</p>
                                    </>
                                ) : plan.name === "White Label" ? (
                                    <>
                                        <p className="text-sm text-navy-400">Starts from</p>
                                        <div className="flex items-baseline gap-1">
                                            <span className="text-4xl font-bold">{plan.priceYearly}</span>
                                            <span className="text-navy-400 text-sm">{plan.currency}</span>
                                        </div>
                                    </>
                                ) : (
                                    <>
                                        <div className="flex items-baseline gap-1">
                                            <span className="text-4xl font-bold">{plan.priceYearly}</span>
                                            <span className="text-navy-400 text-sm">{plan.currency} / yr</span>
                                        </div>
                                        <p className="text-xs text-gold-400 mt-1">Save 15% vs Monthly</p>
                                    </>
                                )}
                            </div>

                            {/* Features */}
                            <ul className="space-y-3 mb-8 flex-1">
                                {plan.features.map((feature) => (
                                    <li key={feature.name} className="flex items-start gap-2 text-sm">
                                        {feature.included ? (
                                            <Check className={`h-4 w-4 mt-0.5 ${plan.highlighted ? "text-gold-400" : "text-green-400"}`} />
                                        ) : (
                                            <X className="h-4 w-4 mt-0.5 text-navy-600" />
                                        )}
                                        <span className={feature.included ? "text-navy-200" : "text-navy-600"}>
                                            {feature.name}
                                        </span>
                                    </li>
                                ))}
                            </ul>

                            {/* CTA */}
                            <Link
                                href={plan.ctaLink}
                                className={`
                  w-full py-3 px-6 rounded-xl text-center font-semibold text-sm transition-all duration-200
                  flex items-center justify-center gap-2
                  ${plan.highlighted
                                        ? "bg-gold-400 text-navy-950 hover:bg-gold-300 shadow-lg shadow-gold-400/20"
                                        : "bg-navy-800 text-white border border-navy-600 hover:border-navy-400"
                                    }
                `}
                            >
                                {plan.cta}
                                <ArrowRight className="h-4 w-4" />
                            </Link>

                            {/* Corporate Note */}
                            {plan.highlighted && (
                                <p className="text-xs text-navy-500 text-center mt-3">
                                    Corporate invoices available.
                                </p>
                            )}
                        </div>
                    ))}
                </div>

                {/* Footer Note */}
                <div className="text-center mt-10">
                    <p className="text-sm text-navy-500">
                        By subscribing, you agree to our Terms of Service.
                    </p>
                    <p className="text-xs text-navy-600 mt-1">
                        Artin Smart Trade branding applies to Professional and Enterprise plans.
                    </p>
                </div>
            </section>
        </div>
    );
}
