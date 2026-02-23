"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { requireAuth, getAccessToken } from "@/lib/auth";
import { TenantSwitcher } from "@/components/tenant/TenantSwitcher";
import { Bell, User } from "lucide-react";

export default function AppLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const router = useRouter();
    const pathname = usePathname();
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        const token = getAccessToken();
        if (!token) {
            router.push("/login");
        } else {
            setMounted(true);
        }
    }, [router]);

    if (!mounted) {
        return null; // Or a loading spinner
    }

    const NAV_ITEMS = [
        { label: "Dashboard", href: "/dashboard" },
        { label: "Hunter", href: "/hunter" },
        { label: "Brain", href: "/crm" },
        { label: "Settings", href: "/settings/tenant" },
    ];

    return (
        <div className="min-h-screen bg-[#071022] text-white">
            {/* Top Bar for App */}
            <header className="sticky top-0 z-40 border-b border-white/10 bg-[#0B1B3A]">
                <div className="flex items-center justify-between px-4 py-2">
                    <div className="flex items-center gap-4">
                        <Link href="/dashboard" className="text-lg font-bold">
                            Artin<span className="text-[#f5a623]">Trade</span>
                        </Link>
                        <div className="h-6 w-px bg-white/10" />
                        <TenantSwitcher />
                    </div>

                    <div className="flex items-center gap-4">
                        <button className="text-white/70 hover:text-white">
                            <Bell className="h-5 w-5" />
                        </button>
                        <div className="h-8 w-8 rounded-full bg-white/10 flex items-center justify-center">
                            <User className="h-5 w-5 text-white/70" />
                        </div>
                    </div>
                </div>
            </header>

            {/* Mobile Bottom Nav */}
            <nav className="fixed bottom-0 z-50 w-full border-t border-white/10 bg-[#0B1B3A] md:hidden">
                <div className="grid grid-cols-4 gap-1 p-2">
                    {NAV_ITEMS.map((item) => (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={[
                                "flex flex-col items-center justify-center rounded-lg py-2 text-xs",
                                pathname.startsWith(item.href)
                                    ? "bg-white/10 text-[#f5a623]"
                                    : "text-white/60",
                            ].join(" ")}
                        >
                            <span>{item.label}</span>
                        </Link>
                    ))}
                </div>
            </nav>

            {/* Desktop Sidebar (Optional / Hidden for now per mobile-first) */}

            {/* Main Content */}
            <main className="pb-20 md:pb-0">
                {children}
            </main>
        </div>
    );
}
