'use client';

import { useEffect, useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuthStore } from '@/store/authStore';
import { Search, TrendingUp, Star, Sparkles, Globe, BookOpen, Lightbulb, Trophy, Loader, ChevronDown, ChevronUp, X, CheckCircle, AlertTriangle, Info, AlertCircle } from 'lucide-react';
import apiClient from '@/lib/api';
import { CandlestickChart } from './components/PlotlyChart';
import { SentimentBadge } from './components';
import { AnalysisResults } from './AnalysisResults';

interface SearchResult {
    ticker: string;
    name: string;
    exchange: string;
}

interface TrendingStock {
    ticker: string;
    analysis_count: number;
    rank: number;
}

interface IndianMarketStock {
    ticker: string;
    price: number;
    change: number;
}

export default function Dashboard() {
    const router = useRouter();
    const { isAuthenticated, checkGuestLimit } = useAuthStore();
    const [country, setCountry] = useState('India');
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
    const [selectedStock, setSelectedStock] = useState<SearchResult | null>(null);
    const [isSearching, setIsSearching] = useState(false);
    const [showDropdown, setShowDropdown] = useState(false);
    const [savedAnalyses, setSavedAnalyses] = useState<any[]>([]);
    const [trendingStocks, setTrendingStocks] = useState<TrendingStock[]>([]);
    const [indianMarketStocks, setIndianMarketStocks] = useState<IndianMarketStock[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const isSelectingStock = useRef(false);

    // Analysis state
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [analysisSteps, setAnalysisSteps] = useState<any[]>([]);
    const [analysisResult, setAnalysisResult] = useState<any>(null);
    const [progressStatus, setProgressStatus] = useState<'idle' | 'analyzing' | 'complete'>('idle');
    const [isStepsCollapsed, setIsStepsCollapsed] = useState(false);
    const [chartRange, setChartRange] = useState<string>('1d');
    const [saveMessage, setSaveMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);
    const [currentAnalysisId, setCurrentAnalysisId] = useState<string | null>(null); // Track if viewing saved analysis (UUID string)

    // Watchlist state
    const [watchlistTickers, setWatchlistTickers] = useState<string[]>([]);

    // Market facts - educational content
    const marketFacts = [
        { icon: '📅', title: 'Trading Hours', text: '9:15 AM - 3:30 PM IST (Mon-Fri)' },
        { icon: '📊', title: 'Major Indices', text: 'NIFTY 50, SENSEX, NIFTY BANK' },
        { icon: '💰', title: 'Market Cap', text: '$3.5+ Trillion (2024)' },
        { icon: '🏢', title: 'Listed Companies', text: '5,000+ on BSE, 2,000+ on NSE' },
        { icon: '🌍', title: 'Global Rank', text: '7th largest stock market' },
    ];

    const funTrivia = [
        { icon: '🎯', text: "NSE: World's largest derivatives exchange by contract volume" },
        { icon: '🏛️', text: 'BSE (1875): Asia\'s oldest stock exchange' },
        { icon: '⚡', text: 'SENSEX established in 1986, NIFTY in 1996' },
        { icon: '🚀', text: 'Circuit breakers: Trading halts at 10%, 15%, 20% moves' },
        { icon: '💎', text: 'T+2 Settlement: Trades settled in 2 business days' },
        { icon: '📈', text: 'SEBI regulates Indian securities market' },
        { icon: '🎲', text: 'Investors: 100M+ registered (2024)' },
    ];

    // Fetch initial data on mount - ONLY ONCE
    const hasInitialized = useRef(false);
    useEffect(() => {
        if (!isAuthenticated) {
            router.push('/auth/login');
            return;
        }

        // Prevent duplicate calls
        if (hasInitialized.current) {
            return;
        }
        hasInitialized.current = true;

        const fetchInitialData = async () => {
            try {
                // 1. Fetch trending cached stocks (/stocks/trending)
                const trendingRes = await apiClient.get('/stocks/trending').catch(() => ({ data: { trending_stocks: [] } }));
                setTrendingStocks(trendingRes.data.trending_stocks || []);

                // 2. Fetch Indian market trending stocks (/api/trending - Yahoo Finance)
                const indianRes = await fetch('/api/trending').catch(() => null);
                if (indianRes?.ok) {
                    const indianData = await indianRes.json();
                    setIndianMarketStocks(indianData || []);
                }

                // 3. Fetch saved analyses
                const savedRes = await apiClient.get('/api/saved-analyses').catch(() => ({ data: [] }));
                setSavedAnalyses(Array.isArray(savedRes.data) ? savedRes.data : []);

                // 4. Fetch watchlist tickers
                const watchlistRes = await apiClient.get('/api/watchlist').catch(() => ({ data: [] }));
                const watchlistData = Array.isArray(watchlistRes.data) ? watchlistRes.data : [];
                setWatchlistTickers(watchlistData.map((item: any) => item.ticker));

            } catch (error) {
                console.error('Failed to fetch data:', error);
            } finally {
                setIsLoading(false);
            }
        };

        fetchInitialData();
    }, [isAuthenticated, router]);

    // Debounced search - wait 500ms after user stops typing
    useEffect(() => {
        if (isSelectingStock.current) {
            isSelectingStock.current = false;
            return;
        }

        if (!searchQuery.trim()) {
            setSearchResults([]);
            setShowDropdown(false);
            return;
        }

        const debounceTimer = setTimeout(async () => {
            setIsSearching(true);
            try {
                const response = await apiClient.get(`/stocks/search?q=${encodeURIComponent(searchQuery)}&country=${country}`);
                setSearchResults(response.data.results || []);
                setShowDropdown(true);
            } catch (error) {
                console.error('Search failed:', error);
                setSearchResults([]);
            } finally {
                setIsSearching(false);
            }
        }, 500);

        return () => clearTimeout(debounceTimer);
    }, [searchQuery, country]);

    const handleSelectStock = (stock: SearchResult) => {
        isSelectingStock.current = true;
        setSelectedStock(stock);
        setSearchQuery(stock.name || stock.ticker);
        setShowDropdown(false);
        setSearchResults([]);
    };

    const handleAnalyze = async (stockOverride?: SearchResult) => {
        const stockToUse = stockOverride || selectedStock;

        if (!stockToUse) {
            alert('Please select a stock from the dropdown');
            return;
        }

        setIsAnalyzing(true);
        setProgressStatus('analyzing');
        setAnalysisSteps([]);
        setAnalysisResult(null);
        setIsStepsCollapsed(false);
        setCurrentAnalysisId(null); // Reset saved analysis state

        try {
            // Get tracking headers (required for authenticated users)
            const { TrackingHeaders } = await import('@/lib/tracking-headers');
            const trackingHeaders = await TrackingHeaders.getHeaders();

            const response = await fetch(
                `http://localhost:8000/stocks/${stockToUse.ticker}/analysis-stream`,
                {
                    credentials: 'include',
                    headers: {
                        ...trackingHeaders as any,
                        'Accept': 'text/event-stream',
                    },
                }
            );

            if (response.status === 429) {
                alert('Rate limit exceeded. Please try again later.');
                setIsAnalyzing(false);
                setProgressStatus('idle');
                return;
            }

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const reader = response.body?.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            let finalData: any = null;

            while (true) {
                const { done, value } = await reader!.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');  // CRITICAL FIX: was '\\n' (double backslash)
                buffer = lines.pop() || '';

                for (const line of lines) {
                    if (!line.trim() || !line.startsWith('data: ')) continue;

                    try {
                        const jsonStr = line.slice(6);
                        const data = JSON.parse(jsonStr);

                        if (data.type === 'step') {
                            const stepText = data.step.text || data.step.description || '';
                            setAnalysisSteps(prev => [...prev, {
                                ...data.step,
                                text: stepText
                            }]);
                        } else if (data.type === 'final') {
                            finalData = data.analysis;
                            setProgressStatus('complete');
                        } else if (data.type === 'error') {
                            console.error('Analysis error:', data);
                            setProgressStatus('idle');
                        }
                    } catch (parseError) {
                        // Skip malformed lines and continue
                        console.warn('Skipped malformed SSE line:', line.substring(0, 100));
                    }
                }
            }

            if (finalData) {
                const sentiment = finalData.sentiment || {};
                const techAnalysis = finalData.technical_analysis || {};
                const indicators = techAnalysis.indicators || {};

                setAnalysisResult({
                    ticker: finalData.ticker,
                    price: finalData.current_price || 0,
                    sentiment: sentiment.classification || 'Neutral',
                    confidence: (sentiment.average_confidence || sentiment.confidence || 0) * 100,
                    rsi: indicators.rsi?.value || 0,
                    macd: indicators.macd?.macd || 0,
                    macdSignal: indicators.macd?.signal || 0,
                    macdHist: indicators.macd?.histogram || 0,
                    bollingerUpper: indicators.bollinger_bands?.upper || 0,
                    bollingerMiddle: indicators.bollinger_bands?.middle || 0,
                    bollingerLower: indicators.bollinger_bands?.lower || 0,

                    // NEW: Pass structured data to AnalysisResults component
                    analysis_structured: finalData.analysis_structured || null,
                    prediction_structured: finalData.prediction_structured || null,

                    // OLD: Keep for backward compatibility
                    aiAnalysis: finalData.analysis || '',
                    analysis: finalData.analysis || '',
                    prediction: finalData.prediction || finalData.future_outlook || 'No prediction available',
                    futureOutlook: finalData.prediction || finalData.future_outlook || 'No prediction available',

                    insights: finalData.key_insights || [],
                    risks: finalData.risk_factors || [],
                    references: finalData.references || [],
                    dayLow: finalData.day_low || 0,
                    dayHigh: finalData.day_high || 0,
                    currency: finalData.currency || 'INR',
                    historicalDataMulti: finalData.historical_data_multi || {},
                });
            }

            // Refresh trending stocks after analysis
            const trendingRes = await apiClient.get('/stocks/trending').catch(() => ({ data: { trending_stocks: [] } }));
            setTrendingStocks(trendingRes.data.trending_stocks || []);

            // Auto-save to history
            try {
                await apiClient.post('/api/history', {
                    ticker: finalData.ticker || selectedStock?.ticker,
                    name: finalData.name || selectedStock?.name || finalData.ticker,
                    exchange: finalData.exchange || selectedStock?.exchange || 'NSE',
                    analysis_data: finalData
                });
            } catch (historyError) {
                console.warn('Failed to save to history:', historyError);
                // Don't fail the analysis if history save fails
            }

            // Refresh user's limit after analysis
            await checkGuestLimit();

            // Refresh the header counter display
            if (typeof (window as any).refreshAnalysisCounter === 'function') {
                await (window as any).refreshAnalysisCounter();
            }

        } catch (error: any) {
            console.error('Analysis failed:', error);
            setProgressStatus('idle');
            alert('Analysis failed. Please try again.');
        } finally {
            setIsAnalyzing(false);
        }
    };

    const handleReset = () => {
        setAnalysisResult(null);
        setAnalysisSteps([]);
        setProgressStatus('idle');
        setSearchQuery('');
        setSelectedStock(null);
    };

    const handleSaveAnalysis = async (analysisData: any) => {
        try {
            // Prepare analysis data - convert confidence from percentage to decimal
            const dataToSave = {
                ...analysisData,
                name: analysisData.name || selectedStock?.name || analysisData.ticker,
                confidence: (analysisData.confidence || 0) / 100  // Convert 87 -> 0.87
            };

            const response = await apiClient.post('/api/saved-analyses', {
                ticker: analysisData.ticker,
                title: null,
                analysis_data: dataToSave
            });

            // Mark as saved
            if (response.data?.id) {
                setCurrentAnalysisId(response.data.id);
            }

            // Show success message
            setSaveMessage({ type: 'success', text: `Analysis for ${analysisData.ticker} saved successfully!` });
            setTimeout(() => setSaveMessage(null), 3000);

            // Optimized: Add to local state instead of refetching entire list
            if (response.data) {
                setSavedAnalyses(prev => [response.data, ...prev]);
            }
        } catch (error: any) {
            // Show error message
            const errorMsg = error.response?.data?.detail || 'Failed to save analysis';
            setSaveMessage({ type: 'error', text: errorMsg });
            setTimeout(() => setSaveMessage(null), 5000);
        }
    };

    const handleLoadSavedAnalysis = async (id: string) => {
        try {
            const response = await apiClient.get(`/api/saved-analyses/${id}`);
            const loadedData = response.data.analysis_data;

            setAnalysisResult(loadedData);
            setProgressStatus('complete');
            setCurrentAnalysisId(id); // Mark as saved analysis (UUID string)
            setSelectedStock({
                ticker: loadedData.ticker,
                name: loadedData.name || loadedData.ticker,
                exchange: loadedData.exchange || '', // Ensure exchange is set if available
            });

            // Auto-save to history when viewing cached analysis
            try {
                await apiClient.post('/api/history', {
                    ticker: loadedData.ticker,
                    name: loadedData.name || loadedData.ticker,
                    exchange: loadedData.exchange || 'NSE',
                    analysis_data: loadedData
                });
            } catch (historyError) {
                console.warn('Failed to save cached analysis to history:', historyError);
            }
        } catch (error) {
            console.error('Failed to load saved analysis:', error);
        }
    };

    const handleDeleteSavedAnalysis = async (id: string) => {
        try {
            await apiClient.delete(`/api/saved-analyses/${id}`);

            // UUID comparison - compare as strings (not parseInt!)
            setSavedAnalyses(prev => prev.filter(analysis => analysis.id !== id));

            setSaveMessage({ type: 'success', text: 'Analysis deleted successfully' });
            setTimeout(() => setSaveMessage(null), 3000);
        } catch (error) {
            setSaveMessage({ type: 'error', text: 'Failed to delete analysis' });
            setTimeout(() => setSaveMessage(null), 3000);
        }
    };

    const handleAddToWatchlist = async () => {
        if (!selectedStock) return;

        try {
            await apiClient.post('/api/watchlist', {
                ticker: selectedStock.ticker,
                name: selectedStock.name || selectedStock.ticker,
                exchange: selectedStock.exchange || 'NSE'
            });

            setSaveMessage({ type: 'success', text: `${selectedStock.ticker} added to watchlist!` });
            setTimeout(() => setSaveMessage(null), 3000);
        } catch (error: any) {
            const errorMsg = error.response?.data?.detail || 'Failed to add to watchlist';
            setSaveMessage({ type: 'error', text: errorMsg });
            setTimeout(() => setSaveMessage(null), 5000);
        }
    };

    // Watchlist helper functions
    const isInWatchlist = (ticker: string): boolean => {
        return watchlistTickers.includes(ticker);
    };

    const toggleWatchlist = async (ticker: string, name: string, exchange: string = 'NSE', event?: React.MouseEvent) => {
        // Prevent event bubbling
        if (event) {
            event.stopPropagation();
        }

        try {
            if (isInWatchlist(ticker)) {
                // Remove from watchlist
                await apiClient.delete(`/api/watchlist/${ticker}`);
                setWatchlistTickers(prev => prev.filter(t => t !== ticker));
                setSaveMessage({ type: 'success', text: `${ticker} removed from watchlist` });
            } else {
                // Add to watchlist
                await apiClient.post('/api/watchlist', { ticker, name, exchange });
                setWatchlistTickers(prev => [...prev, ticker]);
                setSaveMessage({ type: 'success', text: `${ticker} added to watchlist!` });
            }
            setTimeout(() => setSaveMessage(null), 3000);
        } catch (error: any) {
            const errorMsg = error.response?.data?.detail || 'Failed to update watchlist';
            setSaveMessage({ type: 'error', text: errorMsg });
            setTimeout(() => setSaveMessage(null), 5000);
        }
    };


    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-emerald-950/20">
            {/* Toast Notification */}
            <AnimatePresence>
                {saveMessage && (
                    <motion.div
                        initial={{ opacity: 0, y: -50 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -50 }}
                        className="fixed top-4 right-4 z-50"
                    >
                        <div className={`px - 6 py - 4 rounded - xl shadow - 2xl flex items - center gap - 3 ${saveMessage.type === 'success'
                            ? 'bg-emerald-500 text-white'
                            : 'bg-red-500 text-white'
                            } `}>
                            {saveMessage.type === 'success' ? (
                                <CheckCircle size={20} />
                            ) : (
                                <AlertCircle size={20} />
                            )}
                            <span className="font-medium">{saveMessage.text}</span>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            <div className="max-w-[1600px] mx-auto px-4 py-6">
                {/* 3-Column Layout */}
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                    {/* LEFT SIDEBAR - Trending NeuroVest (Cached) */}
                    <div className="lg:col-span-3 space-y-6">
                        {/* Trending Stocks Section */}
                        <motion.div
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: 0.05 }}
                            className="bg-slate-900/50 backdrop-blur-xl border border-slate-800/50 rounded-2xl p-6 hover:border-emerald-500/30 transition-all"
                        >
                            <div className="flex items-center gap-3 mb-5">
                                <div className="p-2.5 rounded-xl bg-gradient-to-br from-emerald-500/10 to-cyan-500/10 border border-emerald-500/20">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-emerald-400">
                                        <path d="M3 3v18h18" />
                                        <path d="m19 9-5 5-4-4-3 3" />
                                    </svg>
                                </div>
                                <h3 className="text-base font-semibold text-white">Trending in NeuroVest</h3>
                            </div>

                            {isLoading ? (
                                <div className="text-center py-8 text-slate-500 text-sm">Loading...</div>
                            ) : trendingStocks.length === 0 ? (
                                <div className="text-center py-8 text-slate-500 text-sm">No trending stocks yet</div>
                            ) : (
                                <div className="space-y-2.5">
                                    {trendingStocks.map((stock) => {
                                        const inWatchlist = isInWatchlist(stock.ticker);

                                        return (
                                            <div key={stock.ticker} className="group relative">
                                                <button
                                                    onClick={() => {
                                                        const stockData = {
                                                            ticker: stock.ticker,
                                                            name: stock.ticker,
                                                            exchange: 'NSE'
                                                        };
                                                        handleSelectStock(stockData);
                                                        handleAnalyze(stockData);
                                                    }}
                                                    className="w-full p-4 pr-12 rounded-xl bg-gradient-to-r from-slate-800/40 to-slate-800/20 hover:from-emerald-500/10 hover:to-cyan-500/10 transition-all border border-slate-700/50 hover:border-emerald-500/40 hover:shadow-lg hover:shadow-emerald-500/5"
                                                >
                                                    <div className="flex items-center justify-between gap-3">
                                                        <div className="flex items-center gap-3 flex-1 min-w-0">
                                                            {/* Rank Badge */}
                                                            <div className={`flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center font-bold text-sm ${stock.rank === 1 ? 'bg-gradient-to-br from-yellow-500 to-orange-500 text-white' :
                                                                stock.rank === 2 ? 'bg-gradient-to-br from-slate-400 to-slate-500 text-white' :
                                                                    stock.rank === 3 ? 'bg-gradient-to-br from-orange-600 to-orange-700 text-white' :
                                                                        'bg-slate-700/50 text-slate-400'
                                                                }`}>
                                                                #{stock.rank}
                                                            </div>

                                                            {/* Stock Info */}
                                                            <div className="flex-1 min-w-0">
                                                                <div className="font-semibold text-white text-sm mb-0.5">{stock.ticker}</div>
                                                                <div className="flex items-center gap-1.5 text-xs text-slate-400">
                                                                    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                                                        <path d="M9 11l3 3L22 4" />
                                                                        <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11" />
                                                                    </svg>
                                                                    <span>{stock.analysis_count}× analyzed</span>
                                                                </div>
                                                            </div>
                                                        </div>

                                                        {/* Arrow Icon */}
                                                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-emerald-400 group-hover:translate-x-1 transition-transform">
                                                            <path d="M5 12h14" />
                                                            <path d="m12 5 7 7-7 7" />
                                                        </svg>
                                                    </div>
                                                </button>

                                                {/* Hover star button */}
                                                <button
                                                    onClick={(e) => toggleWatchlist(stock.ticker, stock.ticker, 'NSE', e)}
                                                    className={`absolute right-2.5 top-1/2 -translate-y-1/2 p-2 rounded-lg transition-all opacity-0 group-hover:opacity-100 bg-slate-900/90 backdrop-blur-sm border border-slate-700/50 ${inWatchlist
                                                        ? 'text-cyan-400 hover:text-cyan-300'
                                                        : 'text-slate-400 hover:text-cyan-400'
                                                        }`}
                                                    title={inWatchlist ? 'Remove from watchlist' : 'Add to watchlist'}
                                                >
                                                    {inWatchlist ? (
                                                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" strokeWidth="2">
                                                            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
                                                        </svg>
                                                    ) : (
                                                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                                            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
                                                        </svg>
                                                    )}
                                                </button>
                                            </div>
                                        );
                                    })}
                                </div>
                            )}
                        </motion.div>

                        {/* Market Facts */}
                        <motion.div
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: 0.1 }}
                            className="bg-slate-900/50 backdrop-blur-xl border border-slate-800/50 rounded-2xl p-5"
                        >
                            <div className="flex items-center gap-2 mb-4">
                                <div className="p-2 rounded-lg bg-blue-500/10">
                                    <BookOpen className="w-4 h-4 text-blue-400" />
                                </div>
                                <h3 className="text-base font-semibold text-white">Market Facts</h3>
                            </div>
                            <div className="space-y-2.5">
                                {marketFacts.map((fact, index) => (
                                    <div key={index} className="p-2.5 rounded-lg bg-slate-800/30 border border-slate-700/50">
                                        <p className="text-xs font-semibold mb-1 text-slate-400">{fact.icon} {fact.title}</p>
                                        <p className="text-xs text-slate-300">{fact.text}</p>
                                    </div>
                                ))}
                            </div>
                        </motion.div>
                    </div>

                    {/* CENTER - Search & Analysis Results */}
                    < div className="lg:col-span-6 space-y-6" >
                        {/* Show Hero + Search when not analyzing/no results */}
                        {
                            !analysisResult && !isAnalyzing && (
                                <>
                                    {/* Hero Section */}
                                    <motion.div
                                        initial={{ opacity: 0, y: 20 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        className="text-center"
                                    >
                                        <h1 className="text-4xl md:text-5xl font-bold text-white mb-3">
                                            <span className="bg-gradient-to-r from-emerald-400 via-cyan-400 to-blue-400 bg-clip-text text-transparent">
                                                Unlock Market Insights
                                            </span>
                                            <br />
                                            <span className="text-2xl md:text-3xl text-slate-300">Instantly ⚡</span>
                                        </h1>
                                        <p className="text-slate-400 text-sm max-w-md mx-auto">Powered by advanced AI • Real-time data • Smart predictions</p>
                                    </motion.div>

                                    {/* Search Card */}
                                    <motion.div
                                        initial={{ opacity: 0, y: 20 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        transition={{ delay: 0.1 }}
                                        className="bg-slate-900/50 backdrop-blur-xl border border-emerald-500/20 rounded-2xl p-6 shadow-2xl shadow-emerald-500/10"
                                    >
                                        <div className="mb-5">
                                            <label className="flex items-center gap-2 text-sm font-medium text-slate-300 mb-3">
                                                <Globe className="w-4 h-4 text-emerald-400" />
                                                Market Region
                                            </label>
                                            <div className="relative">
                                                <select
                                                    value={country}
                                                    onChange={(e) => setCountry(e.target.value)}
                                                    className="w-full px-5 py-3.5 bg-gradient-to-br from-slate-800/80 to-slate-900/80 border-2 border-slate-700/50 rounded-xl text-white font-medium focus:border-emerald-500 focus:ring-4 focus:ring-emerald-500/20 transition-all outline-none appearance-none cursor-pointer hover:border-emerald-500/50 shadow-lg"
                                                >
                                                    <option>🇮🇳 India</option>
                                                    <option>🇺🇸 United States</option>
                                                    <option>🇬🇧 United Kingdom</option>
                                                </select>
                                                <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 pointer-events-none" />
                                            </div>
                                        </div>

                                        <div className="relative">
                                            <div className="relative group">
                                                <Search className="absolute left-5 top-1/2 transform -translate-y-1/2 w-5 h-5 text-emerald-400 transition-all group-focus-within:scale-110" />
                                                <input
                                                    type="text"
                                                    value={searchQuery}
                                                    onChange={(e) => setSearchQuery(e.target.value)}
                                                    placeholder="Search stocks (RELIANCE, TCS, INFY)..."
                                                    className="w-full pl-14 pr-5 py-4 bg-gradient-to-br from-slate-800/80 to-slate-900/80 border-2 border-slate-700/50 rounded-xl text-white text-lg placeholder-slate-500 focus:border-emerald-500 focus:ring-4 focus:ring-emerald-500/20 transition-all outline-none shadow-lg hover:border-emerald-500/50"
                                                />
                                                {isSearching && (
                                                    <div className="absolute right-4 top-1/2 transform -translate-y-1/2">
                                                        <Loader className="w-5 h-5 text-emerald-500 animate-spin" />
                                                    </div>
                                                )}
                                            </div>

                                            {showDropdown && searchResults.length > 0 && (
                                                <motion.div
                                                    initial={{ opacity: 0, y: -10 }}
                                                    animate={{ opacity: 1, y: 0 }}
                                                    className="absolute z-10 w-full mt-2 bg-slate-900 border border-slate-800 rounded-xl shadow-2xl max-h-64 overflow-y-auto"
                                                >
                                                    {searchResults.map((result, index) => {
                                                        const inWatchlist = isInWatchlist(result.ticker);

                                                        return (
                                                            <div
                                                                key={index}
                                                                className="flex items-center justify-between px-4 py-3 hover:bg-slate-800 transition-colors border-b border-slate-800 last:border-b-0"
                                                            >
                                                                <button
                                                                    onClick={() => handleSelectStock(result)}
                                                                    className="flex-1 text-left"
                                                                >
                                                                    <div className="font-semibold text-white">{result.ticker}</div>
                                                                    <div className="text-sm text-slate-400">{result.name}</div>
                                                                </button>

                                                                {/* Watchlist toggle button */}
                                                                <button
                                                                    onClick={(e) => toggleWatchlist(result.ticker, result.name, result.exchange, e)}
                                                                    className={`p-2 rounded-lg transition-all hover:scale-110 ${inWatchlist
                                                                        ? 'text-cyan-400 hover:text-cyan-300'
                                                                        : 'text-slate-500 hover:text-cyan-400'
                                                                        }`}
                                                                    title={inWatchlist ? 'Remove from watchlist' : 'Add to watchlist'}
                                                                >
                                                                    {inWatchlist ? (
                                                                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" strokeWidth="2">
                                                                            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
                                                                        </svg>
                                                                    ) : (
                                                                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                                                            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
                                                                        </svg>
                                                                    )}
                                                                </button>
                                                            </div>
                                                        );
                                                    })}
                                                </motion.div>
                                            )}
                                        </div>

                                        <motion.button
                                            whileHover={{ scale: 1.03, boxShadow: "0 20px 60px rgba(16, 185, 129, 0.4)" }}
                                            whileTap={{ scale: 0.97 }}
                                            onClick={() => handleAnalyze()}
                                            disabled={!selectedStock}
                                            className="w-full mt-6 py-4 bg-gradient-to-r from-emerald-500 via-cyan-500 to-blue-500 hover:from-emerald-600 hover:via-cyan-600 hover:to-blue-600 text-white text-lg font-bold rounded-xl shadow-2xl shadow-emerald-500/40 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-3 relative overflow-hidden group"
                                        >
                                            <div className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/20 to-white/0 -translate-x-full group-hover:translate-x-full transition-transform duration-1000" />
                                            <Sparkles className="w-5 h-5" />
                                            <span>Analyze Stock</span>
                                            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                                <line x1="5" y1="12" x2="19" y2="12" />
                                                <polyline points="12 5 19 12 12 19" />
                                            </svg>
                                        </motion.button>
                                    </motion.div>

                                    {/* Saved Analyses */}
                                    <motion.div
                                        initial={{ opacity: 0, y: 20 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        transition={{ delay: 0.2 }}
                                        className="bg-slate-900/50 backdrop-blur-xl border border-slate-800/50 rounded-2xl p-6 hover:border-emerald-500/30 transition-all"
                                    >
                                        <div className="flex items-center justify-between mb-4">
                                            <div className="flex items-center gap-2">
                                                <div className="p-2 rounded-lg bg-emerald-500/10">
                                                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-emerald-400">
                                                        <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" />
                                                        <polyline points="17 21 17 13 7 13 7 21" />
                                                        <polyline points="7 3 7 8 15 8" />
                                                    </svg>
                                                </div>
                                                <h3 className="text-lg font-semibold text-white">Saved Analyses</h3>
                                            </div>
                                            <span className="text-xs text-slate-500 bg-slate-800 px-2 py-1 rounded-lg">{savedAnalyses.length}/10</span>
                                        </div>

                                        {isLoading ? (
                                            <div className="text-center py-8 text-slate-500">Loading...</div>
                                        ) : savedAnalyses.length === 0 ? (
                                            <div className="text-center py-8">
                                                <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-slate-700 mx-auto mb-2">
                                                    <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" />
                                                    <polyline points="17 21 17 13 7 13 7 21" />
                                                    <polyline points="7 3 7 8 15 8" />
                                                </svg>
                                                <p className="text-slate-500 text-sm">No saved analyses</p>
                                                <p className="text-slate-600 text-xs mt-1">Save your first analysis (limit: 10)</p>
                                            </div>
                                        ) : (
                                            <div className="space-y-3">
                                                {savedAnalyses.map((item: any) => (
                                                    <div
                                                        key={item.id}
                                                        className="group relative p-4 rounded-xl bg-gradient-to-br from-slate-800/40 via-slate-800/60 to-slate-800/40 hover:from-slate-800/60 hover:via-slate-700/80 hover:to-slate-800/60 border border-slate-700/50 hover:border-emerald-500/50 transition-all duration-200 shadow-lg hover:shadow-emerald-500/10"
                                                    >
                                                        <button
                                                            onClick={() => handleLoadSavedAnalysis(item.id)}
                                                            className="w-full text-left"
                                                        >
                                                            {/* Stock Ticker & Sentiment */}
                                                            <div className="flex items-center justify-between mb-3">
                                                                <div className="flex items-center gap-3">
                                                                    <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                                                                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-emerald-400">
                                                                            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
                                                                        </svg>
                                                                    </div>
                                                                    <div>
                                                                        <h4 className="text-lg font-bold text-white">{item.ticker}</h4>
                                                                        <p className="text-xs text-slate-400 truncate">{item.name || 'Stock Analysis'}</p>
                                                                    </div>
                                                                </div>
                                                                <SentimentBadge sentiment={item.sentiment} />
                                                            </div>

                                                            {/* Price & Confidence Metrics */}
                                                            <div className="grid grid-cols-2 gap-3 mb-3">
                                                                <div className="p-2 rounded-lg bg-slate-900/50 border border-slate-700/50">
                                                                    <p className="text-xs text-slate-500 mb-0.5">Price</p>
                                                                    <p className="text-base font-semibold text-emerald-400">
                                                                        {item.currency === 'USD' ? '$' : '₹'}{item.price?.toLocaleString() || 'N/A'}
                                                                    </p>
                                                                </div>
                                                                <div className="p-2 rounded-lg bg-slate-900/50 border border-slate-700/50">
                                                                    <p className="text-xs text-slate-500 mb-0.5">Confidence</p>
                                                                    <p className="text-base font-semibold text-cyan-400">
                                                                        {item.confidence ? `${(item.confidence * 100).toFixed(0)}% ` : 'N/A'}
                                                                    </p>
                                                                </div>
                                                            </div>

                                                            {/* Date & Time */}
                                                            <div className="flex items-center gap-2 text-xs text-slate-500">
                                                                <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                                                    <circle cx="12" cy="12" r="10" />
                                                                    <polyline points="12 6 12 12 16 14" />
                                                                </svg>
                                                                <span>
                                                                    {new Date(item.saved_at).toLocaleDateString('en-US', {
                                                                        month: 'short',
                                                                        day: 'numeric',
                                                                        year: 'numeric'
                                                                    })}
                                                                    {' at '}
                                                                    {new Date(item.saved_at).toLocaleTimeString('en-US', {
                                                                        hour: '2-digit',
                                                                        minute: '2-digit'
                                                                    })}
                                                                </span>
                                                            </div>
                                                        </button>

                                                        {/* Delete Button */}
                                                        <button
                                                            onClick={() => handleDeleteSavedAnalysis(item.id)}
                                                            className="absolute top-3 right-3 p-2 rounded-lg hover:bg-red-500/20 text-slate-500 hover:text-red-400 transition-colors opacity-0 group-hover:opacity-100"
                                                            title="Delete"
                                                        >
                                                            <X size={16} />
                                                        </button>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </motion.div>
                                </>
                            )
                        }

                        {/* Analysis Progress & Results */}
                        {
                            (progressStatus === 'analyzing' || (progressStatus === 'complete' && analysisResult)) && (
                                <AnalysisResults
                                    progressStatus={progressStatus}
                                    selectedStock={selectedStock}
                                    analysisSteps={analysisSteps}
                                    isStepsCollapsed={isStepsCollapsed}
                                    setIsStepsCollapsed={setIsStepsCollapsed}
                                    analysisResult={analysisResult}
                                    chartRange={chartRange}
                                    setChartRange={setChartRange}
                                    onClose={() => {
                                        handleReset();
                                        setCurrentAnalysisId(null); // Reset on close
                                    }}
                                    onSave={handleSaveAnalysis}
                                    onAddToWatchlist={handleAddToWatchlist}
                                    isSaved={currentAnalysisId !== null}
                                    isInWatchlist={selectedStock ? isInWatchlist(selectedStock.ticker) : false}
                                />
                            )
                        }
                    </div >

                    {/* RIGHT SIDEBAR - Indian Market Trending (Live Yahoo Finance) */}
                    < div className="lg:col-span-3 space-y-6" >
                        <motion.div
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            className="bg-slate-900/50 backdrop-blur-xl border border-slate-800/50 rounded-2xl p-5"
                        >
                            <div className="flex items-center gap-2 mb-4">
                                <div className="p-2 rounded-lg bg-orange-500/10">
                                    <Trophy className="w-4 h-4 text-orange-400" />
                                </div>
                                <h3 className="text-base font-semibold text-white">Indian Market Trending</h3>
                            </div>
                            {isLoading ? (
                                <div className="text-center py-8 text-slate-500 text-sm">Loading...</div>
                            ) : indianMarketStocks.length === 0 ? (
                                <div className="text-center py-8 text-slate-500 text-sm">No market data available</div>
                            ) : (
                                <div className="space-y-2">
                                    {indianMarketStocks.slice(0, 6).map((stock, index) => {
                                        const inWatchlist = isInWatchlist(stock.ticker);

                                        return (
                                            <div key={index} className="group relative">
                                                <button
                                                    onClick={() => {
                                                        const stockData = {
                                                            ticker: stock.ticker,
                                                            name: stock.ticker,
                                                            exchange: 'NSE'
                                                        };
                                                        handleSelectStock(stockData);
                                                        handleAnalyze(stockData);
                                                    }}
                                                    className="w-full p-2.5 pr-10 rounded-lg bg-slate-800/30 border border-slate-700/50 hover:bg-slate-800/60 hover:border-blue-500/50 transition-all text-left"
                                                >
                                                    <div className="flex justify-between items-center gap-2">
                                                        <div className="flex-1 min-w-0">
                                                            <div className="font-semibold text-white text-sm">{stock.ticker}</div>
                                                            <div className="text-xs text-slate-500">₹{stock.price.toFixed(2)}</div>
                                                        </div>
                                                        <div className={`text-xs font-semibold whitespace-nowrap ${stock.change > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                                                            {stock.change > 0 ? '+' : ''}{stock.change.toFixed(2)}%
                                                        </div>
                                                    </div>
                                                </button>

                                                {/* Hover star button */}
                                                <button
                                                    onClick={(e) => toggleWatchlist(stock.ticker, stock.ticker, 'NSE', e)}
                                                    className={`absolute right-1.5 top-1/2 -translate-y-1/2 p-1.5 rounded-lg transition-all opacity-0 group-hover:opacity-100 bg-slate-800/80 backdrop-blur-sm ${inWatchlist
                                                        ? 'text-cyan-400 hover:text-cyan-300'
                                                        : 'text-slate-400 hover:text-cyan-400'
                                                        }`}
                                                    title={inWatchlist ? 'Remove from watchlist' : 'Add to watchlist'}
                                                >
                                                    {inWatchlist ? (
                                                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" strokeWidth="2">
                                                            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
                                                        </svg>
                                                    ) : (
                                                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                                            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
                                                        </svg>
                                                    )}
                                                </button>
                                            </div>
                                        );
                                    })}
                                </div>
                            )}
                        </motion.div>

                        {/* Fun Trivia */}
                        <motion.div
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: 0.1 }}
                            className="bg-slate-900/50 backdrop-blur-xl border border-slate-800/50 rounded-2xl p-5"
                        >
                            <div className="flex items-center gap-2 mb-4">
                                <div className="p-2 rounded-lg bg-purple-500/10">
                                    <Lightbulb className="w-4 h-4 text-purple-400" />
                                </div>
                                <h3 className="text-base font-semibold text-white">Did You Know?</h3>
                            </div>
                            <div className="space-y-2">
                                {funTrivia.map((fact, index) => (
                                    <div key={index} className="p-2.5 rounded-lg bg-slate-800/30 border border-slate-700/50">
                                        <p className="text-xs text-slate-300">{fact.icon} {fact.text}</p>
                                    </div>
                                ))}
                            </div>
                        </motion.div>
                    </div >
                </div >

                {/* Disclaimer */}
                < div className="text-center mt-8" >
                    <p className="text-sm text-slate-600">
                        Disclaimer: This is for educational purposes only. Not financial advice.
                    </p>
                </div >
            </div >
        </div >
    );
}
