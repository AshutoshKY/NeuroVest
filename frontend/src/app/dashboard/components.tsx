import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import React from 'react';

// Advanced Candlestick Chart for Real Historical Data
export function CandlestickChart({ data, range }: { data: any; range: string }) {
    if (!data || !data[range]) {
        return (
            <div className="h-[300px] flex items-center justify-center text-gray-500">
                <span>No data available for {range}</span>
            </div>
        );
    }

    const periodData = data[range];
    const { timestamps, opens, highs, lows, closes, volumes } = periodData;

    if (!timestamps || timestamps.length === 0) {
        return (
            <div className="h-[300px] flex items-center justify-center text-gray-500">
                <span>Insufficient data</span>
            </div>
        );
    }

    // Simple visualization - show all data
    const max = Math.max(...highs);
    const min = Math.min(...lows);
    const range_val = max - min || 1;

    // Calculate bar width based on data count for better display
    const barWidth = timestamps.length > 200 ? 3 : timestamps.length > 100 ? 5 : 8;

    return (
        <div className="space-y-2">
            {/* Price Chart with all data points */}
            <div className="h-[250px] w-full bg-[#0a0e14] rounded-lg p-4 overflow-x-auto">
                <div className="flex items-end gap-0.5 h-full" style={{ minWidth: `${timestamps.length * barWidth}px` }}>
                    {closes.map((close: number, index: number) => {
                        const open = opens[index];
                        const high = highs[index];
                        const low = lows[index];
                        const isGreen = close >= open;

                        // Calculate heights as percentage, capped between 2% and 98%
                        const bodyTop = Math.max(close, open);
                        const bodyBottom = Math.min(close, open);
                        const height = Math.min(98, Math.max(2, ((bodyTop - bodyBottom) / range_val) * 100));
                        const bottomOffset = Math.min(95, Math.max(0, ((bodyBottom - min) / range_val) * 100));

                        return (
                            <motion.div
                                key={index}
                                initial={{ height: 0 }}
                                animate={{ height: `${height}%` }}
                                transition={{ duration: 0.2, delay: Math.min(index * 0.002, 0.5) }}
                                className={`flex-1 min-w-[${barWidth}px] rounded-sm ${isGreen ? 'bg-emerald-500/70' : 'bg-red-500/70'} hover:opacity-100 opacity-80 transition-opacity cursor-pointer`}
                                style={{ marginBottom: `${bottomOffset}%` }}
                                title={`Open: ${open.toFixed(2)}, Close: ${close.toFixed(2)}, High: ${high.toFixed(2)}, Low: ${low.toFixed(2)}`}
                            />
                        );
                    })}
                </div>
            </div>

            {/* Volume bars with all data */}
            <div className="h-[50px] w-full bg-[#0a0e14] rounded-lg p-2 overflow-x-auto">
                <div className="flex items-end gap-0.5 h-full" style={{ minWidth: `${timestamps.length * barWidth}px` }}>
                    {volumes && volumes.map((vol: number, index: number) => {
                        const maxVol = Math.max(...volumes);
                        const height = Math.min(100, Math.max(2, (vol / (maxVol || 1)) * 100));
                        const isGreen = closes[index] >= opens[index];

                        return (
                            <div
                                key={index}
                                className={`flex-1 min-w-[${barWidth}px] rounded-sm ${isGreen ? 'bg-emerald-500/50' : 'bg-red-500/50'}`}
                                style={{ height: `${height}%` }}
                                title={`Volume: ${vol.toLocaleString()}`}
                            />
                        );
                    })}
                </div>
            </div>
        </div>
    );
}

// Sentiment Badge Component
export const SentimentBadge: React.FC<{ sentiment: string }> = ({ sentiment }) => {
    // Type guard: ensure sentiment is a string
    const sentimentStr = String(sentiment || 'neutral').toLowerCase();

    const config = {
        bullish: { bg: 'bg-green-500/10', text: 'text-green-400', border: 'border-green-500/20', icon: TrendingUp },
        bearish: { bg: 'bg-red-500/10', text: 'text-red-400', border: 'border-red-500/20', icon: TrendingDown },
        neutral: { bg: 'bg-gray-500/10', text: 'text-gray-400', border: 'border-gray-500/20', icon: Minus }
    };

    const sentimentConfig = config[sentimentStr as keyof typeof config] || config.neutral;
    const Icon = sentimentConfig.icon;

    return (
        <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg border ${sentimentConfig.bg} ${sentimentConfig.border}`}>
            <Icon className={`w-4 h-4 ${sentimentConfig.text}`} />
            <span className={`font-semibold ${sentimentConfig.text} capitalize`}>{sentimentStr}</span>
        </div>
    );
};
