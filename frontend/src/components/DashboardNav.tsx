'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import {
    LayoutDashboard,
    History,
    Bookmark,
    Settings,
    LogOut,
    TrendingUp
} from 'lucide-react';
import { useAuthStore } from '@/store/authStore';
import { useRouter } from 'next/navigation';

const navItems = [
    { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { href: '/dashboard/history', label: 'History', icon: History },
    { href: '/dashboard/watchlist', label: 'Watchlist', icon: Bookmark },
];

export function DashboardNav() {
    const pathname = usePathname();

    return (
        <div className="flex w-64 flex-col border-r border-slate-800 bg-slate-950 px-4 py-8">
            {/* Brand */}
            <div className="mb-8 flex items-center gap-2 px-2">
                <TrendingUp className="h-6 w-6 text-emerald-500" />
                <span className="text-xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-500">
                    Neurovest
                </span>
            </div>

            {/* Nav Links */}
            <nav className="flex-1 space-y-1">
                {navItems.map((item) => {
                    const Icon = item.icon;
                    const isActive = pathname === item.href;

                    return (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={cn(
                                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                                isActive
                                    ? "bg-emerald-500/10 text-emerald-400"
                                    : "text-slate-400 hover:bg-slate-900 hover:text-slate-200"
                            )}
                        >
                            <Icon className={cn("h-5 w-5", isActive ? "text-emerald-500" : "text-slate-500")} />
                            {item.label}
                        </Link>
                    );
                })}
            </nav>
        </div>
    );
}
