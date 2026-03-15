import {
    LayoutDashboard,
    Users,
    Search,
    MessageCircle,
    BarChart3,
    Globe,
    Brain,
    Building2,
    Megaphone,
    Settings,
    Crosshair,
    Package,
    Briefcase,
    Warehouse,
    Truck,
    Zap,
    Camera,
    ShieldCheck,
    FileText,
    QrCode,
    BookOpen,
    Send,
    UserCheck,
    Target,
    TrendingUp,
    AlertTriangle,
    Calculator,
    Radar,
    type LucideIcon,
} from "lucide-react";

// ---------- Types ----------
export type TenantMode = "buyer" | "seller" | "hybrid";
export type UserRole = "super_admin" | "admin" | "user";

export interface NavItem {
    label: string;
    href: string;
    icon: LucideIcon;
    external?: boolean;
    /** Expandable children (sub-menu). Only 1 level deep. */
    children?: NavItem[];
    /**
     * Visibility control.
     * If omitted the item is visible to everyone.
     * modes – show only when tenant is in one of these modes.
     * roles – show only when user has one of these roles.
     */
    visibleIn?: {
        modes?: TenantMode[];
        roles?: UserRole[];
    };
}

// ---------- Unified navigation ----------
export const navItems: NavItem[] = [
    // ── Command Center ──────────────────────────────────
    {
        label: "Command Center",
        href: "/command-center",
        icon: Zap,
    },

    // ── Acquisition ─────────────────────────────────────
    {
        label: "Acquisition",
        href: "/acquisition",
        icon: Target,
        children: [
            { label: "Overview", href: "/acquisition/overview", icon: LayoutDashboard },
            { label: "Buyer Leads", href: "/acquisition/buyer-leads", icon: Search },
            { label: "Supplier Leads", href: "/acquisition/supplier-leads", icon: Package },
            { label: "Expo", href: "/acquisition/expo", icon: Globe },
            { label: "QR Capture", href: "/acquisition/qr-capture", icon: QrCode },
            { label: "Catalogs", href: "/acquisition/catalogs", icon: BookOpen },
            { label: "Broadcasts", href: "/acquisition/broadcasts", icon: Send },
            { label: "Representatives", href: "/acquisition/representatives", icon: UserCheck },
            { label: "Lead Analytics", href: "/acquisition/lead-analytics", icon: BarChart3 },
        ],
    },

    // ── Sales CRM ───────────────────────────────────────
    {
        label: "Sales CRM",
        href: "/crm",
        icon: Briefcase,
        children: [
            { label: "Pipeline", href: "/crm/pipelines", icon: TrendingUp },
            { label: "Companies", href: "/crm/companies", icon: Building2 },
            { label: "Contacts", href: "/crm/contacts", icon: Users },
            { label: "Deals", href: "/deals", icon: Briefcase },
            { label: "Tasks", href: "/crm/tasks", icon: Crosshair },
            { label: "Campaigns", href: "/crm/campaigns", icon: Megaphone },
        ],
    },

    // ── Operations ──────────────────────────────────────
    {
        label: "Operations",
        href: "/operations",
        icon: Warehouse,
        children: [
            { label: "Sourcing", href: "/sourcing/rfqs", icon: Package },
            { label: "Logistics", href: "/shipments", icon: Truck },
            { label: "Smart Scanner", href: "/scanner", icon: Camera },
            { label: "Documents", href: "/documents", icon: FileText },
        ],
    },

    // ── Intelligence ────────────────────────────────────
    {
        label: "Intelligence",
        href: "/intelligence",
        icon: Brain,
        children: [
            { label: "AI Brain", href: "/brain", icon: Brain },
            { label: "Landed Cost", href: "/brain/landed-cost", icon: Calculator },
            { label: "Arbitrage Finder", href: "/brain/arbitrage-finder", icon: Radar },
            { label: "Risk Engine", href: "/intelligence/risk-engine", icon: AlertTriangle },
        ],
    },

    // ── Settings ────────────────────────────────────────
    {
        label: "Settings",
        href: "/settings",
        icon: Settings,
    },
];

// Admin item – ONLY for platform super_admin (NOT tenant admin)
export const adminNavItem: NavItem = {
    label: "Super Admin",
    href: "/admin/super",
    icon: ShieldCheck,
    visibleIn: { roles: ["super_admin"] },
};

// ---------- Helpers ----------

/** Filter a nav tree by tenant mode + user role. */
export function filterNavItems(
    items: NavItem[],
    mode: TenantMode,
    role: UserRole,
): NavItem[] {
    return items
        .filter((item) => {
            if (!item.visibleIn) return true;
            const modeOk = !item.visibleIn.modes || item.visibleIn.modes.includes(mode);
            const roleOk = !item.visibleIn.roles || item.visibleIn.roles.includes(role);
            return modeOk && roleOk;
        })
        .map((item) => {
            if (!item.children) return item;
            const filteredChildren = filterNavItems(item.children, mode, role);
            return { ...item, children: filteredChildren.length ? filteredChildren : undefined };
        });
}
