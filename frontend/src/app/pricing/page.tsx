import Link from "next/link";
import PublicHeader from "../components/public/PublicHeader";
import PublicFooter from "../components/public/PublicFooter";

const TIERS = [
  {
    name: "Professional",
    code: "professional",
    price: 299,
    period: "mo",
    highlight: false,
    features: [
      "Hunter (Lead Scraper)",
      "WhatsApp Bot (Single-channel)",
      "Basic CRM",
      "5 Users included",
      "Email Support",
    ],
    cta: { label: "Start Free Trial", href: "/checkout?plan=professional" },
  },
  {
    name: "Enterprise",
    code: "enterprise",
    price: 999,
    period: "mo",
    highlight: true,
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
    cta: { label: "Start Free Trial", href: "/checkout?plan=enterprise" },
  },
  {
    name: "White Label",
    code: "whitelabel",
    price: 2999,
    period: "mo + setup",
    highlight: false,
    features: [
      "Everything in Enterprise",
      "Custom Domain & Branding",
      "Dedicated Infrastructure",
      "White-glove Onboarding",
      "SLA & Enterprise Support",
    ],
    cta: { label: "Contact Sales", href: "/#about" },
  },
];

export default function PricingPage() {
  return (
    <div className="min-h-screen bg-[#0a1628] text-white">
      <PublicHeader />

      <main className="mx-auto max-w-6xl px-4 py-14">
        <div className="text-center">
          <h1 className="text-3xl font-bold md:text-4xl text-white">
            Simple, Transparent Pricing
          </h1>
          <p className="mt-3 max-w-2xl mx-auto text-sm text-gray-400 md:text-base">
            Choose your plan and start with a <span className="text-[#f5a623] font-semibold">3-day free trial</span>. No credit card required to get started.
          </p>
        </div>

        <div className="mt-12 grid gap-6 md:grid-cols-3">
          {TIERS.map((tier) => (
            <div
              key={tier.name}
              className={[
                "rounded-2xl border p-6 flex flex-col transition-all hover:scale-[1.02]",
                tier.highlight
                  ? "border-[#f5a623]/50 bg-[#0e1e33] shadow-[0_0_20px_rgba(245,166,35,0.1)] ring-1 ring-[#f5a623]/20"
                  : "border-[#1e3a5f] bg-[#0e1e33]/50",
              ].join(" ")}
            >
              <div className="flex items-center justify-between">
                <div className="text-lg font-bold">{tier.name}</div>
                {tier.highlight && (
                  <span className="rounded-full bg-[#f5a623] px-3 py-1 text-[10px] font-bold text-[#0a1628] uppercase tracking-wider">
                    Most Popular
                  </span>
                )}
              </div>

              <div className="mt-6 flex items-baseline gap-1">
                <span className="text-3xl font-bold text-white">${tier.price.toLocaleString()}</span>
                <span className="text-gray-400 text-sm">/{tier.period}</span>
              </div>

              {tier.code !== "whitelabel" && (
                <p className="mt-2 text-xs text-[#f5a623]/80 font-medium">
                  3 days free — then ${tier.price}/mo
                </p>
              )}

              <ul className="mt-8 space-y-3 flex-1">
                {tier.features.map((f) => (
                  <li key={f} className="flex gap-3 text-sm text-gray-300">
                    <span className="text-[#f5a623] font-bold shrink-0">✓</span>
                    <span>{f}</span>
                  </li>
                ))}
              </ul>

              <Link
                href={tier.cta.href}
                className={[
                  "mt-8 block rounded-xl px-4 py-3 text-center text-sm font-bold transition-colors",
                  tier.highlight
                    ? "bg-[#f5a623] text-[#0a1628] hover:bg-[#e0951a]"
                    : "border border-[#1e3a5f] text-white hover:bg-[#12253f] hover:border-[#f5a623]/30",
                ].join(" ")}
              >
                {tier.cta.label}
              </Link>
            </div>
          ))}
        </div>

        {/* FAQ / Trust */}
        <div className="mt-16 text-center">
          <p className="text-sm text-gray-500">
            All plans include SSL encryption, 99.9% uptime SLA, and GDPR compliance.
          </p>
          <p className="mt-2 text-sm text-gray-500">
            Already have an account?{" "}
            <Link href="/login" className="text-[#f5a623] hover:underline font-medium">
              Sign in
            </Link>
          </p>
        </div>
      </main>

      <PublicFooter />
    </div>
  );
}
