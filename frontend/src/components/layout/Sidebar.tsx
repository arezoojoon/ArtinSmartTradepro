"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import TenantSwitcher from "./TenantSwitcher";
import {
    LayoutDashboard,
    Users,
    Search,
    MessageCircle,
    BarChart3,
    Wallet,
    Globe,
    Mic,
    Eye,
    Brain,
    Building2,
    Repeat,
    Megaphone,
    Settings,
    UserCircle,
    Crosshair,
    Package,
    Calculator,
    Briefcase,
    Warehouse,
    CalendarDays,
    Bot,
    Link2,
    ShoppingCart
} from "lucide-react";

interface NavItem {
    label: string;
    href: string;
    icon: any;
    external?: boolean;
}

import { useAuth } from "@/context/AuthContext";
import { LogOut } from "lucide-react";

// Define all possible items
const allNavItems: NavItem[] = [
    // Common
    { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },

    // Buyer Specific
    { label: "Buyer Control Tower", href: "/buyer", icon: LayoutDashboard }, // Replaces standard dashboard for Buyer
    { label: "Sourcing OS", href: "/sourcing/rfqs", icon: Package },
    { label: "Trade Intelligence", href: "/trade", icon: Globe },
    { label: "Deal Flow", href: "/brain/opportunities", icon: Briefcase },
    { label: "Calculators", href: "/finance/simulator", icon: Calculator },
    { label: "Operations", href: "/operations/inventory", icon: Warehouse },

    // Seller Specific
    { label: "Seller Control Tower", href: "/seller", icon: LayoutDashboard }, // Replaces standard dashboard for Seller
    { label: "CRM", href: "/crm", icon: Users },
    { label: "Hunter", href: "/hunter", icon: Search },
    { label: "Campaigns", href: "/crm/campaigns", icon: Megaphone },
    { label: "Competitor Intel", href: "/hunter/competitors", icon: Crosshair },
    { label: "WhatsApp", href: "/whatsapp", icon: MessageCircle },
    { label: "Catalog", href: "/whatsapp/catalog", icon: Package },

    // Universal
    { label: "Wallet", href: "/wallet", icon: Wallet },
    { label: "Settings", href: "/settings", icon: Settings },
];

export default function Sidebar() {
    const pathname = usePathname();
    const { user, logout } = useAuth();

    // Determine Nav Items based on Mode
    const mode = user?.tenant?.mode || "hybrid";

    let displayedItems: NavItem[] = [];

    if (mode === "buyer") {
        displayedItems = [
            { label: "Dashboard", href: "/buyer", icon: LayoutDashboard },
            { label: "Sourcing OS", href: "/sourcing/rfqs", icon: Package },
            { label: "Trade Intelligence", href: "/trade", icon: Globe },
            { label: "Deal Flow (AI)", href: "/brain/opportunities", icon: Briefcase },
            { label: "Operations", href: "/operations/inventory", icon: Warehouse },
            { label: "Wallet", href: "/wallet", icon: Wallet },
        ];
    } else if (mode === "seller") {
        displayedItems = [
            { label: "Dashboard", href: "/seller", icon: LayoutDashboard },
            { label: "CRM", href: "/crm", icon: Users },
            { label: "Hunter (Leads)", href: "/hunter", icon: Search },
            { label: "Campaigns", href: "/crm/campaigns", icon: Megaphone },
            { label: "Market Intel", href: "/hunter/competitors", icon: Crosshair },
            { label: "WhatsApp Sales", href: "/whatsapp", icon: MessageCircle },
            { label: "Wallet", href: "/wallet", icon: Wallet },
        ];
    } else {
        // Hybrid - Show key items from both
        displayedItems = [
            { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
            { label: "CRM (Sales)", href: "/crm", icon: Users },
            { label: "Hunter (Leads)", href: "/hunter", icon: Search },
            { label: "Sourcing", href: "/sourcing/rfqs", icon: Package },
            { label: "WhatsApp", href: "/whatsapp", icon: MessageCircle },
            { label: "AI Brain", href: "/brain", icon: Brain },
            { label: "Wallet", href: "/wallet", icon: Wallet },
            { label: "Settings", href: "/settings", icon: Settings },
        ];
    }

    // Add Admin Panel for Super Admins
    if (user?.role === "super_admin" || user?.role === "admin") {
        // Check if already added (to avoid dupes in hybrid)
        const hasAdmin = displayedItems.some(i => i.href === "/admin");
        if (!hasAdmin) {
            displayedItems.push({ label: "Admin Panel", href: "/admin", icon: Settings });
        }
    }

    if (!user) return null; // Don't render sidebar if not logged in

    return (
        <aside className="w-64 h-full bg-navy-900 border-r border-navy-800 flex flex-col">
            {/* Logo */}
            <div className="p-6 border-b border-navy-800 flex flex-col items-center justify-center gap-4">
                <div className="relative w-16 h-16">
                    <Image
                        src="/logo.png"
                        alt="Artin Smart Trade"
                        fill
                        className="object-contain"
                        priority
                    />
                </div>
                <TenantSwitcher />
            </div>

            {/* Navigation */}
            <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
                <div className="px-3 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                    {mode.toUpperCase()} MODE
                </div>
                {displayedItems.map((item) => {
                    const isActive = pathname === item.href || (item.href !== "/dashboard" && !item.external && pathname?.startsWith(item.href + "/"));
                    const LinkComponent = item.external ? "a" : Link;
                    const props = item.external ? { href: item.href, target: "_blank", rel: "noopener noreferrer" } : { href: item.href };

                    return (
                        <LinkComponent
                            key={item.href}
                            {...props}
                            className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${isActive
                                ? "bg-gold-400/10 text-gold-400"
                                : "text-navy-400 hover:text-white hover:bg-navy-800"
                                }`}
                        >
                            <item.icon className="h-4 w-4" />
                            {item.label}
                        </LinkComponent>
                    );
                })}
            </nav>

            {/* Footer / Logout */}
            <div className="p-4 border-t border-navy-800 space-y-4">
                <button
                    onClick={logout}
                    className="flex w-full items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-red-400 hover:bg-red-400/10 transition-colors"
                >
                    <LogOut className="h-4 w-4" />
                    Log Out
                </button>
                <p className="text-xs text-navy-600 text-center">v2.0 • Phase D2</p>
            </div>
        </aside>
    );
}
