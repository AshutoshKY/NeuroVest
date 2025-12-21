'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { TrendingUp, TrendingDown, RefreshCw, Trash2, BarChart2, Loader2 } from 'lucide-react';
import apiClient from '@/lib/api';

interface WatchlistStock {
    id: number;
    ticker: string;
    name: string;
    exchange: string;
    added_at: string;
}

interface StockData {
    ticker: string;
    name: string;
    current_price: number;
    currency: string;
    day_change: number;
    day_change_percent: number;
    day_high: number;
    day_low: number;
    volume: number;
    market_cap: number;
    pe_ratio: number | null;
    exchange: string;
    market_status: string;
    provider: string;
    timestamp: string;
}

interface BulkWatchlistResponse {
    stocks: StockData[];
    cached_count: number;
    fetched_count: number;
    failed: string[];
    total_time_ms: number;
}

export default function WatchlistPage() {
    const router = useRouter();
    const [watchlist, setWatchlist] = useState<WatchlistStock[]>([]);
    const [stocksData, setStocksData] = useState<StockData[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Fetch watchlist tickers
    const fetchWatchlist = async () => {
        try {
            setIsLoading(true);
            setError(null);

            // 1. Get watchlist tickers
            const watchlistResponse = await apiClient.get('/api/watchlist');
            const watchlistData: WatchlistStock[] = Array.isArray(watchlistResponse.data)
                ? watchlistResponse.data
                : [];

            setWatchlist(watchlistData);

            if (watchlistData.length === 0) {
                setIsLoading(false);
                return;
            }

            // 2. Fetch stock data in bulk
            const tickers = watchlistData.map(stock => stock.ticker);
            const bulkResponse = await apiClient.post<BulkWatchlistResponse>('/stocks/watchlist-data', {
                tickers
            });

            setStocksData(bulkResponse.data.stocks);

            console.log(
                `[WATCHLIST] Loaded ${bulkResponse.data.stocks.length} stocks ` +
                `(${bulkResponse.data.cached_count} cached, ${bulkResponse.data.fetched_count} fetched) ` +
                `in ${bulkResponse.data.total_time_ms}ms`
            );
        } catch (error: any) {
            console.error('[WATCHLIST] Error:', error);
            setError(error.response?.data?.detail || 'Failed to load watchlist');

            if (error.response?.status === 401) {
                router.push('/auth/login');
            }
        } finally {
            setIsLoading(false);
        }
    };

    // Refresh stock data
    const handleRefresh = async () => {
        if (watchlist.length === 0) return;

        setIsRefreshing(true);
        try {
            const tickers = watchlist.map(stock => stock.ticker);
            const bulkResponse = await apiClient.post<BulkWatchlistResponse>('/stocks/watchlist-data', {
                tickers
            });
            setStocksData(bulkResponse.data.stocks);
        } catch (error: any) {
            console.error('[WATCHLIST] Refresh error:', error);
            setError('Failed to refresh stock data');
        } finally {
            setIsRefreshing(false);
        }
    };

    // Remove from watchlist
    const removeFromWatchlist = async (ticker: string) => {
        try {
            await apiClient.delete(`/api/watchlist/${ticker}`);
            fetchWatchlist();
        } catch (error) {
            console.error('[WATCHLIST] Remove error:', error);
        }
    };

    // Analyze stock
    const analyzeStock = (ticker: string) => {
        router.push(`/dashboard?ticker=${ticker}`);
    };

    // Format numbers
    const formatNumber = (num: number, decimals = 2): string => {
        if (num >= 1e12) return `₹${(num / 1e12).toFixed(decimals)}T`;
        if (num >= 1e9) return `₹${(num / 1e9).toFixed(decimals)}B`;
        if (num >= 1e7) return `₹${(num / 1e7).toFixed(decimals)}Cr`;
        if (num >= 1e5) return `₹${(num / 1e5).toFixed(decimals)}L`;
        return `₹${num.toLocaleString('en-IN')}`;
    };

    useEffect(() => {
        fetchWatchlist();
    }, []);

    // Loading skeleton
    if (isLoading) {
        return (
            <div className="px-6 py-6 space-y-6">
                <div className="flex items-center gap-3">
                    <Loader2 className="w-8 h-8 animate-spin text-cyan-500" />
                    <div>
                        <h1 className="text-3xl font-bold text-white">Watchlist</h1>
                        <p className="text-slate-400">Loading your stocks...</p>
                    </div>
                </div>
                <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3">
                    {[1, 2, 3].map((i) => (
                        <div key={i} className="h-[420px] rounded-2xl bg-slate-800/30 animate-pulse border border-slate-700/50" />
                    ))}
                </div>
            </div>
        );
    }

    // Error state
    if (error) {
        return (
            <div className="px-6 py-6 space-y-6">
                <h1 className="text-3xl font-bold text-white">Watchlist</h1>
                <div className="p-6 rounded-2xl bg-red-500/10 border border-red-500/30 text-red-400">
                    <p className="font-semibold">Error loading watchlist</p>
                    <p className="text-sm mt-1">{error}</p>
                    <button
                        onClick={fetchWatchlist}
                        className="mt-4 px-4 py-2 rounded-lg bg-red-500/20 hover:bg-red-500/30 text-red-300 transition-colors"
                    >
                        Try Again
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="px-6 py-6 space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-white">Watchlist</h1>
                    <p className="text-slate-400">Real-time updates for your tracked stocks</p>
                </div>
                <div className="flex gap-3">
                    <button
                        onClick={handleRefresh}
                        disabled={isRefreshing || watchlist.length === 0}
                        className="px-4 py-2 rounded-xl bg-slate-800/50 border border-slate-700 text-slate-300 hover:bg-slate-700 hover:border-emerald-500/50 transition-all flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
                        Refresh
                    </button>
                    <button
                        onClick={() => router.push('/dashboard')}
                        className="px-4 py-2 rounded-xl bg-gradient-to-r from-emerald-600 to-cyan-600 text-white hover:from-emerald-500 hover:to-cyan-500 transition-all font-medium"
                    >
                        + Add Stock
                    </button>
                </div>
            </div>

            {/* Empty state */}
            {watchlist.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-16 px-4">
                    <div className="p-6 rounded-full bg-slate-800/30 mb-4">
                        <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-slate-600">
                            <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
                            <polyline points="9 22 9 12 15 12 15 22" />
                        </svg>
                    </div>
                    <h3 className="text-xl font-semibold text-white mb-2">Your watchlist is empty</h3>
                    <p className="text-slate-400 text-center max-w-md mb-6">
                        Add stocks from the dashboard to track them here and get real-time updates.
                    </p>
                    <button
                        onClick={() => router.push('/dashboard')}
                        className="px-6 py-3 rounded-xl bg-gradient-to-r from-emerald-600 to-cyan-600 text-white hover:from-emerald-500 hover:to-cyan-500 transition-all font-medium"
                    >
                        Browse Stocks
                    </button>
                </div>
            ) : (
                <AnimatePresence mode="wait">
                    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3">
                        {stocksData.map((stock) => (
                            <StockCard
                                key={stock.ticker}
                                stock={stock}
                                onAnalyze={analyzeStock}
                                onRemove={removeFromWatchlist}
                                formatNumber={formatNumber}
                            />
                        ))}
                    </div>
                </AnimatePresence>
            )}
        </div>
    );
}

// Stock Card Component
function StockCard({ stock, onAnalyze, onRemove, formatNumber }: {
    stock: StockData;
    onAnalyze: (ticker: string) => void;
    onRemove: (ticker: string) => void;
    formatNumber: (num: number, decimals?: number) => string;
}) {
    const isPositive = stock.day_change_percent >= 0;

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="group relative bg-gradient-to-br from-slate-900/60 via-slate-800/60 to-slate-900/60 backdrop-blur-xl border border-slate-700/50 rounded-2xl p-6 hover:border-cyan-500/50 transition-all duration-200 shadow-lg hover:shadow-cyan-500/10 min-h-[420px] flex flex-col"
        >
            {/* Header */}
            <div className="flex items-start justify-between mb-5">
                <div className="flex items-center gap-3">
                    <div className="p-3 rounded-lg bg-cyan-500/10 border border-cyan-500/20">
                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-cyan-400">
                            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
                        </svg>
                    </div>
                    <div>
                        <h3 className="text-xl font-bold text-white">{stock.ticker}</h3>
                        <p className="text-xs text-slate-400 truncate max-w-[180px]">{stock.name}</p>
                    </div>
                </div>
            </div>

            {/* Body */}
            <div className="flex-1 flex flex-col">
                {/* Price & Change */}
                <div className="mb-4">
                    <div className="flex items-baseline gap-2 mb-1">
                        <span className="text-2xl font-bold text-white">
                            ₹{stock.current_price.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </span>
                        <span className={`flex items-center gap-1 text-sm font-semibold ${isPositive ? 'text-emerald-400' : 'text-red-400'}`}>
                            {isPositive ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                            {isPositive ? '+' : ''}{stock.day_change.toFixed(2)} ({isPositive ? '+' : ''}{stock.day_change_percent.toFixed(2)}%)
                        </span>
                    </div>
                </div>

                {/* Day Range */}
                <div className="mb-4 p-3 rounded-xl bg-slate-900/50 border border-slate-700/50">
                    <p className="text-xs text-slate-500 mb-2">Day Range</p>
                    <div className="flex justify-between items-center">
                        <span className="text-sm font-medium text-slate-300">₹{stock.day_low.toLocaleString()}</span>
                        <div className="flex-1 mx-3 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                            <div
                                className="h-full bg-gradient-to-r from-red-500 via-yellow-500 to-emerald-500"
                                style={{
                                    width: `${((stock.current_price - stock.day_low) / (stock.day_high - stock.day_low)) * 100}%`
                                }}
                            />
                        </div>
                        <span className="text-sm font-medium text-slate-300">₹{stock.day_high.toLocaleString()}</span>
                    </div>
                </div>

                {/* Metrics Grid */}
                <div className="grid grid-cols-2 gap-3 mb-4">
                    <div className="p-3 rounded-xl bg-slate-900/50 border border-slate-700/50">
                        <p className="text-xs text-slate-500 mb-1">Volume</p>
                        <p className="text-sm font-semibold text-slate-200">{formatNumber(stock.volume, 1)}</p>
                    </div>
                    <div className="p-3 rounded-xl bg-slate-900/50 border border-slate-700/50">
                        <p className="text-xs text-slate-500 mb-1">Market Cap</p>
                        <p className="text-sm font-semibold text-slate-200">{formatNumber(stock.market_cap, 2)}</p>
                    </div>
                    <div className="p-3 rounded-xl bg-slate-900/50 border border-slate-700/50">
                        <p className="text-xs text-slate-500 mb-1">P/E Ratio</p>
                        <p className="text-sm font-semibold text-slate-200">{stock.pe_ratio !== null ? stock.pe_ratio.toFixed(2) : 'N/A'}</p>
                    </div>
                    <div className="p-3 rounded-xl bg-slate-900/50 border border-slate-700/50">
                        <p className="text-xs text-slate-500 mb-1">Exchange</p>
                        <p className="text-sm font-semibold text-slate-200">{stock.exchange}</p>
                    </div>
                </div>

                {/* Actions */}
                <div className="flex gap-2 mt-auto">
                    <button
                        onClick={() => onAnalyze(stock.ticker)}
                        className="flex-1 px-4 py-2 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 font-medium text-sm transition-colors border border-emerald-500/30 hover:border-emerald-500/50 flex items-center justify-center gap-2"
                    >
                        <BarChart2 className="w-4 h-4" />
                        Analyze
                    </button>
                    <button
                        onClick={() => onRemove(stock.ticker)}
                        className="px-4 py-2 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 font-medium text-sm transition-colors border border-red-500/30 hover:border-red-500/50"
                    >
                        <Trash2 className="w-4 h-4" />
                    </button>
                </div>
            </div>
        </motion.div>
    );
}
