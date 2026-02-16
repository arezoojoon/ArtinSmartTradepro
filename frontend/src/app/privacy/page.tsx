import PublicHeader from "../components/public/PublicHeader";
import PublicFooter from "../components/public/PublicFooter";

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-[#071022] text-white">
      <PublicHeader />
      <main className="mx-auto max-w-3xl px-4 py-14">
        <h1 className="text-3xl font-semibold">Privacy Policy</h1>
        <p className="mt-4 text-sm text-white/70">
          This page explains how Artin Smart Trade handles data. Content will be finalized with compliance review.
        </p>

        <div className="mt-8 space-y-4 text-sm text-white/75">
          <p>1) We store account data, CRM objects, and activity logs to provide the service.</p>
          <p>2) We do not sell private customer data. Aggregated analytics may be used to improve the product.</p>
          <p>3) Authentication tokens and sessions are protected using standard security practices.</p>
          <p>4) You can request deletion/export of your data according to applicable laws and your plan.</p>
        </div>
      </main>
      <PublicFooter />
    </div>
  );
}
