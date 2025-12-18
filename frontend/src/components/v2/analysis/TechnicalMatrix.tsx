'use client';

/**
 * Technical Matrix - Pro Mode Only
 * Grid displaying technical indicators
 * Matches design from analysis_8.html
 */

interface TechnicalMatrixProps {
    indicators?: {
        rsi?: number;
        macd?: { macd: number; signal: number; histogram: number };
        sma?: { 50: number; 200: number };
        bollinger?: { upper: number; middle: number; lower: number };
        volume?: number;
        atr?: number;
    };
}

export function TechnicalMatrix({ indicators = {} }: TechnicalMatrixProps) {
    const getRSISignal = (rsi?: number) => {
        if (!rsi) return { text: 'N/A', color: 'text-gray-500' };
        if (rsi > 70) return { text: 'Overbought', color: 'text-danger' };
        if (rsi < 30) return { text: 'Oversold', color: 'text-success' };
        return { text: 'Neutral', color: 'text-gray-500' };
    };

    const getMACDSignal = (macd?: { macd: number; signal: number }) => {
        if (!macd) return { text: 'N/A', color: 'text-gray-500' };
        if (macd.macd > macd.signal) return { text: 'Bullish', color: 'text-success' };
        if (macd.macd < macd.signal) return { text: 'Bearish', color: 'text-danger' };
        return { text: 'Neutral', color: 'text-gray-500' };
    };

    const getSMASignal = (sma?: { 50: number; 200: number }) => {
        if (!sma || !sma[50] || !sma[200]) return { text: 'N/A', color: 'text-gray-500' };
        if (sma[50] > sma[200]) return { text: 'Golden Cross', color: 'text-success' };
        if (sma[50] < sma[200]) return { text: 'Death Cross', color: 'text-danger' };
        return { text: 'Neutral', color: 'text-gray-500' };
    };

    const rsiSignal = getRSISignal(indicators.rsi);
    const macdSignal = getMACDSignal(indicators.macd);
    const smaSignal = getSMASignal(indicators.sma);

    return (
        <div className="pro-element">
            <div className="space-y-4">
                <div className="flex items-center justify-between">
                    <h3 className="text-lg font-bold text-gray-900 dark:text-white">Technical Matrix</h3>
                    <span className="text-xs text-gray-500 font-mono">INDICATORS</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    {/* RSI */}
                    <div className="p-4 rounded-xl bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800 space-y-3">
                        <div className="flex items-center justify-between">
                            <span className="text-xs text-gray-500 font-mono uppercase">RSI (14)</span>
                            <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                            </svg>
                        </div>
                        <div className="text-2xl font-bold text-gray-900 dark:text-white font-mono">
                            {indicators.rsi?.toFixed(1) || '--'}
                        </div>
                        <div className={`text-xs font-bold ${rsiSignal.color}`}>
                            {rsiSignal.text}
                        </div>
                        {indicators.rsi && (
                            <div className="w-full bg-gray-200 dark:bg-zinc-800 h-1.5 rounded-full overflow-hidden">
                                <div
                                    className="bg-primary-500 h-full"
                                    style={{ width: `${indicators.rsi}%` }}
                                />
                            </div>
                        )}
                    </div>

                    {/* MACD */}
                    <div className="p-4 rounded-xl bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800 space-y-3">
                        <div className="flex items-center justify-between">
                            <span className="text-xs text-gray-500 font-mono uppercase">MACD</span>
                            <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
                            </svg>
                        </div>
                        <div className="text-lg font-bold text-gray-900 dark:text-white font-mono">
                            {indicators.macd?.macd?.toFixed(2) || '--'}
                        </div>
                        <div className={`text-xs font-bold ${macdSignal.color}`}>
                            {macdSignal.text}
                        </div>
                        {indicators.macd && (
                            <div className="text-xs text-gray-500 space-y-0.5">
                                <div>Signal: {indicators.macd.signal?.toFixed(2)}</div>
                                <div>Hist: {indicators.macd.histogram?.toFixed(2)}</div>
                            </div>
                        )}
                    </div>

                    {/* SMA */}
                    <div className="p-4 rounded-xl bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800 space-y-3">
                        <div className="flex items-center justify-between">
                            <span className="text-xs text-gray-500 font-mono uppercase">SMA Cross</span>
                            <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                            </svg>
                        </div>
                        <div className={`text-sm font-bold font-mono ${smaSignal.color}`}>
                            {smaSignal.text}
                        </div>
                        {indicators.sma && (
                            <div className="text-xs text-gray-500 space-y-1">
                                <div>SMA 50: {indicators.sma[50]?.toFixed(2) || '--'}</div>
                                <div>SMA 200: {indicators.sma[200]?.toFixed(2) || '--'}</div>
                            </div>
                        )}
                    </div>

                    {/* Volume & ATR */}
                    <div className="p-4 rounded-xl bg-gradient-to-br from-primary-500/10 to-purple-500/10 border border-primary-500/20 space-y-3">
                        <div className="flex items-center justify-between">
                            <span className="text-xs text-primary-600 dark:text-primary-400 font-mono uppercase font-bold">Volatility</span>
                            <svg className="w-4 h-4 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                            </svg>
                        </div>
                        <div className="space-y-2">
                            <div>
                                <div className="text-xs text-gray-500 mb-1">ATR (14)</div>
                                <div className="text-lg font-bold text-gray-900 dark:text-white font-mono">
                                    {indicators.atr?.toFixed(2) || '--'}
                                </div>
                            </div>
                            {indicators.volume && (
                                <div>
                                    <div className="text-xs text-gray-500 mb-1">Volume</div>
                                    <div className="text-sm font-mono text-gray-700 dark:text-gray-300">
                                        {(indicators.volume / 1000000).toFixed(2)}M
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Disclaimer */}
                <div className="text-xs text-gray-500 text-center font-mono pt-2 border-t border-gray-200 dark:border-zinc-800">
                    Technical indicators for reference only | Not investment advice
                </div>
            </div>
        </div>
    );
}
