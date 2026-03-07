"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function AcquisitionRedirect() {
    const router = useRouter();
    useEffect(() => { router.replace("/acquisition/overview"); }, [router]);
    return null;
}
