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
            {/* Desktop Sidebar - Hidden on mobile, flex on desktop */}
            <div className="hidden md:flex h-full shrink-0">
                <Sidebar />
            </div>

            {/* Mobile Drawer */}
            <Sheet open={isMobileOpen} onOpenChange={setIsMobileOpen}>
                <SheetContent side="left" className="p-0 w-72 bg-navy-900 border-navy-800">
                    <Sidebar forceExpanded={true} />
                </SheetContent>
            </Sheet>

            <div className="flex flex-1 flex-col overflow-hidden min-w-0">
                <TopBar onMenuClick={() => setIsMobileOpen(true)} />

                {/* Main Content - Add bottom padding on mobile for BottomNav */}
                <main className="flex-1 overflow-y-auto bg-navy-950 p-4 md:p-6 text-white pb-20 md:pb-6 relative">
                    {children}
                </main>

                {/* Mobile Bottom Nav */}
                <BottomNav />
            </div>
        </div>
    );
};

export default DashboardLayout;
