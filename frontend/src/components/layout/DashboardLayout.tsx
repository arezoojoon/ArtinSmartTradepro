"use client";

import { useState } from "react";
import Sidebar from "./Sidebar";
import TopBar from "./TopBar";
import BottomNav from "./BottomNav";
import { Sheet, SheetContent } from "@/components/ui/sheet";

const DashboardLayout = ({ children }: { children: React.ReactNode }) => {
    const [isMobileOpen, setIsMobileOpen] = useState(false);

    return (
        <div className="flex h-screen overflow-hidden bg-background">
            {/* Desktop Sidebar - Explicitly set width and visibility */}
            <div className="hidden md:flex h-full shrink-0 relative z-20">
                <Sidebar />
            </div>

            {/* Mobile Drawer - High Z-index with explicit background */}
            <Sheet open={isMobileOpen} onOpenChange={setIsMobileOpen}>
                <SheetContent side="left" className="p-0 w-72 bg-navy-900 border-navy-800 z-[100]">
                    <Sidebar forceExpanded={true} />
                </SheetContent>
            </Sheet>

            <div className="flex flex-1 flex-col overflow-hidden min-w-0 relative z-0">
                <TopBar onMenuClick={() => setIsMobileOpen(true)} />

                {/* Main Content */}
                <main className="flex-1 overflow-y-auto bg-navy-950 p-4 md:p-6 text-white pb-20 md:pb-6 relative">
                    {children}
                </main>

                {/* Mobile Bottom Nav */}
                <div className="md:hidden">
                    <BottomNav onMenuClick={() => setIsMobileOpen(true)} />
                </div>
            </div>
        </div>
    );
};

export default DashboardLayout;
