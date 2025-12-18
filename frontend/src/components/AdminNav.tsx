'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import {
    BarChart,
    Users,
    Activity,
    Terminal,
    LogOut,
    ShieldAlert,
    LayoutDashboard
} from 'lucide-react';
import { useAuthStore } from '@/store/authStore';
import { useRouter } from 'next/navigation';

const navItems = [
    { href: '/admin', label: 'Overview', icon: BarChart },
    { href: '/admin/users', label: 'User Management', icon: Users },
    { href: '/admin/health', label: 'System Health', icon: Activity },
    { href: '/admin/logs', label: 'System Logs', icon: Terminal },
];

export function AdminNav() {
    const pathname = usePathname();
    const { logout } = useAuthStore();
    const router = useRouter();

    const handleLogout = async () => {
        await logout();
        router.push('/auth/login');
    };

    return (
        <div className="flex w-64 flex-col border-r border-slate-800 bg-slate-950 px-4 py-8">
            {/* Brand */}
            <div className="mb-8 flex items-center gap-2 px-2">
                <ShieldAlert className="h-6 w-6 text-cyan-500" />
                <span className="text-xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500">
                    Admin Console
                </span>
            </div>

            {/* Back to App */}
            <div className="mb-6 px-2">
                <Link
                    href="/dashboard"
                    className="flex items-center gap-2 text-xs font-medium text-slate-500 hover:text-emerald-400 transition-colors"
                >
                    <LayoutDashboard size={14} /> Back to App
                </Link>
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
                                    ? "bg-cyan-500/10 text-cyan-400"
                                    : "text-slate-400 hover:bg-slate-900 hover:text-slate-200"
                            )}
                        >
                            <Icon className={cn("h-5 w-5", isActive ? "text-cyan-500" : "text-slate-500")} />
                            {item.label}
                        </Link>
                    );
                })}
            </nav>

            {/* Logout */}
            <div className="mt-auto border-t border-slate-800 pt-4">
                <button
                    onClick={handleLogout}
                    className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-slate-400 transition-colors hover:bg-red-500/10 hover:text-red-400"
                >
                    <LogOut className="h-5 w-5" />
                    Sign Out
                </button>
            </div>
        </div>
    );
}
