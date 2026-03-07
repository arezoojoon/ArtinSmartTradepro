"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Zap, Target, Briefcase, Brain, Menu } from "lucide-react";

interface BottomNavProps {
    onMenuClick?: () => void;
}

export default function BottomNav({ onMenuClick }: BottomNavProps) {
    const pathname = usePathname();

    const tabs = [
        { label: "Home", href: "/command-center", icon: Zap },
        { label: "Acquisition", href: "/acquisition", icon: Target },
        { label: "CRM", href: "/crm", icon: Briefcase },
        { label: "Intel", href: "/brain", icon: Brain },
    ];

    return (
        <div className="fixed bottom-0 left-0 right-0 bg-[#0e1e33]/95 backdrop-blur-md border-t border-[#1e3a5f] pb-safe z-50 md:hidden">
            <div className="flex justify-around items-center h-16">
                {tabs.map((tab) => {
                    const isActive =
                        pathname === tab.href ||
                        (tab.href !== "/command-center" && pathname?.startsWith(tab.href + "/"));
                    return (
                        <Link
                            key={tab.href}
                            href={tab.href}
                            className={`flex flex-col items-center justify-center w-full h-full space-y-1 active:scale-95 transition-transform ${isActive ? "text-[#f5a623]" : "text-gray-100 hover:text-white"
                                }`}
                        >
                            <tab.icon className={`h-6 w-6 ${isActive ? "stroke-[2.5px]" : "stroke-2"}`} />
                            <span className="text-[10px] font-medium">{tab.label}</span>
                        </Link>
                    );
                })}

                {/* Menu Drawer Trigger */}
                <button
                    onClick={onMenuClick}
                    className="flex flex-col items-center justify-center w-full h-full space-y-1 text-gray-100 hover:text-white active:scale-95 transition-transform"
                >
                    <Menu className="h-6 w-6" />
                    <span className="text-[10px] font-medium">Menu</span>
                </button>
            </div>
        </div>
    );
}
