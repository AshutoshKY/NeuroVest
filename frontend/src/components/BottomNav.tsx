'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion } from 'framer-motion';
import { LayoutDashboard, History, Bookmark, FileText } from 'lucide-react';

const navItems = [
    { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { href: '/dashboard/history', label: 'History', icon: History },
    { href: '/dashboard/watchlist', label: 'Watchlist', icon: Bookmark },
    { href: '/dashboard/documentation', label: 'Docs', icon: FileText },
];

export function BottomNav() {
    const pathname = usePathname();

    return (
        <nav className="fixed bottom-0 left-0 right-0 z-40 bg-slate-950/80 backdrop-blur-xl border-t border-slate-800 safe-area-bottom">
            <div className="flex items-center justify-around h-16 md:h-20 max-w-7xl mx-auto px-4">
                {navItems.map((item) => {
                    const Icon = item.icon;
                    const isActive = pathname === item.href;

                    return (
                        <Link
                            key={item.href}
                            href={item.href}
                            className="relative flex flex-col items-center justify-center flex-1 h-full group touch-manipulation"
                        >
                            {/* Active indicator glow */}
                            {isActive && (
                                <motion.div
                                    layoutId="bottomNavActiveTab"
                                    className="absolute inset-0 bg-gradient-to-t from-emerald-500/10 to-transparent rounded-t-xl"
                                    transition={{ type: "spring", damping: 30, stiffness: 300 }}
                                />
                            )}

                            {/* Icon */}
                            <div className={`relative ${isActive ? 'text-emerald-400' : 'text-slate-400 group-hover:text-slate-200'} transition-colors`}>
                                <Icon className={`w-6 h-6 ${isActive ? 'drop-shadow-[0_0_8px_rgba(16,185,129,0.5)]' : ''}`} />

                                {/* Active dot indicator (mobile) */}
                                {isActive && (
                                    <motion.div
                                        initial={{ scale: 0 }}
                                        animate={{ scale: 1 }}
                                        className="absolute -top-1 -right-1 w-2 h-2 bg-emerald-400 rounded-full"
                                    />
                                )}
                            </div>

                            {/* Label - hidden on very small screens */}
                            <span className={`mt-1 text-[10px] md:text-xs font-medium hidden sm:block ${isActive
                                ? 'text-emerald-400'
                                : 'text-slate-500 group-hover:text-slate-300'
                                } transition-colors`}>
                                {item.label}
                            </span>
                        </Link>
                    );
                })}
            </div>
        </nav>
    );
}
