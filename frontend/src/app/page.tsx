import Link from "next/link";
import Image from "next/image";
// We inline the old header because the new PublicHeader component attempts to use new menu structures which user dislikes.
// import PublicHeader from "./components/public/PublicHeader"; 
import PublicFooter from "./components/public/PublicFooter";

export default function HomePage() {
  return (
    <div className="min-h-screen bg-[#071022] text-white">
      {/* Old PublicHeader Inlined to restore exact menu structure */}
      <header className="fixed top-0 z-50 w-full border-b border-white/5 bg-[#071022]/80 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-2">
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
          </div>

          <nav className="hidden md:flex items-center gap-8">
            <Link href="#features" className="text-sm font-medium text-white/70 transition-colors hover:text-white">
              Features
            </Link>
            <Link href="/pricing" className="text-sm font-medium text-white/70 transition-colors hover:text-white">
              Pricing
            </Link>
            <Link href="#stories" className="text-sm font-medium text-white/70 transition-colors hover:text-white">
              Success Stories
            </Link>
          </nav>

          <div className="flex items-center gap-4">
            <Link
              href="/login"
              className="text-sm font-medium text-white/70 transition-colors hover:text-white"
            >
              Login
            </Link>
            <Link
              href="/register"
              className="rounded-full bg-[#f5a623] px-4 py-2 text-sm font-semibold text-[#071022] transition-colors hover:bg-[#B5952F]"
            >
              Get Started
            </Link>
          </div>
        </div>
      </header>

      <main className="pt-16">
        {/* Hero */}
        <section className="mx-auto max-w-6xl px-4 py-16 md:py-24">
          <div className="max-w-3xl">
            <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-white/80">
              <span className="text-[#f5a623]">AI Trade OS</span>
              <span>Mobile-first. Data-driven. Built for exporters.</span>
            </div>

            <h1 className="mt-6 text-4xl font-semibold leading-tight md:text-5xl">
              Artin Smart Trade{" "}
              <span className="text-[#f5a623]">— AI Trade Operating System</span>
            </h1>

            <p className="mt-5 text-base text-white/75 md:text-lg">
              One platform that unifies intelligence, execution, and communication for global commerce.
              You don’t trade products — you trade data + price gaps between markets.
            </p>

            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Link
                href="/register"
                className="rounded-2xl bg-[#f5a623] px-6 py-3 text-center text-sm font-semibold text-[#0B1B3A]"
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

        {/* Note: The Power Triad section was removed as requested ("Old navy/gold landing... not the new AI Trade OS triad section") */}

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
