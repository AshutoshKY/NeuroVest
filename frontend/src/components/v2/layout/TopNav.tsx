'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ModeToggle } from './ModeToggle';
import { X } from 'lucide-react';

/**
 * Top Navigation Bar for Analysis Page
 * Matches design from analysis_8.html
 */

interface TopNavProps {
    ticker?: string;
    showBack?: boolean;
    showActions?: boolean;
    onClose?: () => void;
    onSave?: () => void;
    onWatchlist?: () => void;
}

export function TopNav({
    ticker,
    showBack = false,
    showActions = false,
    onClose,
    onSave,
    onWatchlist
}: TopNavProps) {
    const router = useRouter();

    const handleBack = () => {
        if (onClose) {
            onClose();
        } else {
            router.push('/dashboard');
        }
    };

    return (
        <header className="h-16 border-b border-gray-200 dark:border-zinc-800 bg-white/90 dark:bg-[#09090b]/90 backdrop-blur-md fixed top-8 w-full z-50 flex items-center justify-between px-6 transition-colors duration-300">
            {/* Left Side - Back Button or Logo */}
            <div className="flex items-center gap-8">
                {showBack ? (
                    <button
                        onClick={handleBack}
                        className="flex items-center gap-2 group"
                    >
                        <div className="w-8 h-8 rounded-lg bg-gray-200 dark:bg-zinc-800 border border-gray-300 dark:border-zinc-700 flex items-center justify-center text-gray-500 dark:text-gray-400 group-hover:bg-primary-500 group-hover:text-white group-hover:border-primary-500 transition">
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                            </svg>
                        </div>
                        <div className="font-bold text-gray-900 dark:text-white text-lg tracking-tight hidden md:block group-hover:text-primary-500 transition">
                            Dashboard
                        </div>
                    </button>
                ) : (
                    <Link href="/dashboard" className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-purple-600 flex items-center justify-center text-white font-bold shadow-lg">
                            N
                        </div>
                        <div className="font-bold text-gray-900 dark:text-white text-xl tracking-tight hidden md:block">
                            NEUROVEST
                        </div>
                    </Link>
                )}
            </div>

            {/* Right Side - Mode Toggle + Actions */}
            <div className="flex items-center gap-3">
                {/* Mode Toggle */}
                <ModeToggle className="mr-2" />

                {/* Action Buttons (only on analysis page) */}
                {showActions && (
                    <>
                        <button
                            onClick={onSave}
                            className="hidden md:flex items-center gap-2 px-3 py-1.5 bg-primary-500/10 hover:bg-primary-500/20 text-primary-600 dark:text-primary-400 text-xs font-bold rounded-lg border border-primary-500/20 transition"
                        >
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                            </svg>
                            Save
                        </button>

                        <button
                            onClick={onWatchlist}
                            className="hidden md:flex items-center gap-2 px-3 py-1.5 bg-gray-100 dark:bg-zinc-800 hover:bg-gray-200 dark:hover:bg-zinc-700 text-gray-600 dark:text-gray-300 text-xs font-bold rounded-lg border border-gray-200 dark:border-zinc-700 transition"
                        >
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                            </svg>
                            Watchlist
                        </button>

                        <div className="h-6 w-px bg-gray-300 dark:bg-zinc-700 mx-1" />
                    </>
                )}

                {/* Close Button */}
                {onClose && (
                    <button
                        onClick={onClose}
                        className="p-2 text-gray-400 hover:text-danger bg-gray-100 dark:bg-zinc-800 hover:bg-danger/10 rounded-full transition"
                        title="Close Analysis"
                    >
                        <X size={20} />
                    </button>
                )}
            </div>
        </header>
    );
}
