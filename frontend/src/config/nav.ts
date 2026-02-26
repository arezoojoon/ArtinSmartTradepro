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
    ShoppingCart,
    Truck
} from "lucide-react";

export interface NavItem {
    label: string;
    href: string;
    icon: any;
    external?: boolean;
}

export const navItems = {
    buyer: [
        { label: "Dashboard", href: "/buyer", icon: LayoutDashboard },
        { label: "Sourcing OS", href: "/sourcing/rfqs", icon: Package },
        { label: "Trade Intelligence", href: "/trade", icon: Globe },
        { label: "Deal Flow (AI)", href: "/brain/opportunities", icon: Briefcase },
        { label: "Operations", href: "/operations/inventory", icon: Warehouse },
        { label: "Logistics", href: "/shipments", icon: Truck },
        { label: "Settings", href: "/settings", icon: Settings },
    ],
    seller: [
        { label: "Dashboard", href: "/seller", icon: LayoutDashboard },
        { label: "CRM", href: "/crm", icon: Users },
        { label: "Hunter (Leads)", href: "/hunter", icon: Search },
        { label: "Campaigns", href: "/crm/campaigns", icon: Megaphone },
        { label: "Market Intel", href: "/hunter/competitors", icon: Crosshair },
        { label: "WhatsApp Sales", href: "/whatsapp", icon: MessageCircle },
        { label: "Logistics", href: "/shipments", icon: Truck },
        { label: "Settings", href: "/settings", icon: Settings },
    ],
    hybrid: [
        { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
        { label: "CRM (Sales)", href: "/crm", icon: Users },
        { label: "Hunter (Leads)", href: "/hunter", icon: Search },
        { label: "Sourcing", href: "/sourcing/rfqs", icon: Package },
        { label: "WhatsApp", href: "/whatsapp", icon: MessageCircle },
        { label: "AI Brain", href: "/brain", icon: Brain },
        { label: "Logistics", href: "/shipments", icon: Truck },
        { label: "Settings", href: "/settings", icon: Settings },
    ]
};
