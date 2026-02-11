"use client";

import { useAuth } from "@/context/AuthContext";
import { Bell, User } from "lucide-react";

const TopBar = () => {
    const { user } = useAuth();

    return (
        <header className="flex h-16 items-center justify-between border-b border-navy-800 bg-navy-900 px-6 shadow-sm">
            <div className="flex items-center">
                {/* Mobile trigger could go here */}
                <span className="text-gray-400 text-sm">Welcome back, <span className="text-gold-400 font-semibold">{user?.full_name || "Trader"}</span></span>
            </div>

            <div className="flex items-center space-x-4">
                <button className="relative p-1 text-gray-400 hover:text-white">
                    <Bell className="h-6 w-6" />
                    <span className="absolute top-0 right-0 h-2 w-2 rounded-full bg-red-500"></span>
                </button>
                <div className="h-8 w-8 rounded-full bg-navy-700 flex items-center justify-center border border-navy-600">
                    <User className="h-5 w-5 text-gold-400" />
                </div>
            </div>
        </header>
    );
};

export default TopBar;
