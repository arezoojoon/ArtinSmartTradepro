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
    <div className="min-h-screen bg-[#0a1628] text-white">
      <PublicHeader />

      <main className="mx-auto max-w-6xl px-4 py-14">
        <h1 className="text-3xl font-bold md:text-4xl text-white">Pricing Plans</h1>
        <p className="mt-2 max-w-2xl text-sm text-gray-400 md:text-base">
          Choose a plan that matches your trade operation. Upgrade anytime to unlock advanced AI intelligence.
        </p>

        <div className="mt-10 grid gap-6 md:grid-cols-3">
          {TIERS.map((tier) => (
            <div
              key={tier.name}
              className={[
                "rounded-2xl border p-6 flex flex-col transition-all hover:scale-[1.02]",
                tier.highlight
                  ? "border-[#f5a623]/50 bg-[#0e1e33] shadow-[0_0_20px_rgba(245,166,35,0.1)]"
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
                <span className="text-3xl font-bold text-white">{tier.price.split('/')[0]}</span>
                <span className="text-gray-400 text-sm">/{tier.price.split('/')[1]}</span>
              </div>

              <ul className="mt-8 space-y-3 flex-1">
                {tier.features.map((f) => (
                  <li key={f} className="flex gap-3 text-sm text-gray-300">
                    <span className="text-[#f5a623] font-bold">✓</span>
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
      </main>

      <PublicFooter />
    </div>
  );
}
