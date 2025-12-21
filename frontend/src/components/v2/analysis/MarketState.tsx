'use client';

import { useUI } from '@/contexts/UIContext';
import type { MarketState as MarketStateType } from '@/lib/api/mappers';

/**
 * Market State Component
 * Displays trend bias, confidence, momentum, volatility
 * Matches design from analysis_8.html
 */

interface MarketStateProps {
    marketState: MarketStateType;
}

export function MarketState({ marketState }: MarketStateProps) {
    const { mode } = useUI();

    const getTrendColor = (bias: string) => {
        if (bias === 'bullish') return 'text-success border-success/20 bg-success/10';
        if (bias === 'bearish') return 'text-danger border-danger/20 bg-danger/10';
        return 'text-gray-500 border-gray-500/20 bg-gray-500/10';
    };

    const getConfidenceLabel = (confidence: number) => {
        if (confidence >= 80) return 'Very High';
        if (confidence >= 60) return 'High';
        if (confidence >= 40) return 'Moderate';
        return 'Low';
    };

    return (
        <div className="space-y-4">
            {/* Lite Mode - 3 Cards */}
            <div className="lite-element">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {/* Trend Bias */}
                    <div className="p-5 rounded-xl bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800">
                        <div className="text-xs text-gray-500 mb-2 font-medium">Market Trend</div>
                        <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-bold border ${getTrendColor(marketState.trend_bias)}`}>
                            <span className="w-2 h-2 rounded-full bg-current" />
                            {marketState.trend_bias === 'bullish' ? 'Bullish' :
                                marketState.trend_bias === 'bearish' ? 'Bearish' : 'Neutral'}
                        </div>
                    </div>

                    {/* Confidence */}
                    <div className="p-5 rounded-xl bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800">
                        <div className="text-xs text-gray-500 mb-2 font-medium">Confidence</div>
                        <div className="space-y-2">
                            <div className="text-2xl font-bold text-gray-900 dark:text-white">
                                {marketState.confidence.toFixed(0)}%
                            </div>
                            <div className="w-full bg-gray-200 dark:bg-zinc-800 h-2 rounded-full overflow-hidden">
                                <div
                                    className="bg-primary-500 h-full transition-all duration-500"
                                    style={{ width: `${marketState.confidence}%` }}
                                />
                            </div>
                            <div className="text-xs text-gray-500">
                                {getConfidenceLabel(marketState.confidence)}
                            </div>
                        </div>
                    </div>

                    {/* Simple Summary */}
                    <div className="p-5 rounded-xl bg-gradient-to-br from-primary-500/10 to-purple-500/10 border border-primary-500/20">
                        <div className="text-xs text-primary-600 dark:text-primary-400 mb-2 font-bold">AI Summary</div>
                        <div className="text-sm text-gray-700 dark:text-gray-300">
                            {marketState.trend_bias === 'bullish'
                                ? '🚀 Market shows positive momentum'
                                : marketState.trend_bias === 'bearish'
                                    ? '⚠️ Market shows downward pressure'
                                    : '➡️ Market is consolidating'}
                        </div>
                    </div>
                </div>
            </div>

            {/* Pro Mode - 4 Cards with Technical Details */}
            <div className="pro-element">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    {/* Trend Bias */}
                    <div className="p-5 rounded-xl bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800 space-y-3">
                        <div className="flex items-center justify-between">
                            <div className="text-xs text-gray-500 font-mono uppercase tracking-wider">Trend Bias</div>
                            <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                            </svg>
                        </div>
                        <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-bold border ${getTrendColor(marketState.trend_bias)}`}>
                            <span className="w-2 h-2 rounded-full bg-current animate-pulse" />
                            {marketState.trend_bias?.toUpperCase() || 'UNKNOWN'}
                        </div>
                        <div className="text-xs text-gray-500 font-mono">
                            {marketState.trend_bias === 'bullish'
                                ? 'Upward momentum detected'
                                : marketState.trend_bias === 'bearish'
                                    ? 'Downward pressure active'
                                    : 'Range-bound consolidation'}
                        </div>
                    </div>

                    {/* Momentum */}
                    <div className="p-5 rounded-xl bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800 space-y-3">
                        <div className="flex items-center justify-between">
                            <div className="text-xs text-gray-500 font-mono uppercase tracking-wider">Momentum</div>
                            <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                            </svg>
                        </div>
                        <div className="text-lg font-bold text-gray-900 dark:text-white font-mono">
                            {marketState.momentum?.toUpperCase() || 'N/A'}
                        </div>
                        <div className="text-xs text-gray-500">
                            Velocity & direction
                        </div>
                    </div>

                    {/* Volatility */}
                    <div className="p-5 rounded-xl bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800 space-y-3">
                        <div className="flex items-center justify-between">
                            <div className="text-xs text-gray-500 font-mono uppercase tracking-wider">Volatility</div>
                            <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
                            </svg>
                        </div>
                        <div className={`text-lg font-bold font-mono ${marketState.volatility === 'high' ? 'text-danger' :
                                marketState.volatility === 'low' ? 'text-success' :
                                    'text-warning'
                            }`}>
                            {marketState.volatility?.toUpperCase() || 'N/A'}
                        </div>
                        <div className="text-xs text-gray-500">
                            Price fluctuation range
                        </div>
                    </div>

                    {/* Confidence */}
                    <div className="p-5 rounded-xl bg-gradient-to-br from-primary-500/10 to-purple-500/10 border border-primary-500/20 space-y-3">
                        <div className="flex items-center justify-between">
                            <div className="text-xs text-primary-600 dark:text-primary-400 font-mono uppercase tracking-wider font-bold">Confidence</div>
                            <svg className="w-4 h-4 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                        </div>
                        <div className="text-3xl font-bold text-gray-900 dark:text-white font-mono">
                            {marketState.confidence.toFixed(0)}%
                        </div>
                        <div className="w-full bg-gray-200 dark:bg-zinc-800 h-1.5 rounded-full overflow-hidden">
                            <div
                                className="bg-gradient-to-r from-primary-500 to-purple-500 h-full transition-all duration-500"
                                style={{ width: `${marketState.confidence}%` }}
                            />
                        </div>
                        <div className="text-xs text-gray-600 dark:text-gray-400 font-medium">
                            {getConfidenceLabel(marketState.confidence)} certainty
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
