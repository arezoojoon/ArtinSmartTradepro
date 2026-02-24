"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function RegisterPage() {
    const router = useRouter();

    useEffect(() => {
        // Redirect to pricing page - registration now happens through checkout flow
        router.replace("/pricing");
    }, [router]);

    return (
        <div className="flex items-center justify-center min-h-[40vh]">
            <p className="text-gray-400 text-sm">Redirecting to pricing...</p>
        </div>
    );
}
