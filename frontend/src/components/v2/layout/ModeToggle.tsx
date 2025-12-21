'use client';

import { useUI } from '@/contexts/UIContext';

/**
 * Lite/Pro Mode Toggle
 * Matches design from analysis_8.html
 */

interface ModeToggleProps {
    className?: string;
}

export function ModeToggle({ className = '' }: ModeToggleProps) {
    const { mode, setMode } = useUI();

    return (
        <div className={`flex items-center bg-gray-200 dark:bg-zinc-800 rounded-full p-1 relative ${className}`}>
            {/* Animated slider background */}
            <div
                id="mode-slider"
                className="absolute left-1 w-[58px] h-7 bg-white dark:bg-zinc-600 rounded-full shadow-sm transition-all duration-300 mode-slider"
                style={{
                    transform: mode === 'pro' ? 'translateX(100%)' : 'translateX(0)'
                }}
            />

            {/* Lite button */}
            <button
                onClick={() => setMode('lite')}
                className={`relative z-10 px-3 py-1 text-xs font-bold rounded-full transition-colors duration-300 ${mode === 'lite'
                        ? 'text-gray-900 dark:text-white'
                        : 'text-gray-500 dark:text-gray-400'
                    }`}
                id="btn-lite"
            >
                Lite
            </button>

            {/* Pro button */}
            <button
                onClick={() => setMode('pro')}
                className={`relative z-10 px-3 py-1 text-xs font-bold rounded-full transition-colors duration-300 ${mode === 'pro'
                        ? 'text-gray-900 dark:text-white'
                        : 'text-gray-500 dark:text-gray-400'
                    }`}
                id="btn-pro"
            >
                Pro
            </button>
        </div>
    );
}
