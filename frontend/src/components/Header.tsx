'use client';

import { useAuthStore } from '@/store/authStore';
import { useThemeStore } from '@/store/themeStore';
import { useRouter } from 'next/navigation';
import { UserCircle, Settings, LogOut, ChevronDown, Sun, Moon } from 'lucide-react';
import { useState, useEffect, useRef } from 'react';
import Image from 'next/image';
import { apiClient } from '@/lib/api';

export function Header() {
    const { user, logout } = useAuthStore();
    const { isDarkMode, toggleTheme } = useThemeStore();
    const router = useRouter();
    const [showProfileMenu, setShowProfileMenu] = useState(false);
    const [requestsRemaining, setRequestsRemaining] = useState(5);
    const [resetAt, setResetAt] = useState<number | null>(null);
    const [timeUntilReset, setTimeUntilReset] = useState<string>('');
    const hasInitialized = useRef(false);

    // Fetch remaining analyses count (once on mount)
    useEffect(() => {
        // Prevent duplicate calls
        if (hasInitialized.current) {
            return;
        }
        hasInitialized.current = true;

        const fetchRemaining = async () => {
            try {
                // CRITICAL: Include tracking headers
                const { TrackingHeaders } = await import('@/lib/tracking-headers');
                const trackingHeaders = await TrackingHeaders.getHeaders();

                const response = await apiClient.get('/tracking/user/check-limit', {
                    headers: trackingHeaders as any
                });
                setRequestsRemaining(response.data.remaining);
                setResetAt(response.data.reset_at);  // Store reset timestamp
            } catch (error) {
                console.error('Failed to fetch remaining count:', error);
            }
        };

        fetchRemaining();

        // Make fetchRemaining available globally so dashboard can call it
        (window as any).refreshAnalysisCounter = async () => {
            try {
                // CRITICAL: Include tracking headers
                const { TrackingHeaders } = await import('@/lib/tracking-headers');
                const trackingHeaders = await TrackingHeaders.getHeaders();

                const response = await apiClient.get('/tracking/user/check-limit', {
                    headers: trackingHeaders as any
                });
                setRequestsRemaining(response.data.remaining);
                setResetAt(response.data.reset_at);  // Store reset timestamp
            } catch (error) {
                console.error('Failed to refresh counter:', error);
            }
        };
    }, []);

    // Countdown timer effect
    useEffect(() => {
        if (!resetAt) {
            setTimeUntilReset('');
            return;
        }

        const updateCountdown = () => {
            const now = Math.floor(Date.now() / 1000);
            const secondsRemaining = resetAt - now;

            if (secondsRemaining <= 0) {
                setTimeUntilReset('soon');
                return;
            }

            const hours = Math.floor(secondsRemaining / 3600);
            const minutes = Math.floor((secondsRemaining % 3600) / 60);

            if (hours > 0) {
                setTimeUntilReset(`${hours}h ${minutes}m`);
            } else if (minutes > 0) {
                setTimeUntilReset(`${minutes}m`);
            } else {
                setTimeUntilReset('1m'); // Show at least 1 minute
            }
        };

        // Update immediately
        updateCountdown();

        // Then update every minute
        const interval = setInterval(updateCountdown, 60000);

        return () => clearInterval(interval);
    }, [resetAt]);

    const handleLogout = () => {
        logout();
        router.push('/');
    };

    return (
        <header className="flex h-auto min-h-16 items-center justify-between border-b border-slate-800/50 bg-slate-950/80 backdrop-blur-xl px-8 md:px-16 lg:px-24 py-3 md:py-0 z-50 relative sticky top-0">
            {/* Left side - Logo Image */}
            <div className="flex items-center gap-4">
                <div
                    onClick={() => router.push('/dashboard')}
                    className="cursor-pointer hover:opacity-80 transition-opacity"
                >
                    <Image
                        src="/neurovest-logo.jpg"
                        alt="NeuroVest"
                        width={180}
                        height={40}
                        className="h-8 md:h-10 w-auto object-contain"
                        priority
                    />
                </div>
            </div>

            {/* Right side - Controls */}
            <div className="flex items-center gap-2 md:gap-4">
                {/* Request Counter - Responsive text */}
                <div className={`px-2 md:px-4 py-1.5 md:py-2 rounded-lg text-xs md:text-sm font-semibold whitespace-nowrap transition-all ${requestsRemaining <= 1
                    ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                    : requestsRemaining <= 2
                        ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30'
                        : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                    }`}>
                    {requestsRemaining === 0 ? (
                        <>
                            <span className="hidden sm:inline">
                                Resets in {timeUntilReset || '...'}
                            </span>
                            <span className="sm:hidden">
                                {timeUntilReset || '0/5'}
                            </span>
                        </>
                    ) : (
                        <>
                            <span className="hidden sm:inline">{requestsRemaining}/5 analyses remaining</span>
                            <span className="sm:hidden">{requestsRemaining}/5</span>
                        </>
                    )}
                </div>


                {/* User Menu */}
                <div className="relative z-50">
                    <button
                        onClick={() => {
                            console.log('User menu clicked, current state:', showProfileMenu);
                            setShowProfileMenu(!showProfileMenu);
                        }}
                        className="flex items-center gap-1 md:gap-2 rounded-lg border border-slate-800/50 bg-slate-900/50 px-2 md:px-3 py-2 hover:bg-slate-800/50 transition-colors touch-manipulation backdrop-blur-sm"
                        aria-label="User menu"
                    >
                        <UserCircle className="h-4 w-4 md:h-5 md:w-5 text-emerald-500" />
                        <span className="hidden md:inline text-sm font-medium text-slate-300 max-w-[120px] truncate">
                            {user?.full_name || user?.email?.split('@')[0] || 'User'}
                        </span>
                        <ChevronDown className="w-3 h-3 md:w-4 md:h-4 text-slate-400" />
                    </button>

                    {showProfileMenu && (
                        <>
                            {/* Backdrop to close menu */}
                            <div
                                className="fixed inset-0 z-[60]"
                                onClick={() => setShowProfileMenu(false)}
                            />

                            <div className="absolute right-0 mt-2 w-48 md:w-56 rounded-xl shadow-2xl bg-slate-900/95 backdrop-blur-xl border border-slate-800/50 z-[70]">
                                <div className="p-3 border-b border-slate-800/50">
                                    <p className="text-sm font-medium text-white truncate">
                                        {user?.email || 'User'}
                                    </p>
                                    <p className="text-xs text-slate-500">
                                        {user?.role === 'admin' ? 'Administrator' : 'User'}
                                    </p>
                                </div>
                                <button
                                    onClick={() => {
                                        setShowProfileMenu(false);
                                        router.push('/dashboard/settings');
                                    }}
                                    className="w-full px-4 py-3 md:py-2 text-left text-sm hover:bg-slate-800/50 text-slate-300 flex items-center gap-2 touch-manipulation transition-colors"
                                >
                                    <Settings className="w-4 h-4" />
                                    Settings
                                </button>
                                <button
                                    onClick={handleLogout}
                                    className="w-full px-4 py-3 md:py-2 text-left text-sm text-red-400 hover:bg-red-500/10 flex items-center gap-2 touch-manipulation transition-colors rounded-b-xl"
                                >
                                    <LogOut className="w-4 h-4" />
                                    Logout
                                </button>
                            </div>
                        </>
                    )}
                </div>
            </div>
        </header>
    );
}
