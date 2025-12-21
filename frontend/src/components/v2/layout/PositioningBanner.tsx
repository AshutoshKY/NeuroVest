'use client';

import { useUI } from '@/contexts/UIContext';

/**
 * Positioning Banner
 * 8px height system notice bar
 * Matches design from analysis_8.html
 */

export function PositioningBanner() {
    const { mode } = useUI();

    return (
        <div className="w-full h-8 bg-white/95 dark:bg-[#09090b]/95 border-b border-gray-200 dark:border-zinc-800 flex items-center justify-center backdrop-blur-md fixed top-0 z-[60]">
            {/* Pro Mode Message */}
            <p className="text-[10px] font-mono text-gray-500 uppercase tracking-wide pro-element">
                <span className="text-primary-500 font-bold">SYSTEM NOTICE:</span> Structured market state engine. Visualizing
                probabilistic scenarios. Not advice.
            </p>

            {/* Lite Mode Message */}
            <p className="text-[10px] font-sans text-gray-500 tracking-wide lite-element">
                <span className="text-success font-bold">Simple View:</span> AI-powered summary for long-term investors.
            </p>
        </div>
    );
}
