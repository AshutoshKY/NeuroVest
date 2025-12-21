'use client';

import type { PriceZones as PriceZonesType } from '@/lib/api/mappers';

/**
 * Price Zones Visual Display
 * Pro Mode Only
 * Matches design from analysis_8.html
 */

interface PriceZonesProps {
    zones: PriceZonesType;
    ticker: string;
}

export function PriceZones({ zones, ticker }: PriceZonesProps) {
    const { support, value_area, resistance, current_price } = zones;

    // Calculate positions for visual display (percentage)
    const min = support.lower;
    const max = resistance.upper;
    const range = max - min;

    const getPosition = (price: number) => {
        return ((price - min) / range) * 100;
    };

    const currentPos = getPosition(current_price);
    const supportPos = getPosition(support.upper);
    const valuePos = getPosition(value_area.upper);
    const resistancePos = getPosition(resistance.lower);

    return (
        <div className="pro-element h-full">
            <div className="p-6 rounded-xl bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800 h-full space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h3 className="text-sm font-bold text-gray-900 dark:text-white mb-1">Price Zones</h3>
                        <p className="text-xs text-gray-500 font-mono">{ticker} | ₹{current_price.toFixed(2)}</p>
                    </div>
                    <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
                    </svg>
                </div>

                {/* Visual Zone Display */}
                <div className="relative h-64 bg-gray-100 dark:bg-zinc-950 rounded-lg border border-gray-200 dark:border-zinc-800 overflow-hidden">
                    {/* Resistance Zone */}
                    <div
                        className="absolute left-0 right-0 bg-yellow-500/10 border-t-2 border-b-2 border-yellow-500/30"
                        style={{
                            bottom: `${resistancePos}%`,
                            height: `${100 - resistancePos}%`
                        }}
                    >
                        <div className="absolute top-2 left-3 text-xs font-mono text-yellow-600 dark:text-yellow-500 font-bold">
                            RESISTANCE
                        </div>
                        <div className="absolute top-8 left-3 text-xs font-mono text-yellow-700 dark:text-yellow-400">
                            ₹{resistance.lower.toFixed(2)} - ₹{resistance.upper.toFixed(2)}
                        </div>
                    </div>

                    {/* Value Area Zone */}
                    <div
                        className="absolute left-0 right-0 bg-primary-500/10 border-t-2 border-b-2 border-primary-500/30"
                        style={{
                            bottom: `${supportPos}%`,
                            height: `${valuePos - supportPos}%`
                        }}
                    >
                        <div className="absolute top-2 left-3 text-xs font-mono text-primary-600 dark:text-primary-400 font-bold">
                            VALUE AREA
                        </div>
                        <div className="absolute top-8 left-3 text-xs font-mono text-primary-700 dark:text-primary-300">
                            ₹{value_area.lower.toFixed(2)} - ₹{value_area.upper.toFixed(2)}
                        </div>
                    </div>

                    {/* Support Zone */}
                    <div
                        className="absolute left-0 right-0 bg-gray-500/10 border-t-2 border-b-2 border-gray-500/30"
                        style={{
                            bottom: '0%',
                            height: `${supportPos}%`
                        }}
                    >
                        <div className="absolute top-2 left-3 text-xs font-mono text-gray-600 dark:text-gray-400 font-bold">
                            SUPPORT
                        </div>
                        <div className="absolute top-8 left-3 text-xs font-mono text-gray-700 dark:text-gray-300">
                            ₹{support.lower.toFixed(2)} - ₹{support.upper.toFixed(2)}
                        </div>
                    </div>

                    {/* Current Price Marker */}
                    <div
                        className="absolute left-0 right-0 border-t-2 border-dashed border-emerald-500 z-10"
                        style={{ bottom: `${currentPos}%` }}
                    >
                        <div className="absolute -top-2 right-3 flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full bg-emerald-500 shadow-lg shadow-emerald-500/50 animate-pulse" />
                            <span className="text-xs font-mono font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/30">
                                NOW: ₹{current_price.toFixed(2)}
                            </span>
                        </div>
                    </div>
                </div>

                {/* Legend */}
                <div className="grid grid-cols-2 gap-3 text-xs">
                    <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded bg-gray-500/30 border border-gray-500/50" />
                        <span className="text-gray-600 dark:text-gray-400">Support</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded bg-primary-500/30 border border-primary-500/50" />
                        <span className="text-gray-600 dark:text-gray-400">Value Area</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded bg-yellow-500/30 border border-yellow-500/50" />
                        <span className="text-gray-600 dark:text-gray-400">Resistance</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full bg-emerald-500" />
                        <span className="text-gray-600 dark:text-gray-400">Current Price</span>
                    </div>
                </div>
            </div>
        </div>
    );
}
