"use client";

import Link from "next/link";
import { useState } from "react";

const NAV = [
    { label: "Features", href: "/#features" },
    { label: "Pricing", href: "/pricing" },
    { label: "Success Stories", href: "/#stories" },
    { label: "About", href: "/#about" },
];

export default function PublicHeader() {
    const [open, setOpen] = useState(false);

    return (
        <header className="sticky top-0 z-50 border-b border-white/10 bg-[#0B1B3A]/95 backdrop-blur">
            <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
                <Link href="/" className="flex items-center gap-2">
                    <span className="text-base font-semibold tracking-tight text-white">
                        Artin <span className="text-[#f5a623]">Smart Trade</span>
                    </span>
                    <span className="hidden rounded-full border border-white/15 px-2 py-0.5 text-xs text-white/70 md:inline">
                        AI Trade OS
                    </span>
                </Link>

                <nav className="hidden items-center gap-6 md:flex">
                    {NAV.map((item) => (
                        <Link
                            key={item.href}
                            href={item.href}
                            className="text-sm text-white/80 hover:text-white"
                        >
                            {item.label}
                        </Link>
                    ))}
                </nav>

                <div className="hidden items-center gap-3 md:flex">
                    <Link
                        href="/login"
                        className="rounded-xl border border-white/15 px-4 py-2 text-sm text-white hover:border-white/25"
                    >
                        Login
                    </Link>
                    <Link
                        href="/pricing"
                        className="rounded-xl bg-[#f5a623] px-4 py-2 text-sm font-medium text-[#0B1B3A] hover:opacity-95"
                    >
                        Get Started
                    </Link>
                </div>

                <button
                    type="button"
                    className="inline-flex items-center justify-center rounded-xl border border-white/15 p-2 text-white md:hidden"
                    aria-label="Open menu"
                    onClick={() => setOpen((v) => !v)}
                >
                    <span className="text-lg leading-none">{open ? "×" : "≡"}</span>
                </button>
            </div>

            {open && (
                <div className="border-t border-white/10 bg-[#0B1B3A] md:hidden">
                    <div className="mx-auto max-w-6xl px-4 py-3">
                        <div className="flex flex-col gap-2">
                            {NAV.map((item) => (
                                <Link
                                    key={item.href}
                                    href={item.href}
                                    className="rounded-xl px-3 py-2 text-sm text-white/85 hover:bg-white/5"
                                    onClick={() => setOpen(false)}
                                >
                                    {item.label}
                                </Link>
                            ))}
                            <div className="mt-2 grid grid-cols-2 gap-2">
                                <Link
                                    href="/login"
                                    className="rounded-xl border border-white/15 px-3 py-2 text-center text-sm text-white"
                                    onClick={() => setOpen(false)}
                                >
                                    Login
                                </Link>
                                <Link
                                    href="/pricing"
                                    className="rounded-xl bg-[#f5a623] px-3 py-2 text-center text-sm font-medium text-[#0B1B3A]"
                                    onClick={() => setOpen(false)}
                                >
                                    Get Started
                                </Link>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </header>
    );
}
