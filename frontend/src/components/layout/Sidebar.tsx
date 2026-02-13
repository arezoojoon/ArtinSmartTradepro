"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
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

const navItems: NavItem[] = [
    { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { label: "CRM", href: "/crm", icon: Users },
    { label: "Companies", href: "/crm/companies", icon: Building2 },
    { label: "Campaigns", href: "/crm/campaigns", icon: Megaphone },
    { label: "Follow-Ups", href: "/crm/followups", icon: Repeat },
    { label: "Voice Intelligence", href: "/crm/voice", icon: Mic },
    { label: "Vision Intelligence", href: "/crm/vision", icon: Eye },
    { label: "Hunter", href: "/hunter", icon: Search },
    { label: "Competitor Intel", href: "/hunter/competitors", icon: Crosshair },
    { label: "Sourcing OS", href: "/sourcing/rfqs", icon: Package },
    { label: "Financial OS", href: "/finance/simulator", icon: Calculator },
    { label: "Deal Flow", href: "/brain/opportunities", icon: Briefcase },
    { label: "Operations", href: "/operations/inventory", icon: Warehouse },
    { label: "Scheduling", href: "/schedule", icon: CalendarDays },
    { label: "Leads", href: "/leads", icon: Users },
    { label: "WhatsApp", href: "/whatsapp", icon: MessageCircle },
    { label: "Bot Settings", href: "/whatsapp/bot", icon: Bot },
    { label: "Catalog", href: "/whatsapp/catalog", icon: Package },
    { label: "Buyer RFQs", href: "/whatsapp/rfqs", icon: ShoppingCart },
    { label: "Deep Links", href: "/whatsapp/links", icon: Link2 },
    { label: "Trader Toolbox", href: "/toolbox", icon: Globe },
    { label: "Trade Intelligence", href: "/trade", icon: Globe },
    { label: "AI Brain", href: "/brain", icon: Brain },
    { label: "Wallet", href: "/wallet", icon: Wallet },
];

import { useAuth } from "@/context/AuthContext";
import { LogOut } from "lucide-react";

export default function Sidebar() {
    const pathname = usePathname();
    const { logout } = useAuth();

    return (
        <aside className="w-64 h-full bg-navy-900 border-r border-navy-800 flex flex-col">
            {/* Logo */}
            <div className="p-6 border-b border-navy-800 flex items-center justify-center">
                <div className="relative w-16 h-16">
                    <Image
                        src="/logo.png"
                        alt="Artin Smart Trade"
                        fill
                        className="object-contain"
                        priority
                    />
                </div>
            </div>

            {/* Navigation */}
            <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
                {navItems.map((item) => {
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
