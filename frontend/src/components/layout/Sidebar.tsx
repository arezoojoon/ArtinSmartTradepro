"use client";

import { useState, useEffect } from "react";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import TenantSwitcher from "./TenantSwitcher";
import { navItems, NavItem } from "@/config/nav";
import { useAuth } from "@/context/AuthContext";
import { LogOut, ChevronLeft, ChevronRight, Settings } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

interface SidebarProps {
    forceExpanded?: boolean;
}

export default function Sidebar({ forceExpanded = false }: SidebarProps) {
    const pathname = usePathname();
    const { user, logout } = useAuth();
    const [isCollapsed, setIsCollapsed] = useState(false);
    const [mounted, setMounted] = useState(false);

    // Hydration fix & LocalStorage persistence
    useEffect(() => {
        setMounted(true);
        if (forceExpanded) {
            setIsCollapsed(false);
            return;
        }
        const stored = localStorage.getItem("sidebar-collapsed");
        if (stored) setIsCollapsed(JSON.parse(stored));
    }, [forceExpanded]);

    const toggleCollapse = () => {
        if (forceExpanded) return;
        const newState = !isCollapsed;
        setIsCollapsed(newState);
        localStorage.setItem("sidebar-collapsed", JSON.stringify(newState));
    };

    const effectiveCollapsed = forceExpanded ? false : isCollapsed;

    if (!mounted) return null; // Avoid hydration mismatch
    // SAFETY: Default to hybrid if user/mode is missing to prevent disappearance
    const safeUser = user || { role: "user", tenant: { mode: "hybrid" } };
    const mode = (safeUser.tenant?.mode || "hybrid") as keyof typeof navItems;
    const items: NavItem[] = navItems[mode] || navItems.hybrid;

    if (!mounted) return null; // Hydration
    // REMOVED: if (!user) return null; -> causing sidebar to vanish if auth context is slightly delayed or malformed

    // Add Admin Panel for Super Admins if not present
    let displayedItems: NavItem[] = [...items];
    if ((user?.role === "super_admin" || user?.role === "admin") && !displayedItems.some(i => i.href === "/admin")) {
        displayedItems.push({ label: "Admin Panel", href: "/admin", icon: Settings });
    }

    return (
        <aside
            className={cn(
                "h-full bg-navy-900 border-r border-navy-800 flex flex-col transition-all duration-300 relative",
                effectiveCollapsed ? "w-20" : "w-64"
            )}
        >
            {/* Toggle Button - Hide if forced expanded (mobile) */}
            {!forceExpanded && (
                <Button
                    variant="ghost"
                    size="icon"
                    onClick={toggleCollapse}
                    className="absolute -right-3 top-6 h-6 w-6 rounded-full border border-navy-700 bg-navy-800 text-navy-400 hover:text-white hover:bg-navy-700 z-50 shadow-md hidden md:flex"
                >
                    {effectiveCollapsed ? <ChevronRight className="h-3 w-3" /> : <ChevronLeft className="h-3 w-3" />}
                </Button>
            )}

            {/* Logo area */}
            <div className={cn(
                "border-b border-navy-800 flex flex-col items-center justify-center gap-4 transition-all overflow-hidden",
                effectiveCollapsed ? "p-4 h-20" : "p-6"
            )}>
                <div className={cn("relative transition-all", effectiveCollapsed ? "w-10 h-10" : "w-16 h-16")}>
                    <Image
                        src="/logo.png"
                        alt="Artin Smart Trade"
                        fill
                        className="object-contain"
                        priority
                    />
                </div>
                {!effectiveCollapsed && <TenantSwitcher />}
                {effectiveCollapsed && <TenantSwitcher collapsed={true} />}
            </div>

            {/* Navigation */}
            <nav className="flex-1 p-3 space-y-1 overflow-y-auto overflow-x-hidden custom-scrollbar">
                {!effectiveCollapsed && (
                    <div className="px-3 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider fade-in">
                        {mode.toUpperCase()} MODE
                    </div>
                )}

                {displayedItems.map((item) => {
                    const isActive = pathname === item.href || (item.href !== "/dashboard" && !item.external && pathname?.startsWith(item.href + "/"));
                    const LinkComponent = item.external ? "a" : Link;
                    const props = item.external ? { href: item.href, target: "_blank", rel: "noopener noreferrer" } : { href: item.href };

                    return (
                        <LinkComponent
                            key={item.href}
                            {...props}
                            className={cn(
                                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all group relative",
                                isActive ? "bg-gold-400/10 text-gold-400" : "text-navy-400 hover:text-white hover:bg-navy-800",
                                effectiveCollapsed && "justify-center px-2"
                            )}
                            title={effectiveCollapsed ? item.label : undefined}
                        >
                            <item.icon className={cn("shrink-0", effectiveCollapsed ? "h-5 w-5" : "h-4 w-4")} />
                            {!effectiveCollapsed && <span className="truncate">{item.label}</span>}
                        </LinkComponent>
                    );
                })}
            </nav>

            {/* Footer / Logout */}
            <div className="p-4 border-t border-navy-800 space-y-4">
                <button
                    onClick={logout}
                    className={cn(
                        "flex w-full items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-red-400 hover:bg-red-400/10 transition-colors",
                        effectiveCollapsed && "justify-center"
                    )}
                    title="Log Out"
                >
                    <LogOut className="h-4 w-4" />
                    {!effectiveCollapsed && <span>Log Out</span>}
                </button>
                {!effectiveCollapsed && <p className="text-xs text-navy-600 text-center truncate">v2.0 • Phase D2</p>}
            </div>
        </aside>
    );
}
