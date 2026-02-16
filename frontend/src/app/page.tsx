import Link from "next/link";
import PublicHeader from "./components/public/PublicHeader";
import PublicFooter from "./components/public/PublicFooter";

export default function HomePage() {
  return (
    <div className="min-h-screen bg-[#071022] text-white">
      <PublicHeader />

      <main>
        {/* Hero */}
        <section className="mx-auto max-w-6xl px-4 py-16 md:py-24">
          <div className="max-w-3xl">
            <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-white/80">
              <span className="text-[#D4AF37]">AI Trade OS</span>
              <span>Mobile-first. Data-driven. Built for exporters.</span>
            </div>

            <h1 className="mt-6 text-4xl font-semibold leading-tight md:text-5xl">
              Artin Smart Trade{" "}
              <span className="text-[#D4AF37]">— AI Trade Operating System</span>
            </h1>

            <p className="mt-5 text-base text-white/75 md:text-lg">
              One platform that unifies intelligence, execution, and communication for global commerce.
              You don’t trade products — you trade data + price gaps between markets.
            </p>

            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Link
                href="/auth/register"
                className="rounded-2xl bg-[#D4AF37] px-6 py-3 text-center text-sm font-semibold text-[#0B1B3A]"
              >
                Get Started
              </Link>
              <Link
                href="/pricing"
                className="rounded-2xl border border-white/15 px-6 py-3 text-center text-sm text-white hover:border-white/25"
              >
                View Pricing
              </Link>
            </div>
          </div>
        </section>

        {/* Power Triad */}
        <section id="features" className="bg-[#08142B]">
          <div className="mx-auto max-w-6xl px-4 py-14 md:py-18">
            <h2 className="text-2xl font-semibold md:text-3xl">
              The Power Triad
            </h2>
            <p className="mt-2 max-w-2xl text-sm text-white/70 md:text-base">
              The core system that replaces an entire department: Eyes to find opportunities,
              Brain to decide, Voice to execute.
            </p>

            <div className="mt-8 grid gap-4 md:grid-cols-3">
              <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
                <div className="text-sm font-semibold text-[#D4AF37]">Eyes</div>
                <div className="mt-2 text-lg font-semibold">Hunter Lead Generation</div>
                <p className="mt-2 text-sm text-white/70">
                  Finds buyers and competitors from trade data and market signals — fast, structured, and actionable.
                </p>
              </div>

              <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
                <div className="text-sm font-semibold text-[#D4AF37]">Brain</div>
                <div className="mt-2 text-lg font-semibold">CRM + Intelligence</div>
                <p className="mt-2 text-sm text-white/70">
                  Unifies deals, pipelines, cash flow, and risk analysis into one decision engine.
                </p>
              </div>

              <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
                <div className="text-sm font-semibold text-[#D4AF37]">Voice</div>
                <div className="mt-2 text-lg font-semibold">Automation & Follow-ups</div>
                <p className="mt-2 text-sm text-white/70">
                  WhatsApp/Email automation with real CRM context — turns leads into invoices with minimal effort.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Stories */}
        <section id="stories" className="mx-auto max-w-6xl px-4 py-14">
          <h3 className="text-xl font-semibold md:text-2xl">Success Stories</h3>
          <p className="mt-2 max-w-2xl text-sm text-white/70 md:text-base">
            Case studies will appear here. Keep this section as a placeholder for now.
          </p>
        </section>

        {/* About */}
        <section id="about" className="bg-[#08142B]">
          <div className="mx-auto max-w-6xl px-4 py-14">
            <h3 className="text-xl font-semibold md:text-2xl">About</h3>
            <p className="mt-2 max-w-3xl text-sm text-white/70 md:text-base">
              Artin Smart Trade is designed for data-driven exporters and importers. It combines
              trade intelligence, CRM execution, and automation into a single mobile-first platform.
            </p>
          </div>
        </section>
      </main>

      <PublicFooter />
    </div>
  );
}
