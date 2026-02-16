import Link from "next/link";

export default function PublicFooter() {
    return (
        <footer className="border-t border-white/10 bg-[#08142B]">
            <div className="mx-auto max-w-6xl px-4 py-10">
                <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
                    <div className="text-sm text-white/70">
                        © {new Date().getFullYear()} Artin Smart Trade. All rights reserved.
                    </div>
                    <div className="flex flex-wrap items-center gap-4 text-sm">
                        <Link href="/pricing" className="text-white/80 hover:text-white">
                            Pricing
                        </Link>
                        <Link href="/terms" className="text-white/80 hover:text-white">
                            Terms
                        </Link>
                        <Link href="/privacy" className="text-white/80 hover:text-white">
                            Privacy
                        </Link>
                    </div>
                </div>
                <div className="mt-6 text-xs text-white/50">
                    Artin Smart Trade is a software platform. Always validate trade decisions with professional advisors.
                </div>
            </div>
        </footer>
    );
}
