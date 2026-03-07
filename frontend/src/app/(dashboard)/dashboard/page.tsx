"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function DashboardRedirect() {
    const router = useRouter();
    useEffect(() => {
        router.replace("/command-center");
    }, [router]);
    return (
        <div className="min-h-screen bg-[#050A15] flex items-center justify-center">
            <p className="text-slate-400 text-sm">Redirecting to Command Center…</p>
        </div>
    );
}
