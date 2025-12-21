'use client';

import { useUI } from '@/contexts/UIContext';
import { useState, useEffect } from 'react';

/**
 * Price Chart Component
 * Reuses existing Plotly candlestick chart
 * Responsive width based on mode (full in Lite, 55% in Pro)
 */

interface PriceChartProps {
    data: any; // historicalDataMulti from API
    ticker: string;
}

export function PriceChart({ data, ticker }: PriceChartProps) {
    const { mode } = useUI();
    const [CandlestickChart, setCandlestickChart] = useState<any>(null);

    // Dynamic import to avoid SSR issues with Plotly
    useEffect(() => {
        import('@/app/dashboard/components/PlotlyChart').then((mod) => {
            setCandlestickChart(() => mod.CandlestickChart);
        });
    }, []);

    return (
        <div className={`${mode === 'pro' ? 'lg:w-[55%]' : 'w-full'}`}>
            <div className="p-4 rounded-xl bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-sm font-bold text-gray-900 dark:text-white">Price Chart</h3>
                    <span className="text-xs text-gray-500 font-mono">{ticker}</span>
                </div>

                {data && CandlestickChart ? (
                    <CandlestickChart data={data} ticker={ticker} range="1d" />
                ) : (
                    <div className="h-64 flex items-center justify-center text-gray-500">
                        <div className="text-center">
                            <svg className="w-12 h-12 mx-auto mb-2 text-gray-400 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                            </svg>
                            <p className="text-sm">{CandlestickChart ? 'Loading chart...' : 'Initializing...'}</p>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
