'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import {
    LayoutDashboard, Users, CreditCard, Globe, Bot, FileText, ListChecks, LogOut,
    ShieldAlert
} from 'lucide-react';

const NAV = [
    { href: '/sys', label: 'Overview', icon: LayoutDashboard },
    { href: '/sys/tenants', label: 'Tenants', icon: Users },
    { href: '/sys/plans', label: 'Plans', icon: CreditCard },
    { href: '/sys/whitelabel', label: 'White-label', icon: Globe },
    { href: '/sys/prompt-ops', label: 'Prompt Ops', icon: Bot },
    { href: '/sys/audit', label: 'Audit Logs', icon: FileText },
];

export default function SysLayout({ children }: { children: React.ReactNode }) {
    const pathname = usePathname();
    const router = useRouter();
    const [admin, setAdmin] = useState<{ email: string; name?: string } | null>(null);

    useEffect(() => {
        if (pathname === '/sys/login') return;
        const token = sessionStorage.getItem('sys_token');
        if (!token) { router.replace('/sys/login'); return; }
        import('@/lib/sys-api').then(api =>
            api.sysGetMe()
                .then(me => setAdmin(me))
                .catch(() => router.replace('/sys/login'))
        );
    }, [pathname]);

    if (pathname === '/sys/login') return <>{children}</>;

    return (
        <div className="flex h-screen bg-slate-950 text-slate-100 font-sans">
            {/* Sidebar */}
            <aside className="w-56 flex-shrink-0 bg-slate-900 border-r border-slate-800 flex flex-col">
                {/* Logo */}
                <div className="px-4 py-5 border-b border-slate-800">
                    <div className="flex items-center gap-2">
                        <ShieldAlert className="h-5 w-5 text-amber-400" />
                        <span className="font-semibold text-sm text-slate-100">Artin Sys Admin</span>
                    </div>
                    {admin && (
                        <p className="text-xs text-slate-500 mt-1 truncate">{admin.email}</p>
                    )}
                </div>

                {/* Nav */}
                <nav className="flex-1 px-2 py-3 space-y-0.5">
                    {NAV.map(({ href, label, icon: Icon }) => {
                        const active = href === '/sys' ? pathname === '/sys' : pathname.startsWith(href);
                        return (
                            <Link
                                key={href}
                                href={href}
                                className={`flex items-center gap-2.5 px-3 py-2 rounded-md text-sm transition-colors ${active
                                        ? 'bg-amber-500/10 text-amber-400 font-medium'
                                        : 'text-slate-400 hover:bg-slate-800 hover:text-slate-100'
                                    }`}
                            >
                                <Icon className="h-4 w-4 flex-shrink-0" />
                                {label}
                            </Link>
                        );
                    })}
                </nav>

                {/* Logout */}
                <div className="px-2 py-3 border-t border-slate-800">
                    <button
                        onClick={() => { sessionStorage.removeItem('sys_token'); router.replace('/sys/login'); }}
                        className="flex items-center gap-2.5 w-full px-3 py-2 rounded-md text-sm text-slate-400 hover:bg-slate-800 hover:text-red-400 transition-colors"
                    >
                        <LogOut className="h-4 w-4" />
                        Sign out
                    </button>
                </div>
            </aside>

            {/* Main */}
            <main className="flex-1 overflow-y-auto bg-slate-950 p-6">
                {children}
            </main>
        </div>
    );
}
