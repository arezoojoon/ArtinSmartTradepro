import Link from "next/link";
import PublicHeader from "../components/public/PublicHeader";
import PublicFooter from "../components/public/PublicFooter";

const TIERS = [
  {
    name: "Professional",
    price: "$299/mo",
    highlight: false,
    features: ["Hunter (Lead Scraper)", "WhatsApp Bot (Single-channel)", "Basic CRM"],
    cta: { label: "Start Professional", href: "/register" },
  },
  {
    name: "Enterprise",
    price: "$999/mo",
    highlight: true,
    features: [
      "Full Trade Intelligence (Freight/FX/Risk)",
      "Omnichannel Bots (WhatsApp + Telegram)",
      "Broadcast Campaigns",
      "Competitor Tracking",
    ],
    cta: { label: "Start Enterprise", href: "/register" },
  },
  {
    name: "White Label",
    price: "$2,999/mo + setup",
    highlight: false,
    features: ["Custom Domain & Branding", "Dedicated Infrastructure", "Enterprise Support"],
    cta: { label: "Contact Sales", href: "/#about" },
  },
];

export default function PricingPage() {
  return (
    <div className="min-h-screen bg-[#071022] text-white">
      <PublicHeader />

      <main className="mx-auto max-w-6xl px-4 py-14">
        <h1 className="text-3xl font-semibold md:text-4xl">Pricing</h1>
        <p className="mt-2 max-w-2xl text-sm text-white/70 md:text-base">
          Choose a plan that matches your trade operation. Upgrade anytime.
        </p>

        <div className="mt-10 grid gap-4 md:grid-cols-3">
          {TIERS.map((tier) => (
            <div
              key={tier.name}
              className={[
                "rounded-2xl border p-6",
                tier.highlight
                  ? "border-[#f5a623]/50 bg-[#0B1B3A]"
                  : "border-white/10 bg-white/5",
              ].join(" ")}
            >
              <div className="flex items-center justify-between">
                <div className="text-lg font-semibold">{tier.name}</div>
                {tier.highlight && (
                  <span className="rounded-full bg-[#f5a623] px-2 py-1 text-xs font-semibold text-[#0B1B3A]">
                    Most Popular
                  </span>
                )}
              </div>

              <div className="mt-4 text-2xl font-semibold text-[#f5a623]">
                {tier.price}
              </div>

              <ul className="mt-5 space-y-2 text-sm text-white/75">
                {tier.features.map((f) => (
                  <li key={f} className="flex gap-2">
                    <span className="text-[#f5a623]">•</span>
                    <span>{f}</span>
                  </li>
                ))}
              </ul>

              <Link
                href={tier.cta.href}
                className={[
                  "mt-6 block rounded-2xl px-4 py-3 text-center text-sm font-semibold",
                  tier.highlight
                    ? "bg-[#f5a623] text-[#0B1B3A]"
                    : "border border-white/15 text-white hover:border-white/25",
                ].join(" ")}
              >
                {tier.cta.label}
              </Link>
            </div>
          ))}
        </div>
      </main>

      <PublicFooter />
    </div>
  );
}
