"use client";

import { useState } from "react";
import Sidebar from "./Sidebar";
import TopBar from "./TopBar";
import BottomNav from "./BottomNav";
import { Sheet, SheetContent } from "@/components/ui/sheet";

const DashboardLayout = ({ children }: { children: React.ReactNode }) => {
    const [isMobileOpen, setIsMobileOpen] = useState(false);

    return (
        <div className="flex h-screen overflow-hidden bg-black selection:bg-[#D4AF37]/30 selection:text-[#D4AF37]">
            {/* Background Texture/Grain for Luxury feel */}
            <div className="fixed inset-0 pointer-events-none opacity-20 contrast-125 grayscale" style={{ backgroundImage: 'url("https://www.transparenttextures.com/patterns/asfalt-dark.png")' }}></div>

            {/* Desktop Sidebar */}
            <div className="hidden md:flex h-full shrink-0 relative z-20 border-r border-white/5">
                <Sidebar />
            </div>

            {/* Mobile Drawer */}
            <Sheet open={isMobileOpen} onOpenChange={setIsMobileOpen}>
                <SheetContent side="left" className="p-0 w-72 bg-black border-white/10 z-[100]">
                    <Sidebar forceExpanded={true} onItemClick={() => setIsMobileOpen(false)} />
                </SheetContent>
            </Sheet>

            <div className="flex flex-1 flex-col overflow-hidden min-w-0 relative z-10 font-sans">
                <TopBar onMenuClick={() => setIsMobileOpen(true)} />

                {/* Main Content */}
                <main className="flex-1 overflow-y-auto bg-transparent p-4 md:p-6 text-white pb-20 md:pb-6 relative custom-scrollbar">
                    {children}

                    {/* Decorative Ambient Glow */}
                    <div className="fixed bottom-0 right-0 w-[500px] h-[500px] bg-[#D4AF37]/5 rounded-full blur-[120px] pointer-events-none -z-10"></div>
                </main>

                {/* Mobile Bottom Nav */}
                <div className="md:hidden">
                    <BottomNav onMenuClick={() => setIsMobileOpen(true)} />
                </div>
            </div>

            <style jsx global>{`
                .custom-scrollbar::-webkit-scrollbar {
                    width: 4px;
                }
                .custom-scrollbar::-webkit-scrollbar-track {
                    background: transparent;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb {
                    background: rgba(212, 175, 55, 0.2);
                    border-radius: 20px;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb:hover {
                    background: rgba(212, 175, 55, 0.4);
                }
            `}</style>
        </div>
    );
};

export default DashboardLayout;
