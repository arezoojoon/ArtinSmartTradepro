"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Users, Search, Brain, Menu } from "lucide-react";
import { useState } from "react";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import Sidebar from "./Sidebar";

interface BottomNavProps {
    onMenuClick?: () => void;
}

export default function BottomNav({ onMenuClick }: BottomNavProps) {
    const pathname = usePathname();

    const tabs = [
        { label: "Home", href: "/dashboard", icon: LayoutDashboard },
        { label: "CRM", href: "/crm", icon: Users },
        { label: "Hunter", href: "/hunter", icon: Search },
        { label: "Brain", href: "/brain", icon: Brain },
    ];

    return (
        <div className="fixed bottom-0 left-0 right-0 bg-navy-900/95 backdrop-blur-md border-t border-navy-800 pb-safe z-50 md:hidden">
            <div className="flex justify-around items-center h-16">
                {tabs.map((tab) => {
                    const isActive = pathname === tab.href || (tab.href !== "/dashboard" && pathname?.startsWith(tab.href + "/"));
                    return (
                        <Link
                            key={tab.href}
                            href={tab.href}
                            className={`flex flex-col items-center justify-center w-full h-full space-y-1 active:scale-95 transition-transform ${isActive ? "text-gold-400" : "text-gray-300 hover:text-white"
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
                    className="flex flex-col items-center justify-center w-full h-full space-y-1 text-gray-300 hover:text-white active:scale-95 transition-transform"
                >
                    <Menu className="h-6 w-6" />
                    <span className="text-[10px] font-medium">Menu</span>
                </button>
            </div>
        </div>
    );
}
