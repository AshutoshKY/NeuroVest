'use client';

/**
 * Trending Stock Card - POC Design Match
 * Exactly matches design_poc_1/index.html
 */

interface TrendingCardProps {
    stock: {
        ticker: string;
        rank?: number;
        analysis_count?: number;
        change_percent?: number;
        sector?: string;
        market_cap?: string;
    };
    onClick: () => void;
}

export function TrendingCard({ stock, onClick }: TrendingCardProps) {
    // Sample data for demo
    const changePercent = stock.change_percent ?? (Math.random() > 0.5 ? 2.47 : -0.85);
    const sector = stock.sector ?? 'Energy';
    const marketCap = stock.market_cap ?? 'Large Cap';
    const isPositive = changePercent >= 0;

    // Get first letter for avatar
    const letter = stock.ticker.charAt(0).toUpperCase();

    return (
        <a
            href="#"
            onClick={(e) => {
                e.preventDefault();
                onClick();
            }}
            className="block bg-white dark:bg-[#18181b] border border-gray-200 dark:border-zinc-800 p-5 rounded-2xl hover:border-primary-500/50 hover:shadow-lg cursor-pointer transition group"
        >
            <div className="flex justify-between items-start mb-3">
                {/* Circular Avatar */}
                <div className="w-10 h-10 rounded-full bg-gray-100 dark:bg-zinc-800 flex items-center justify-center font-bold text-xs group-hover:bg-primary-500 group-hover:text-white transition">
                    {letter}
                </div>

                {/* Percentage Badge */}
                <span
                    className={`${isPositive
                        ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20'
                        : 'bg-red-500/10 text-red-500 border-red-500/20'
                        } text-xs font-mono px-2 py-1 rounded border`}
                >
                    {isPositive ? '+' : ''}{changePercent.toFixed(2)}%
                </span>
            </div>

            {/* Ticker Name */}
            <h4 className="text-lg font-bold text-gray-900 dark:text-white">{stock.ticker}</h4>

            {/* Sector + Market Cap */}
            <div className="text-xs text-gray-500">
                {sector} • {marketCap}
            </div>
        </a>
    );
}
