'use client';

/**
 * Admin Sidebar Navigation
 * 
 * Matches the POC design with 7 navigation items in two sections:
 * - Platform: Overview, Infrastructure, AI & RAG, External APIs
 * - Operations: User Intelligence, Security & Audit, Kill Switches
 */

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import {
    LayoutDashboard,
    Server,
    Brain,
    Plug,
    Users,
    ShieldAlert,
    AlertTriangle,
    LogOut,
    ArrowLeft
} from 'lucide-react';
import { useAuthStore } from '@/store/authStore';
import { useRouter } from 'next/navigation';

const platformNavItems = [
    { href: '/admin', label: 'Overview', icon: LayoutDashboard },
    { href: '/admin/infrastructure', label: 'Infrastructure (DB/Redis)', icon: Server },
    { href: '/admin/ai-rag', label: 'AI & RAG Engine', icon: Brain },
    { href: '/admin/api-health', label: 'External APIs', icon: Plug },
];

const operationsNavItems = [
    { href: '/admin/users', label: 'User Intelligence', icon: Users },
    { href: '/admin/security', label: 'Security & Audit', icon: ShieldAlert },
];

const dangerItem = { href: '/admin/controls', label: 'Kill Switches & Config', icon: AlertTriangle };

export function AdminNav() {
    const pathname = usePathname();
    const { logout } = useAuthStore();
    const router = useRouter();

    const handleLogout = async () => {
        await logout();
        router.push('/auth/login');
    };

    const isActive = (href: string) => {
        if (href === '/admin') return pathname === '/admin';
        return pathname.startsWith(href);
    };

    return (
        <aside className="w-64 bg-[#0f172a] border-r border-[#1e293b] flex flex-col h-full shrink-0">
            {/* Brand Header */}
            <div className="h-16 flex items-center gap-3 px-6 border-b border-[#1e293b]">
                <div className="w-8 h-8 rounded bg-[#6366f1] flex items-center justify-center text-white font-bold">
                    N
                </div>
                <div className="font-bold text-white tracking-tight">
                    NEUROVEST
                    <span className="text-[10px] text-[#6366f1] block font-normal">
                        Command Center
                    </span>
                </div>
            </div>

            {/* Navigation */}
            <nav className="flex-1 overflow-y-auto py-4 space-y-1">
                {/* Platform Section */}
                <div className="px-6 text-[10px] font-bold text-slate-500 uppercase tracking-widest mt-2 mb-2">
                    Platform
                </div>
                {platformNavItems.map((item) => {
                    const Icon = item.icon;
                    const active = isActive(item.href);

                    return (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={cn(
                                "nav-link flex items-center gap-3 px-6 py-3 text-slate-400 hover:text-white hover:bg-white/5 transition text-sm",
                                active && "bg-[#6366f1]/10 border-l-[3px] border-[#6366f1] text-white"
                            )}
                        >
                            <Icon className="h-4 w-4" />
                            {item.label}
                        </Link>
                    );
                })}

                {/* Operations Section */}
                <div className="px-6 text-[10px] font-bold text-slate-500 uppercase tracking-widest mt-6 mb-2">
                    Operations
                </div>
                {operationsNavItems.map((item) => {
                    const Icon = item.icon;
                    const active = isActive(item.href);

                    return (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={cn(
                                "nav-link flex items-center gap-3 px-6 py-3 text-slate-400 hover:text-white hover:bg-white/5 transition text-sm",
                                active && "bg-[#6366f1]/10 border-l-[3px] border-[#6366f1] text-white"
                            )}
                        >
                            <Icon className="h-4 w-4" />
                            {item.label}
                        </Link>
                    );
                })}

                {/* Kill Switches - Danger Item */}
                <Link
                    href={dangerItem.href}
                    className={cn(
                        "nav-link flex items-center gap-3 px-6 py-3 text-red-400 hover:text-red-300 hover:bg-red-500/10 transition text-sm font-bold",
                        isActive(dangerItem.href) && "bg-red-500/10 border-l-[3px] border-red-500"
                    )}
                >
                    <dangerItem.icon className="h-4 w-4" />
                    {dangerItem.label}
                </Link>
            </nav>

            {/* Footer */}
            <div className="border-t border-[#1e293b] p-4 space-y-2">
                <Link
                    href="/dashboard"
                    className="flex items-center gap-2 text-xs text-slate-500 hover:text-emerald-400 transition-colors"
                >
                    <ArrowLeft size={14} />
                    Back to App
                </Link>
                <button
                    onClick={handleLogout}
                    className="flex w-full items-center gap-2 text-xs text-slate-500 hover:text-red-400 transition-colors"
                >
                    <LogOut size={14} />
                    Sign Out
                </button>
            </div>
        </aside>
    );
}
