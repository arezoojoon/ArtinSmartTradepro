import PublicHeader from "../components/public/PublicHeader";
import PublicFooter from "../components/public/PublicFooter";

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-[#071022] text-white">
      <PublicHeader />
      <main className="mx-auto max-w-3xl px-4 py-14">
        <h1 className="text-3xl font-semibold">Terms of Service</h1>
        <p className="mt-4 text-sm text-white/70">
          This page defines the terms for using Artin Smart Trade. Content will be finalized with legal review.
        </p>

        <div className="mt-8 space-y-4 text-sm text-white/75">
          <p>1) You are responsible for verifying trade decisions and compliance requirements.</p>
          <p>2) The platform provides software tools and informational outputs; it is not legal or financial advice.</p>
          <p>3) Subscription fees are billed according to your selected plan and renewal terms.</p>
          <p>4) Misuse, scraping abuse, or illegal activity will result in suspension.</p>
        </div>
      </main>
      <PublicFooter />
    </div>
  );
}
