"use client";

import { useState, useEffect, useCallback } from "react";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import TenantSwitcher from "./TenantSwitcher";
import { navItems, adminNavItem, filterNavItems, NavItem, TenantMode, UserRole } from "@/config/nav";
import { useAuth } from "@/context/AuthContext";
import { LogOut, ChevronLeft, ChevronRight, ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

interface SidebarProps {
    forceExpanded?: boolean;
    onItemClick?: () => void;
}

export default function Sidebar({ forceExpanded = false, onItemClick }: SidebarProps) {
    const pathname = usePathname();
    const { user, logout } = useAuth();
    const [isCollapsed, setIsCollapsed] = useState(false);
    const [mounted, setMounted] = useState(false);
    const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({});

    // Hydration fix & LocalStorage persistence
    useEffect(() => {
        setMounted(true);
        if (forceExpanded) {
            setIsCollapsed(false);
            return;
        }
        const stored = localStorage.getItem("sidebar-collapsed");
        if (stored) setIsCollapsed(JSON.parse(stored));

        const storedSections = localStorage.getItem("sidebar-sections");
        if (storedSections) {
            try { setExpandedSections(JSON.parse(storedSections)); } catch { /* ignore */ }
        }
    }, [forceExpanded]);

    // Auto-expand the section that contains the current route
    useEffect(() => {
        if (!pathname) return;
        const allItems = getDisplayedItems();
        for (const item of allItems) {
            if (item.children) {
                const childActive = item.children.some(c => isRouteActive(c.href, pathname));
                if (childActive) {
                    setExpandedSections(prev => {
                        if (prev[item.href]) return prev; // already open
                        const next = { ...prev, [item.href]: true };
                        localStorage.setItem("sidebar-sections", JSON.stringify(next));
                        return next;
                    });
                }
            }
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [pathname]);

    const toggleCollapse = () => {
        if (forceExpanded) return;
        const newState = !isCollapsed;
        setIsCollapsed(newState);
        localStorage.setItem("sidebar-collapsed", JSON.stringify(newState));
    };

    const toggleSection = (href: string) => {
        setExpandedSections(prev => {
            const next = { ...prev, [href]: !prev[href] };
            localStorage.setItem("sidebar-sections", JSON.stringify(next));
            return next;
        });
    };

    const effectiveCollapsed = forceExpanded ? false : isCollapsed;

    // SAFETY: Default to hybrid if user/mode is missing
    const safeUser = user || { role: "user" as UserRole, tenant: { mode: "hybrid" as TenantMode } };
    const mode = ((safeUser as any).tenant?.mode || "hybrid") as TenantMode;
    const role = ((safeUser as any).role || "user") as UserRole;

    const getDisplayedItems = useCallback((): NavItem[] => {
        let items = filterNavItems(navItems, mode, role);
        // Add Super Admin panel ONLY for platform super_admin (NOT tenant admin)
        const isSuperUser = (user as any)?.is_superuser === true || role === "super_admin";
        if (isSuperUser && !items.some(i => i.href === "/admin/super")) {
            items = [...items, adminNavItem];
        }
        return items;
    }, [mode, role, user]);

    if (!mounted) return null;

    const displayedItems = getDisplayedItems();

    return (
        <aside
            className={cn(
                "h-full bg-[#0e1e33] border-r border-[#1e3a5f] flex flex-col transition-all duration-300 relative",
                effectiveCollapsed ? "w-20" : "w-64"
            )}
        >
            {/* Toggle Button */}
            {!forceExpanded && (
                <Button
                    variant="ghost"
                    size="icon"
                    onClick={toggleCollapse}
                    className="absolute -right-3 top-6 h-6 w-6 rounded-full border-[#1e3a5f] bg-[#12253f] text-navy-400 hover:text-white hover:bg-[#1e3a5f] z-50 shadow-md hidden md:flex"
                >
                    {effectiveCollapsed ? <ChevronRight className="h-3 w-3" /> : <ChevronLeft className="h-3 w-3" />}
                </Button>
            )}

            {/* Logo area */}
            <div className={cn(
                "border-b border-[#1e3a5f] flex flex-col items-center justify-center gap-4 transition-all overflow-hidden",
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
            <nav className="flex-1 p-3 space-y-0.5 overflow-y-auto overflow-x-hidden custom-scrollbar">
                {displayedItems.map((item) => (
                    <NavEntry
                        key={item.href}
                        item={item}
                        pathname={pathname}
                        collapsed={effectiveCollapsed}
                        expanded={!!expandedSections[item.href]}
                        onToggle={() => toggleSection(item.href)}
                        onItemClick={onItemClick}
                    />
                ))}
            </nav>

            {/* Footer / Logout */}
            <div className="border-t border-[#1e3a5f] space-y-4">
                <button
                    onClick={() => {
                        onItemClick?.();
                        logout();
                    }}
                    className={cn(
                        "flex w-full items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-red-400 hover:bg-red-400/10 transition-colors",
                        effectiveCollapsed && "justify-center"
                    )}
                    title="Log Out"
                >
                    <LogOut className="h-4 w-4" />
                    {!effectiveCollapsed && <span>Log Out</span>}
                </button>
                {!effectiveCollapsed && <p className="text-xs text-navy-600 text-center truncate">v3.0 • Unified</p>}
            </div>
        </aside>
    );
}

// ─── NavEntry Component ─────────────────────────────────────────────────────────
interface NavEntryProps {
    item: NavItem;
    pathname: string;
    collapsed: boolean;
    expanded: boolean;
    onToggle: () => void;
    onItemClick?: () => void;
}

function NavEntry({ item, pathname, collapsed, expanded, onToggle, onItemClick }: NavEntryProps) {
    const hasChildren = item.children && item.children.length > 0;
    const isActive = isRouteActive(item.href, pathname);
    const isChildActive = hasChildren && item.children!.some(c => isRouteActive(c.href, pathname));
    const isHighlighted = isActive || isChildActive;

    // ── Parent with children ──
    if (hasChildren) {
        return (
            <div className="space-y-0.5">
                {/* Parent row */}
                <button
                    onClick={onToggle}
                    className={cn(
                        "flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm font-medium transition-all group relative",
                        isHighlighted
                            ? "bg-[#f5a623]/10 text-[#f5a623]"
                            : "text-gray-100 hover:text-white hover:bg-[#12253f]",
                        collapsed && "justify-center px-2"
                    )}
                    title={collapsed ? item.label : undefined}
                >
                    <item.icon className={cn("shrink-0", collapsed ? "h-5 w-5" : "h-4 w-4")} />
                    {!collapsed && (
                        <>
                            <span className="truncate flex-1 text-left">{item.label}</span>
                            <ChevronDown
                                className={cn(
                                    "h-3.5 w-3.5 shrink-0 transition-transform duration-200",
                                    expanded ? "rotate-0" : "-rotate-90",
                                    isHighlighted ? "text-[#f5a623]/60" : "text-gray-500"
                                )}
                            />
                        </>
                    )}
                </button>

                {/* Children */}
                {!collapsed && expanded && (
                    <div className="ml-4 pl-3 border-l border-[#1e3a5f] space-y-0.5">
                        {item.children!.map(child => {
                            const childActive = isRouteActive(child.href, pathname);
                            return (
                                <Link
                                    key={child.href}
                                    href={child.href}
                                    onClick={onItemClick}
                                    className={cn(
                                        "flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-all group",
                                        childActive
                                            ? "bg-[#f5a623]/10 text-[#f5a623] font-medium"
                                            : "text-gray-400 hover:text-white hover:bg-[#12253f]"
                                    )}
                                >
                                    <child.icon className="h-3.5 w-3.5 shrink-0" />
                                    <span className="truncate">{child.label}</span>
                                </Link>
                            );
                        })}
                    </div>
                )}
            </div>
        );
    }

    // ── Leaf item ──
    const LinkComponent = item.external ? "a" : Link;
    const props = item.external
        ? { href: item.href, target: "_blank", rel: "noopener noreferrer" }
        : { href: item.href };

    return (
        <LinkComponent
            {...props}
            onClick={onItemClick}
            className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all group relative",
                isActive ? "bg-[#f5a623]/10 text-[#f5a623]" : "text-gray-100 hover:text-white hover:bg-[#12253f]",
                collapsed && "justify-center px-2"
            )}
            title={collapsed ? item.label : undefined}
        >
            <item.icon className={cn("shrink-0", collapsed ? "h-5 w-5" : "h-4 w-4")} />
            {!collapsed && <span className="truncate">{item.label}</span>}
        </LinkComponent>
    );
}

// ─── Helpers ────────────────────────────────────────────────────────────────────
function isRouteActive(href: string, pathname: string): boolean {
    if (!pathname) return false;
    if (pathname === href) return true;
    // Prevent /command-center matching / etc.
    if (href === "/" || href === "/dashboard" || href === "/command-center") {
        return pathname === href;
    }
    return pathname.startsWith(href + "/");
}
