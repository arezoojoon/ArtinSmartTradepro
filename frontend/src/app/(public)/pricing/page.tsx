import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Check, X } from "lucide-react";

const pricingPlans = [
    {
        name: "Trial",
        price: "$0",
        period: "/14 days",
        description: "Perfect for testing the platform capability.",
        features: [
            "5 Hunter searches/day",
            "1 GB Storage",
            "Community Support",
            "Basic CRM",
        ],
        missing: ["AI Negotiation", "API Access", "White Label"],
        button: "Start Free Trial",
        href: "/register?plan=trial",
        popular: false
    },
    {
        name: "Professional",
        price: "$49",
        period: "/month",
        description: "For growing trade businesses.",
        features: [
            "Unlimited Hunter searches",
            "100 GB Storage",
            "Priority Support",
            "Full CRM & Pipeline",
            "WhatsApp Automation (1 number)",
            "AI Negotiator (Standard)",
        ],
        missing: ["White Label"],
        button: "Get Started",
        href: "/register?plan=professional",
        popular: true
    },
    {
        name: "Enterprise",
        price: "Custom",
        period: "",
        description: "For large organizations with custom needs.",
        features: [
            "Unlimited Everything",
            "Dedicated Account Manager",
            "Custom AI Models",
            "White Label Options",
            "API Access",
            "SLA 99.9%",
        ],
        missing: [],
        button: "Contact Sales",
        href: "mailto:sales@artin.com",
        popular: false
    }
];

export default function PricingPage() {
    return (
        <div className="min-h-screen bg-navy-950 text-white selection:bg-gold-500 selection:text-navy-900 py-24">
            <div className="container mx-auto px-4">
                <div className="text-center mb-16">
                    <h1 className="text-4xl font-extrabold tracking-tight md:text-6xl mb-4">
                        Simple, Transparent Pricing
                    </h1>
                    <p className="text-xl text-gray-400 max-w-2xl mx-auto">
                        Choose the plan that fits your business needs. No hidden fees.
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-7xl mx-auto">
                    {pricingPlans.map((plan) => (
                        <div
                            key={plan.name}
                            className={`relative rounded-2xl p-8 border ${plan.popular ? 'border-gold-500 bg-navy-900/50 shadow-2xl shadow-gold-500/10' : 'border-navy-800 bg-navy-900/30'}`}
                        >
                            {plan.popular && (
                                <div className="absolute top-0 right-0 -mt-3 mr-6 bg-gold-500 text-navy-900 text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wide">
                                    Most Popular
                                </div>
                            )}
                            <h3 className="text-xl font-bold text-white">{plan.name}</h3>
                            <div className="mt-4 flex items-baseline text-white">
                                <span className="text-5xl font-extrabold tracking-tight">{plan.price}</span>
                                <span className="ml-1 text-xl font-semibold text-gray-400">{plan.period}</span>
                            </div>
                            <p className="mt-2 text-gray-400">{plan.description}</p>

                            <ul className="mt-8 space-y-4">
                                {plan.features.map((feature) => (
                                    <li key={feature} className="flex items-start">
                                        <div className="flex-shrink-0">
                                            <Check className="h-5 w-5 text-gold-400" />
                                        </div>
                                        <p className="ml-3 text-sm text-gray-300">{feature}</p>
                                    </li>
                                ))}
                                {plan.missing.map((feature) => (
                                    <li key={feature} className="flex items-start opacity-50">
                                        <div className="flex-shrink-0">
                                            <X className="h-5 w-5 text-gray-500" />
                                        </div>
                                        <p className="ml-3 text-sm text-gray-500">{feature}</p>
                                    </li>
                                ))}
                            </ul>

                            <div className="mt-8">
                                <Link href={plan.href}>
                                    <Button
                                        className={`w-full h-12 rounded-full font-bold text-lg ${plan.popular ? 'bg-gold-500 text-navy-900 hover:bg-gold-600' : 'bg-navy-800 text-white hover:bg-navy-700'}`}
                                    >
                                        {plan.button}
                                    </Button>
                                </Link>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
