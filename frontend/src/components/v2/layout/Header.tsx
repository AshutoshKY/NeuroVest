'use client';

import Link from 'next/link';
import { Menu } from 'lucide-react';
import { useState } from 'react';

/**
 * Header Navigation - POC Design Match
 * Exactly matches design_poc_1/index.html
 */

interface HeaderProps {
    analysesRemaining?: number;
    analysesLimit?: number;
    userInitials?: string;
    onDrawerToggle?: () => void;
}

export function Header({
    analysesRemaining = 4,
    analysesLimit = 5,
    userInitials = 'TD',
    onDrawerToggle
}: HeaderProps) {
    return (
        <header className="h-16 border-b border-gray-200 dark:border-zinc-800 bg-white/80 dark:bg-[#09090b]/80 backdrop-blur fixed top-0 w-full z-50 flex items-center justify-between px-6">
            {/* Left Side: Logo + Navigation */}
            <div className="flex items-center gap-8">
                {/* Logo */}
                <Link href="/dashboard-v2" className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-purple-600 flex items-center justify-center text-white font-bold shadow-lg">
                        N
                    </div>
                    <div className="font-bold text-gray-900 dark:text-white text-xl tracking-tight hidden md:block">
                        NEUROVEST
                    </div>
                </Link>

                {/* Navigation */}
                <nav className="hidden md:flex items-center gap-1 text-sm font-medium h-16">
                    <Link
                        href="/dashboard-v2"
                        className="h-full flex items-center px-4 text-primary-500 dark:text-white border-b-2 border-primary-500"
                    >
                        Dashboard
                    </Link>
                    <Link
                        href="/watchlist"
                        className="h-full flex items-center px-4 text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition"
                    >
                        Watchlist
                    </Link>
                    <Link
                        href="/history"
                        className="h-full flex items-center px-4 text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition"
                    >
                        History
                    </Link>
                    <Link
                        href="/docs"
                        className="h-full flex items-center px-4 text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition"
                    >
                        Docs
                    </Link>
                </nav>
            </div>

            {/* Right Side: Analysis Count + User + Drawer Toggle */}
            <div className="flex items-center gap-4">
                {/* Analysis Count Badge */}
                <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 bg-primary-500/10 border border-primary-500/20 rounded-full">
                    <span className="w-2 h-2 rounded-full bg-primary-500 animate-pulse"></span>
                    <span className="text-xs font-bold text-primary-600 dark:text-primary-400">
                        {analysesRemaining}/{analysesLimit} Analyses Left
                    </span>
                </div>

                {/* User Avatar */}
                <Link
                    href="/settings"
                    className="w-8 h-8 rounded-full bg-gray-200 dark:bg-zinc-800 border border-gray-300 dark:border-zinc-700 flex items-center justify-center text-xs font-bold text-gray-700 dark:text-white hover:border-primary-500 transition"
                >
                    {userInitials}
                </Link>

                {/* Drawer Toggle Button */}
                <button
                    onClick={onDrawerToggle}
                    className="text-gray-500 hover:text-gray-900 dark:hover:text-white p-2 transition"
                    aria-label="Toggle drawer"
                >
                    <Menu className="w-6 h-6" />
                </button>
            </div>
        </header>
    );
}
