"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Users, Search, Brain, Menu } from "lucide-react";
import { useState } from "react";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import Sidebar from "./Sidebar";

export default function BottomNav() {
    const pathname = usePathname();
    const [open, setOpen] = useState(false);

    const tabs = [
        { label: "Home", href: "/dashboard", icon: LayoutDashboard },
        { label: "CRM", href: "/crm", icon: Users },
        { label: "Hunter", href: "/hunter", icon: Search },
        { label: "Brain", href: "/brain", icon: Brain },
    ];

    return (
        <div className="fixed bottom-0 left-0 right-0 bg-navy-900 border-t border-navy-800 pb-safe z-50 md:hidden">
            <div className="flex justify-around items-center h-16">
                {tabs.map((tab) => {
                    const isActive = pathname === tab.href || pathname?.startsWith(tab.href + "/");
                    return (
                        <Link
                            key={tab.href}
                            href={tab.href}
                            className={`flex flex-col items-center justify-center w-full h-full space-y-1 ${isActive ? "text-gold-400" : "text-gray-400 hover:text-gray-200"
                                }`}
                        >
                            <tab.icon className={`h-6 w-6 ${isActive ? "stroke-[2.5px]" : "stroke-2"}`} />
                            <span className="text-[10px] font-medium">{tab.label}</span>
                        </Link>
                    );
                })}

                {/* Menu Drawer Trigger */}
                <Sheet open={open} onOpenChange={setOpen}>
                    <SheetTrigger asChild>
                        <button className="flex flex-col items-center justify-center w-full h-full space-y-1 text-gray-400 hover:text-gray-200">
                            <Menu className="h-6 w-6" />
                            <span className="text-[10px] font-medium">Menu</span>
                        </button>
                    </SheetTrigger>
                    <SheetContent side="right" className="bg-navy-900 border-navy-800 p-0 text-white w-[80%]">
                        <Sidebar />
                    </SheetContent>
                </Sheet>
            </div>
        </div>
    );
}
