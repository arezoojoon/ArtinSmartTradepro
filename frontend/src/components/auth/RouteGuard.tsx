"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { navItems, filterNavItems } from "@/config/nav";
import { Loader2 } from "lucide-react";

export default function RouteGuard({ children }: { children: React.ReactNode }) {
    const { user, loading, isAuthenticated } = useAuth();
    const router = useRouter();
    const pathname = usePathname();
    const [authorized, setAuthorized] = useState(false);

    useEffect(() => {
        if (loading) return;

        // Not authenticated -> Login
        if (!isAuthenticated || !user) {
            router.push("/login");
            return;
        }

        // Check if user has permission for the current path
        const checkAccess = () => {
            // Get user's mode and role
            const mode = user.tenant?.mode || "hybrid";
            const role = user.role || "user";

            // Allow root and command center universally for authenticated users
            if (pathname === "/" || pathname === "/command-center") return true;

            // Flatten the visible nav items based on user's identity
            const visibleItems = filterNavItems(navItems, mode, role);

            // Helper function to check if a path is within the allowed items
            const isPathAllowed = (items: typeof navItems, targetPath: string): boolean => {
                for (const item of items) {
                    // Exact match or active parent match
                    if (targetPath === item.href || targetPath.startsWith(item.href + "/")) {
                        return true;
                    }
                    if (item.children && isPathAllowed(item.children, targetPath)) {
                        return true;
                    }
                }
                return false;
            };

            return isPathAllowed(visibleItems, pathname);
        };

        const hasAccess = checkAccess();

        if (!hasAccess) {
            // Redirect to command center if trying to access a restricted page
            router.push("/command-center");
        } else {
            setAuthorized(true);
        }
    }, [user, loading, isAuthenticated, pathname, router]);

    if (loading || !authorized) {
        return (
            <div className="min-h-screen bg-[#050A15] flex items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-[#D4AF37]" />
            </div>
        );
    }

    return <>{children}</>;
}
