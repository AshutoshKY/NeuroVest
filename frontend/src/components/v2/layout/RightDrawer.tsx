'use client';

import { useState } from 'react';
import { X } from 'lucide-react';

/**
 * Right Drawer - Context Panel
 * Matches design from index.html
 */

interface RightDrawerProps {
    isOpen?: boolean;
    onClose?: () => void;
    analysisCount?: {
        remaining: number;
        limit: number;
    };
    savedAnalyses?: Array<{
        id: number;
        ticker: string;
        sentiment: string;
        price?: number;
        timestamp?: string;
    }>;
    onLoadAnalysis?: (id: number) => void;
}

export function RightDrawer({
    isOpen: externalIsOpen,
    onClose,
    analysisCount = { remaining: 0, limit: 5 },
    savedAnalyses = [],
    onLoadAnalysis
}: RightDrawerProps) {
    const [internalIsOpen, setInternalIsOpen] = useState(false);

    // Use external state if provided, otherwise use internal
    const isOpen = externalIsOpen !== undefined ? externalIsOpen : internalIsOpen;
    const toggleDrawer = () => {
        if (onClose) {
            onClose();
        } else {
            setInternalIsOpen(!internalIsOpen);
        }
    };

    const drawerClass = isOpen ? 'drawer open' : 'drawer closed';

    const progressPercentage = (analysisCount.remaining / analysisCount.limit) * 100;

    return (
        <aside
            id="right-drawer"
            className={`fixed top-16 right-0 bottom-0 w-80 bg-white dark:bg-[#18181b] border-l border-gray-200 dark:border-zinc-800 transition-transform duration-500 ${drawerClass} z-40 flex flex-col shadow-2xl`}
        >
            {/* Peek Handle */}
            <div
                className="absolute -left-3 top-1/2 w-3 h-12 bg-primary-500 rounded-l-md cursor-pointer flex items-center justify-center text-white hover:bg-primary-600 transition"
                onClick={toggleDrawer}
            >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
            </div>

            {/* Header */}
            <div className="p-4 border-b border-gray-200 dark:border-zinc-800 flex justify-between items-center bg-gray-50 dark:bg-zinc-900/50">
                <span className="text-xs font-bold text-gray-500 uppercase tracking-widest">Context</span>
                <button
                    onClick={toggleDrawer}
                    className="text-gray-400 hover:text-white transition"
                >
                    <X className="w-4 h-4" />
                </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4 space-y-6">
                {/* Daily Limit */}
                <div className="p-4 bg-gray-50 dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800 rounded-xl">
                    <div className="flex justify-between items-center mb-3">
                        <span className="text-sm font-semibold text-gray-700 dark:text-gray-300">Analysis Limit</span>
                        <span className="text-sm font-bold text-gray-900 dark:text-white">
                            {analysisCount.remaining} / {analysisCount.limit}
                        </span>
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-zinc-800 h-2.5 rounded-full overflow-hidden">
                        <div
                            className="bg-gradient-to-r from-primary-500 to-purple-600 h-full transition-all duration-300"
                            style={{ width: `${progressPercentage}%` }}
                        />
                    </div>
                    <div className="mt-2 text-xs text-gray-500 text-center">
                        {analysisCount.remaining} {analysisCount.remaining === 1 ? 'analysis' : 'analyses'} remaining today
                    </div>
                </div>

                {/* Saved Scans */}
                <div>
                    <div className="text-xs font-bold text-gray-500 mb-3">Saved Scans</div>
                    {savedAnalyses.length > 0 ? (
                        <div className="space-y-2">
                            {savedAnalyses.slice(0, 5).map((analysis) => (
                                <button
                                    key={analysis.id}
                                    onClick={() => onLoadAnalysis?.(analysis.id)}
                                    className="w-full p-3 bg-white dark:bg-zinc-950 border border-gray-200 dark:border-zinc-800 rounded-lg hover:border-primary-500/50 cursor-pointer transition text-left"
                                >
                                    <div className="flex justify-between text-gray-900 dark:text-white font-bold text-sm">
                                        <span>{analysis.ticker}</span>
                                        <span
                                            className={`${analysis.sentiment === 'Bullish'
                                                ? 'text-emerald-500'
                                                : analysis.sentiment === 'Bearish'
                                                    ? 'text-red-500'
                                                    : 'text-yellow-500'
                                                }`}
                                        >
                                            {analysis.sentiment}
                                        </span>
                                    </div>
                                    {analysis.price && (
                                        <div className="text-xs text-gray-500 mt-1">
                                            ₹{analysis.price.toFixed(2)} • {analysis.timestamp || '2m ago'}
                                        </div>
                                    )}
                                </button>
                            ))}
                        </div>
                    ) : (
                        <div className="p-3 bg-white dark:bg-zinc-950 border border-gray-200 dark:border-zinc-800 rounded-lg text-center">
                            <div className="text-sm text-gray-500">No saved analyses yet</div>
                            <div className="text-xs text-gray-400 mt-1">Analyze a stock to save it</div>
                        </div>
                    )}
                </div>
            </div>
        </aside>
    );
}

// Auto-peek animation on mount (optional - can be added to parent component)
export function useDrawerPeek() {
    useState(() => {
        const timer = setTimeout(() => {
            const drawer = document.getElementById('right-drawer');
            if (drawer) {
                drawer.style.transform = 'translateX(90%)';
                setTimeout(() => {
                    drawer.style.transform = '';
                }, 1000);
            }
        }, 500);

        return () => clearTimeout(timer);
    });
}
