'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuthStore } from '@/store/authStore';
import { useThemeStore } from '@/store/themeStore';
import deviceFingerprintService from '@/lib/fingerprint';
import { Search, TrendingUp, Info, BookOpen, ChevronRight, ChevronDown, ChevronUp, Loader, AlertCircle, X, AlertTriangle, CheckCircle } from 'lucide-react';
import apiClient from '@/lib/api';
import { generateMockChartData } from '@/utils/mockChart';
import { CandlestickChart } from './components/PlotlyChartWrapper';  // Use wrapper instead
import { SentimentBadge } from './components';
import { themeClass } from '@/lib/themeUtils';
import { NeuroVestLogo } from '@/components/NeuroVestLogo';

// Prevent static generation for this page
export const dynamic = 'force-dynamic';

interface TrendingStock {
    ticker: string;
    analysis_count: number;
    rank: number;
    price?: string;
    change?: number;
}

interface SearchResult {
    ticker: string;
    name: string;
    exchange: string;
}

export default function DemoPage() {
    const router = useRouter();
    const { isAuthenticated, guestRequestsRemaining, guestLimit, checkGuestLimit } = useAuthStore();
    const { isDarkMode, toggleTheme } = useThemeStore();
    const [country, setCountry] = useState('India');
    const [showBlockModal, setShowBlockModal] = useState(false);
    const [showProfileMenu, setShowProfileMenu] = useState(false);
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [trendingStocks, setTrendingStocks] = useState<TrendingStock[]>([]);
    const [realTrendingStocks, setRealTrendingStocks] = useState<any[]>([]); // Real Indian market trending stocks
    const [isTrendingLoading, setIsTrendingLoading] = useState(true);
    const [analysisResult, setAnalysisResult] = useState<any>(null);
    const [isStepsCollapsed, setIsStepsCollapsed] = useState(false);

    // Stock search states
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
    const [selectedStock, setSelectedStock] = useState<SearchResult | null>(null);
    const [isSearching, setIsSearching] = useState(false);
    const [showDropdown, setShowDropdown] = useState(false);
    const isSelectingStock = useRef(false);  // Prevent duplicate search when selecting

    const [analysisSteps, setAnalysisSteps] = useState<any[]>([]);
    const [progressStatus, setProgressStatus] = useState<'idle' | 'analyzing' | 'complete'>('idle');
    const [chartRange, setChartRange] = useState<string>('1d');

    useEffect(() => {
        if (isAuthenticated) {
            router.push('/dashboard');
            return;
        }

        const init = async () => {
            try {
                console.log('[INIT] 🚀 Initializing tracking...');

                // 1. Initialize device registration and session tracking
                const { deviceTokenManager } = await import('@/lib/device-token-manager');
                const { sessionManager } = await import('@/lib/session-manager');

                console.log('[INIT] 📱 Registering device with backend...');
                // Register device (gets or creates signed token)
                const deviceToken = await deviceTokenManager.getDeviceToken();
                console.log('[INIT] ✅ Device token:', deviceToken ? 'OK' : 'FAILED');

                console.log('[INIT] 🆔 Creating session ID...');
                // Initialize session
                const sessionId = sessionManager.getSessionId();
                console.log('[INIT] ✅ Session ID:', sessionId.substring(0, 16) + '...');

                console.log('[INIT] ✅ Tracking initialized successfully');

                // Fetch data
                await checkGuestLimit();
                fetchTrendingStocks();
                fetchRealTrendingStocks();
            } catch (error) {
                console.error('[INIT] ❌ Initialization failed:', error);
                // Still fetch data even if tracking fails
                fetchTrendingStocks();
                fetchRealTrendingStocks();
            }
        };

        init();
    }, [isAuthenticated, checkGuestLimit, router]);

    const fetchTrendingStocks = async () => {
        try {
            setIsTrendingLoading(true);
            const response = await apiClient.get('/stocks/trending');
            setTrendingStocks(response.data.trending_stocks || []);
        } catch (error: any) {
            // Silently handle rate limit errors - don't crash the app
            if (error.response?.status === 429) {
                console.warn('Rate limit hit for trending stocks, will retry later');
            } else {
                console.error('Failed to fetch trending stocks:', error);
            }
            // Don't throw - let the app continue working
        } finally {
            setIsTrendingLoading(false);
        }
    };

    // Fetch real Indian market trending stocks from API
    const fetchRealTrendingStocks = async () => {
        try {
            // Call local API proxy to avoid CORS issues
            const response = await fetch('/api/trending');
            const data = await response.json();

            // Parse and format the data
            if (Array.isArray(data)) {
                setRealTrendingStocks(data);
            } else if (data.finance?.result?.[0]?.quotes) {
                const formattedStocks = data.finance.result[0].quotes.slice(0, 5).map((quote: any) => ({
                    ticker: quote.symbol,
                    price: quote.regularMarketPrice || 0,
                    change: quote.regularMarketChangePercent || 0
                }));
                setRealTrendingStocks(formattedStocks);
            }
        } catch (error) {
            console.error('Failed to fetch real trending stocks:', error);
            // Fallback to empty array on error
            setRealTrendingStocks([]);
        }
    };

    // Debounced stock search
    const searchStocks = useCallback(async (query: string) => {
        if (!query || query.length < 2) {
            setSearchResults([]);
            setShowDropdown(false);
            return;
        }

        setIsSearching(true);
        try {
            const response = await apiClient.get('/stocks/search', {
                params: { q: query, country: country }
            });

            if (response.data.results) {
                setSearchResults(response.data.results);
                setShowDropdown(true);
            }
        } catch (error) {
            console.error('Stock search error:', error);
            setSearchResults([]);
        } finally {
            setIsSearching(false);
        }
    }, [country]);

    // Debounce search
    useEffect(() => {
        // Skip search if we're selecting from dropdown
        if (isSelectingStock.current) {
            isSelectingStock.current = false;
            return;
        }

        const timer = setTimeout(() => {
            searchStocks(searchQuery);
        }, 300);

        return () => clearTimeout(timer);
    }, [searchQuery, searchStocks]);

    const handleSelectStock = (stock: SearchResult) => {
        // Set flag to prevent debounced search from triggering
        isSelectingStock.current = true;

        setSelectedStock(stock);
        setSearchQuery(stock.name || stock.ticker);
        setShowDropdown(false);
        setSearchResults([]);
    };

    const handleClearSearch = () => {
        setSearchQuery('');
        setSelectedStock(null);
        setSearchResults([]);
        setShowDropdown(false);
        setAnalysisSteps([]);
        setProgressStatus('idle');
    };

    const handleAnalyze = async (stockOverride?: SearchResult) => {
        // REMOVED: Frontend rate limit check
        // Backend now checks cache FIRST (FREE), then rate limit
        // This allows users to access cached analyses even when at limit

        // Use override if provided (from trending click), otherwise use state
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

        try {
            // Get all tracking headers (device token + session ID)
            const { TrackingHeaders } = await import('@/lib/tracking-headers');
            const trackingHeaders = await TrackingHeaders.getHeaders();

            const response = await fetch(
                `http://localhost:8000/stocks/${stockToUse.ticker}/analysis-stream`,
                {
                    credentials: 'include',
                    headers: {
                        ...trackingHeaders,
                        'Accept': 'text/event-stream',
                    },
                }
            );

            // Backend returns 429 if TRULY at limit (cache miss + limit exceeded)
            if (response.status === 429) {
                setShowBlockModal(true);
                setIsAnalyzing(false);
                setProgressStatus('idle');
                return;
            }

            if (!response.ok) {
                throw new Error(
                    `HTTP ${response.status}: ${response.statusText}`);
            }

            const reader = response.body?.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            let finalData: any = null;
            let isCached = false;

            while (true) {
                const { done, value } = await reader!.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';

                for (const line of lines) {
                    if (!line.trim() || !line.startsWith('data: ')) continue;

                    try {
                        const data = JSON.parse(line.slice(6));

                        if (data.type === 'step') {
                            // Parse step data - backend sends 'text' field
                            const stepText = data.step.text || data.step.description || '';
                            // Check if cached
                            if (stepText.toLowerCase().includes('cache')) {
                                isCached = true;
                            }
                            // Store step with proper text field
                            setAnalysisSteps(prev => [...prev, {
                                ...data.step,
                                text: stepText
                            }]);
                        } else if (data.type === 'final') {
                            finalData = data.analysis;
                            // Don't setAnalysisResult here - will do after loop with transformation
                            setProgressStatus('complete');
                        } else if (data.type === 'error') {
                            console.error('Analysis error:', data);
                            setProgressStatus('idle');
                        }
                    } catch (error) {
                        console.error('Failed to parse SSE data:', error);
                    }
                }
            }

            // After SSE loop, transform and set analysis result
            if (finalData) {
                // Transform backend response to match our UI structure
                const sentiment = finalData.sentiment || {};
                const techAnalysis = finalData.technical_analysis || {};
                const indicators = techAnalysis.indicators || {};

                setAnalysisResult({
                    ticker: finalData.ticker,
                    price: finalData.current_price || 0,
                    change: 0,
                    sentiment: sentiment.classification || 'Neutral',
                    confidence: (sentiment.average_confidence || sentiment.confidence || 0) * 100,

                    // Technical indicators
                    rsi: indicators.rsi?.value || 0,
                    macd: indicators.macd?.macd || 0,
                    macdSignal: indicators.macd?.signal || 0,
                    macdHist: indicators.macd?.histogram || 0,
                    bollingerUpper: indicators.bollinger_bands?.upper || 0,
                    bollingerMiddle: indicators.bollinger_bands?.middle || 0,
                    bollingerLower: indicators.bollinger_bands?.lower || 0,

                    // AI Analysis
                    aiAnalysis: finalData.analysis || '',

                    // Insights
                    insights: finalData.key_insights || [],

                    // Future outlook and risks
                    futureOutlook: finalData.prediction || finalData.future_outlook || 'No prediction available',
                    risks: finalData.risk_factors || [],

                    // References
                    references: finalData.references || [],

                    // Day range
                    dayLow: finalData.day_low || 0,
                    dayHigh: finalData.day_high || 0,
                    currency: finalData.currency || 'INR',

                    // Historical data
                    historicalDataMulti: finalData.historical_data_multi || {},
                    // Cache info
                    cached: isCached
                });
            }
            // Success - update remaining count and refresh trending stocks

            // ALWAYS refresh guest limit after analysis (backend handles increment correctly)
            await checkGuestLimit();

            // CRITICAL: Refresh trending stocks after analysis
            fetchTrendingStocks();

        } catch (error: any) {
            console.error('Analysis failed:', error);
            setProgressStatus('idle');
            if (error.message?.includes('429')) {
                setShowBlockModal(true);
            }
        } finally {
            setIsAnalyzing(false);
        }
    };

    const handleReset = () => {
        setAnalysisResult(null);
        setSearchQuery('');
        setSelectedStock(null);
        setSearchResults([]);
    };

    return (
        <div className={`min-h-screen relative overflow-hidden transition-colors duration-300 ${isDarkMode ? 'bg-[#0a0e14] text-gray-100' : 'bg-gray-50 text-gray-900'}`}>
            {/* Animated Background */}
            <div className="fixed inset-0 z-0">
                <div className="absolute inset-0 bg-[linear-gradient(rgba(6,182,212,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(6,182,212,0.03)_1px,transparent_1px)] bg-[size:50px_50px] [mask-image:radial-gradient(ellipse_at_center,black_50%,transparent_100%)]" />

                <motion.div
                    animate={{ y: [0, -30, 0], x: [0, 20, 0], scale: [1, 1.1, 1] }}
                    transition={{ duration: 15, repeat: Infinity, ease: 'easeInOut' }}
                    className="absolute top-1/4 left-1/4 w-96 h-96 bg-teal-500/5 rounded-full blur-3xl"
                />
                <motion.div
                    animate={{ y: [0, 30, 0], x: [0, -20, 0], scale: [1, 1.2, 1] }}
                    transition={{ duration: 20, repeat: Infinity, ease: 'easeInOut' }}
                    className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl"
                />

                <motion.div
                    animate={{ y: ['0%', '100%'] }}
                    transition={{ duration: 8, repeat: Infinity, ease: 'linear' }}
                    className="absolute inset-x-0 h-px bg-gradient-to-r from-transparent via-teal-500/20 to-transparent"
                />
            </div>

            {/* Content */}
            <div className="relative z-10">
                {/* Header */}
                <motion.div
                    initial={{ y: -50, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}

                    transition={{ duration: 0.5 }}
                >
                    <header className={`border-b sticky top-0 z-50 backdrop-blur-sm transition-colors ${isDarkMode ? 'border-gray-800 bg-[#0c1015]/80' : 'border-gray-200 bg-white/80'}`}>
                        <div className={`max-w-7xl mx-auto px-6 py-4 flex justify-between items-center ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                            <Link href="/" className="flex items-center gap-1 select-none hover:opacity-80 transition-opacity">
                                <span className={`text-2xl font-bold tracking-wider font-sans bg-clip-text text-transparent bg-gradient-to-r from-teal-400 to-purple-500`}>NEUR</span>
                                <NeuroVestLogo className="h-8 w-8" />
                                <span className={`text-2xl font-bold tracking-wider font-sans bg-clip-text text-transparent bg-gradient-to-r from-purple-500 to-teal-400`}>VEST</span>
                            </Link>
                            <div className={`flex items-center gap-4 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                                <span className="text-sm text-gray-400">Guest Mode</span>
                                <span className="text-emerald-400 text-sm font-medium">{guestRequestsRemaining}/{guestLimit || 2} Free Analyses Remaining</span>

                                {/* Profile Dropdown Menu */}
                                <div className="relative">
                                    <button
                                        onClick={() => setShowProfileMenu(!showProfileMenu)}
                                        className="p-2 rounded-full hover:bg-gray-800 transition-colors"
                                    >
                                        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                                        </svg>
                                    </button>

                                    {/* Dropdown Menu */}
                                    {showProfileMenu && (
                                        <motion.div
                                            initial={{ opacity: 0, y: -10 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            className={`absolute right-0 mt-2 w-48 rounded-lg shadow-xl overflow-hidden z-50 ${isDarkMode ? 'bg-[#1a1d24] border border-gray-700' : 'bg-white border border-gray-200'}`}
                                        >
                                            <button
                                                onClick={toggleTheme}
                                                className={`w-full px-4 py-3 text-left transition-colors flex items-center gap-2 ${isDarkMode ? 'text-gray-300 hover:bg-gray-800' : 'text-gray-700 hover:bg-gray-100'}`}
                                            >
                                                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={isDarkMode ? "M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" : "M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"} />
                                                </svg>
                                                {isDarkMode ? 'Switch to Light' : 'Switch to Dark'}
                                            </button>
                                            <div className={`border-t ${isDarkMode ? 'border-gray-700' : 'border-gray-200'}`}></div>
                                            <button
                                                onClick={() => router.push('/auth/login')}
                                                className="w-full px-4 py-3 text-left text-teal-400 hover:bg-gray-800 transition-colors flex items-center gap-2"
                                            >
                                                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
                                                </svg>
                                                Login
                                            </button>
                                            <button
                                                onClick={() => router.push('/auth/signup')}
                                                className="w-full px-4 py-3 text-left text-teal-400 hover:bg-gray-800 transition-colors flex items-center gap-2"
                                            >
                                                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
                                                </svg>
                                                Sign Up
                                            </button>
                                        </motion.div>
                                    )}
                                </div>
                            </div>
                        </div>
                    </header>
                </motion.div>

                <div className="flex justify-center max-w-[1800px] mx-auto">
                    {/* Left Sidebar - Reorganized */}
                    <motion.aside
                        initial={{ x: -300 }}
                        animate={{ x: 0 }}
                        className={`w-96 border-r min-h-screen p-6 space-y-6 transition-colors ${isDarkMode ? 'bg-[#0d1117] border-gray-800' : 'bg-white border-gray-200'}`}
                    >
                        {/* 1. Settings + Country Selector */}
                        <div>
                            <h3 className={`text-sm font-semibold mb-4 flex items-center gap-2 ${isDarkMode ? 'text-gray-400' : 'text-gray-700'}`}>
                                <div className="w-1 h-4 bg-teal-400 rounded" />
                                Settings
                            </h3>
                            <div className="mb-4">
                                <label className={`text-sm mb-2 block ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>Select Region</label>
                                <select
                                    value={country}
                                    onChange={(e) => setCountry(e.target.value)}
                                    className={`w-full rounded-lg px-4 py-2.5 focus:border-teal-500 focus:outline-none transition-colors ${isDarkMode ? 'bg-[#161b22] border-gray-700 text-gray-200' : 'bg-gray-50 border-gray-300 text-gray-900'} border`}
                                >
                                    <option>India</option>
                                    <option>United States</option>
                                    <option>United Kingdom</option>
                                </select>
                            </div>
                        </div>

                        {/* 2. Trending in NeuroVest (moved here) */}
                        <div>
                            <h3 className={`text-sm font-semibold mb-4 flex items-center gap-2 ${isDarkMode ? 'text-gray-400' : 'text-gray-700'}`}>
                                <TrendingUp className="text-teal-400" size={16} />
                                Trending in NeuroVest
                            </h3>
                            {isTrendingLoading ? (
                                <p className={`text-sm ${isDarkMode ? 'text-gray-500' : 'text-gray-400'}`}>Loading trending stocks...</p>
                            ) : trendingStocks.length === 0 ? (
                                <p className={`text-sm ${isDarkMode ? 'text-gray-500' : 'text-gray-400'}`}>No trending stocks available</p>
                            ) : (
                                <div className="flex flex-col gap-2">
                                    {trendingStocks.slice(0, 5).map((stock, i) => (
                                        <motion.button
                                            key={stock.ticker}
                                            onClick={() => {
                                                // Convert trending stock to SearchResult format
                                                const stockToAnalyze: SearchResult = {
                                                    ticker: stock.ticker,
                                                    name: stock.ticker,
                                                    exchange: 'NSE'
                                                };
                                                handleSelectStock(stockToAnalyze);
                                                // Pass stock directly to avoid race condition
                                                handleAnalyze(stockToAnalyze);
                                            }}
                                            whileHover={{ scale: 1.02 }}
                                            whileTap={{ scale: 0.98 }}
                                            className={`p-3 rounded-lg border transition-all cursor-pointer text-left ${isDarkMode
                                                ? 'bg-[#161b22] border-gray-700 hover:border-teal-500/50 hover:bg-[#1c2128]'
                                                : 'bg-gray-50 border-gray-200 hover:border-teal-500/50 hover:bg-gray-100'
                                                } backdrop-blur-sm`}
                                        >
                                            <div className="flex items-center justify-between gap-4">
                                                <div>
                                                    <div className={`font-medium text-sm ${isDarkMode ? 'text-gray-200' : 'text-gray-900'}`}>{stock.ticker}</div>
                                                    <div className={`text-xs ${isDarkMode ? 'text-gray-500' : 'text-gray-500'}`}>#{stock.rank} • {stock.analysis_count}× analyzed</div>
                                                </div>
                                                {stock.change !== undefined && (
                                                    <div className={`text-sm font-semibold ${stock.change > 0 ? 'text-teal-400' : 'text-red-400'}`}>
                                                        {stock.change > 0 ? '+' : ''}{stock.change.toFixed(2)}%
                                                    </div>
                                                )}
                                            </div>
                                        </motion.button>
                                    ))}
                                </div>
                            )}
                        </div>

                        {/* 3. Indian Market Facts */}
                        <div className={`pt-6 border-t ${isDarkMode ? 'border-gray-800' : 'border-gray-200'}`}>
                            <h3 className={`text-sm font-semibold mb-4 flex items-center gap-2 ${isDarkMode ? 'text-gray-400' : 'text-gray-700'}`}>
                                <BookOpen size={16} className="text-teal-400" />
                                Indian Market Facts
                            </h3>
                            <div className="space-y-3">
                                <div className={`p-3 rounded-lg border ${isDarkMode ? 'bg-[#161b22] border-gray-800' : 'bg-gray-50 border-gray-200'}`}>
                                    <p className={`text-xs font-semibold mb-1 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>📅 Trading Hours</p>
                                    <p className={`text-xs ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>9:15 AM - 3:30 PM IST</p>
                                </div>
                                <div className={`p-3 rounded-lg border ${isDarkMode ? 'bg-[#161b22] border-gray-800' : 'bg-gray-50 border-gray-200'}`}>
                                    <p className={`text-xs font-semibold mb-1 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>📊 Indices</p>
                                    <p className={`text-xs ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>NIFTY 50, SENSEX</p>
                                </div>
                            </div>
                        </div>

                        {/* 4. Did You Know */}
                        <div className={`pt-6 border-t ${isDarkMode ? 'border-gray-800' : 'border-gray-200'}`}>
                            <h3 className={`text-sm font-semibold mb-4 flex items-center gap-2 ${isDarkMode ? 'text-gray-400' : 'text-gray-700'}`}>
                                <span className="text-teal-400">💡</span>
                                Did You Know?
                            </h3>
                            <div className="space-y-3">
                                <div className={`p-3 rounded-lg border ${isDarkMode ? 'bg-[#161b22] border-gray-800' : 'bg-gray-50 border-gray-200'}`}>
                                    <p className={`text-xs ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                                        NSE: World's largest derivatives exchange by contract volume
                                    </p>
                                </div>
                                <div className={`p-3 rounded-lg border ${isDarkMode ? 'bg-[#161b22] border-gray-800' : 'bg-gray-50 border-gray-200'}`}>
                                    <p className={`text-xs ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                                        BSE (1875): Asia's oldest stock exchange
                                    </p>
                                </div>
                            </div>
                        </div>

                    </motion.aside>

                    {/* Main Content */}
                    <main className="flex-1 p-8">
                        <div className="max-w-4xl mx-auto">

                            {/* IF ANALYZING OR RESULT, SHOW DIFFERENT HEADER/CONTENT */}

                            {!analysisResult && !isAnalyzing && (
                                <>
                                    {/* Hero */}
                                    <motion.div
                                        initial={{ opacity: 0, y: 20 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        className="text-center mb-12"
                                    >
                                        <h1 className="text-3xl font-bold mb-4 bg-gradient-to-r from-teal-400 to-cyan-400 bg-clip-text text-transparent">
                                            AI-Powered Stock Analysis & Prediction
                                        </h1>
                                        <p className="text-gray-400 text-lg">
                                            2 complimentary analyses • No credit card required
                                        </p>
                                    </motion.div>

                                    {/* Stock Analysis Search Card */}
                                    <motion.div
                                        initial={{ opacity: 0, y: 20 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        transition={{ delay: 0.2 }}
                                        className={`border rounded-2xl p-8 mb-8 ${isDarkMode ? 'bg-[#0d1117] border-gray-800' : 'bg-white border-gray-200'}`}
                                    >

                                        <div className="mb-6 relative">
                                            <div className="relative">
                                                <input
                                                    type="text"
                                                    value={searchQuery}
                                                    onChange={(e) => setSearchQuery(e.target.value)}
                                                    onFocus={() => searchResults.length > 0 && setShowDropdown(true)}
                                                    placeholder="Type to search (e.g., Apple, Reliance)..."
                                                    className="w-full bg-[#161b22] border border-gray-700 rounded-lg px-5 py-4 pr-20 text-gray-200 placeholder-gray-500 focus:border-teal-500 focus:outline-none transition-colors"
                                                    disabled={isAnalyzing}
                                                />
                                                <div className="absolute right-4 top-1/2 -translate-y-1/2 flex items-center gap-2">
                                                    {isSearching && <Loader className="animate-spin text-teal-400" size={20} />}
                                                    {searchQuery && !isSearching && (
                                                        <button onClick={handleClearSearch} className="text-gray-400 hover:text-white">
                                                            <X size={20} />
                                                        </button>
                                                    )}
                                                    <Search className="text-gray-400" size={20} />
                                                </div>

                                                {/* Dropdown Results */}
                                                <AnimatePresence>
                                                    {showDropdown && searchResults.length > 0 && (
                                                        <motion.div
                                                            initial={{ opacity: 0, y: -10 }}
                                                            animate={{ opacity: 1, y: 0 }}
                                                            exit={{ opacity: 0, y: -10 }}
                                                            className="absolute top-full left-0 right-0 mt-2 bg-[#161b22] border border-gray-700 rounded-lg shadow-2xl max-h-80 overflow-y-auto z-50"
                                                        >
                                                            {searchResults.map((result, index) => (
                                                                <motion.button
                                                                    key={`${result.ticker}-${index}`}
                                                                    whileHover={{ backgroundColor: 'rgba(20, 184, 166, 0.1)' }}
                                                                    onClick={() => handleSelectStock(result)}
                                                                    className="w-full text-left px-5 py-3 border-b border-gray-800 last:border-0 transition-colors"
                                                                >
                                                                    <div className="flex justify-between items-center">
                                                                        <div>
                                                                            <div className="text-white font-semibold">{result.ticker}</div>
                                                                            <div className="text-gray-400 text-sm">{result.name}</div>
                                                                        </div>
                                                                        <div className="text-teal-400 text-xs">{result.exchange}</div>
                                                                    </div>
                                                                </motion.button>
                                                            ))}
                                                        </motion.div>
                                                    )}
                                                </AnimatePresence>
                                            </div>

                                            {/* Selected Stock Display */}
                                            {selectedStock && (
                                                <motion.div
                                                    initial={{ opacity: 0 }}
                                                    animate={{ opacity: 1 }}
                                                    className="mt-3 px-4 py-2 bg-teal-500/10 border border-teal-500/30 rounded-lg"
                                                >
                                                    <div className="flex items-center justify-between">
                                                        <div>
                                                            <span className="text-teal-400 font-semibold">Selected: </span>
                                                            <span className="text-white">{selectedStock.ticker} - {selectedStock.name}</span>
                                                        </div>
                                                        <button onClick={handleClearSearch} className="text-gray-400 hover:text-white">
                                                            <X size={18} />
                                                        </button>
                                                    </div>
                                                </motion.div>
                                            )}
                                        </div>

                                        <button
                                            onClick={() => handleAnalyze()}
                                            disabled={!selectedStock}
                                            data-analyze-btn="true"
                                            className="w-full bg-gradient-to-r from-teal-500 to-cyan-500 text-white h-10 px-4 rounded-lg font-medium text-sm hover:shadow-lg hover:shadow-teal-500/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                                        >
                                            Analyze Stock
                                            <ChevronRight size={18} />
                                        </button>
                                    </motion.div>

                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                        <QuickInfoCard isDarkMode={isDarkMode} />
                                        <WhyChooseCard isDarkMode={isDarkMode} />
                                    </div>
                                </>
                            )}

                            {/* RESULT STATE - Shows both analyzing and complete states */}
                            {(progressStatus === 'analyzing' || (progressStatus === 'complete' && analysisResult)) && (
                                <motion.div
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                >
                                    {/* Progress Panel */}
                                    <div className="mb-8">
                                        <div className="bg-[#0d1117] border border-gray-800 rounded-2xl p-6">
                                            <div className="flex items-center justify-between mb-4">
                                                <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                                                    {progressStatus === 'complete' ? (
                                                        <><CheckCircle className="text-teal-400" size={20} /> Analysis complete for {selectedStock?.ticker}</>
                                                    ) : (
                                                        <><Loader className="animate-spin text-teal-400" size={20} /> Analyzing {selectedStock?.ticker}...</>
                                                    )}
                                                </h3>
                                                <button
                                                    onClick={() => setIsStepsCollapsed(!isStepsCollapsed)}
                                                    className="p-1 hover:bg-gray-800 rounded-lg transition-colors text-gray-400 hover:text-white"
                                                >
                                                    {isStepsCollapsed ? <ChevronDown size={20} /> : <ChevronUp size={20} />}
                                                </button>
                                            </div>

                                            {!isStepsCollapsed && (
                                                <div className="space-y-3 pl-2">
                                                    {analysisSteps.map((step, i) => (
                                                        <motion.div
                                                            key={i}
                                                            initial={{ opacity: 0, x: -20 }}
                                                            animate={{ opacity: 1, x: 0 }}
                                                            transition={{ delay: i * 0.1 }}
                                                            className={`p-3 rounded-lg border ${isDarkMode ? 'bg-gray-800/50 border-gray-700' : 'bg-gray-50 border-gray-200'}`}
                                                        >
                                                            <div className="flex items-start justify-between gap-2">
                                                                <span className="text-sm flex-1">{step.text || step.description || 'Processing...'}</span>
                                                                <span className="text-green-500 font-mono text-xs ml-auto whitespace-nowrap">
                                                                    {new Date(step.timestamp).toLocaleTimeString('en-US', { hour12: false })}
                                                                    {step.timeTaken && ` (${parseFloat(step.timeTaken).toFixed(2)}s)`}
                                                                </span>
                                                            </div>
                                                        </motion.div>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    </div>

                                    {/* Cache Warning */}
                                    {analysisResult?.cached && (
                                        <div className="mb-6 p-4 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
                                            <p className="text-yellow-500 text-sm">⚡ Fetched from cache - Fresh analysis available in less than 1 hour</p>
                                        </div>
                                    )}

                                    {/* Results Content - Only show when complete */}
                                    {progressStatus === 'complete' && analysisResult && (
                                        <>
                                            {/* Header */}
                                            <div className="flex items-center justify-between mb-8">
                                                <h2 className="text-2xl font-bold text-white">AI Analysis Results</h2>
                                                <button
                                                    onClick={handleReset}
                                                    className="px-4 py-2 rounded-lg bg-[#1c2128] border border-gray-700 text-sm text-gray-300 hover:text-white hover:border-teal-500 transition-colors"
                                                >
                                                    New Search
                                                </button>
                                            </div>

                                            {/* TOP ROW: Key Metrics (Left) + Price Charts (Right) */}
                                            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-10">
                                                {/* Key Metrics - Left Column */}
                                                <div className="lg:col-span-1 space-y-6">
                                                    <div>
                                                        <div className="flex items-center gap-2 mb-4">
                                                            <div className="w-1 h-6 bg-teal-400 rounded" />
                                                            <h3 className="text-xl font-semibold text-white">Key Metrics</h3>
                                                        </div>

                                                        <div className="bg-[#0d1117] p-6 rounded-xl border border-gray-800 h-full">
                                                            {/* Current Price */}
                                                            <div className="mb-2 text-sm text-gray-400 font-semibold">💰 Current Price</div>
                                                            <div className="text-4xl font-bold text-white mb-6">{analysisResult.currency || 'INR'} {(analysisResult.price || 0).toFixed(2)}</div>

                                                            {/* Sentiment Badge */}
                                                            <div className="mb-6">
                                                                <SentimentBadge sentiment={analysisResult.sentiment} />
                                                            </div>

                                                            {/* Confidence Score */}
                                                            <div>
                                                                <div className="flex items-center gap-2 mb-2">
                                                                    <div className="w-2 h-2 rounded-full bg-teal-400 animate-pulse" />
                                                                    <span className="text-gray-300 text-sm font-semibold">🎯 Confidence Score</span>
                                                                </div>
                                                                <div className="text-3xl font-bold text-white">{(analysisResult.confidence || 0).toFixed(2)}%</div>
                                                                <div className="w-full h-2 bg-gray-800 rounded-full mt-3 overflow-hidden">
                                                                    <div
                                                                        className="h-full bg-gradient-to-r from-teal-500 to-cyan-500 transition-all duration-500"
                                                                        style={{ width: `${analysisResult.confidence}%` }}
                                                                    />
                                                                </div>
                                                            </div>

                                                            {/* Day Range */}
                                                            <div className="mt-6 pt-6 border-t border-gray-800">
                                                                <div className="text-sm text-gray-400 font-semibold mb-2">Day Range</div>
                                                                <div className="text-lg font-semibold text-white">
                                                                    {analysisResult.currency || 'INR'} {(analysisResult.dayLow || 0).toFixed(2)} - {analysisResult.currency || 'INR'} {(analysisResult.dayHigh || 0).toFixed(2)}
                                                                </div>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>

                                                {/* Price Charts - Right Column (2/3 width) */}
                                                <div className="lg:col-span-2">
                                                    <div className="flex items-center gap-2 mb-6">
                                                        <div className="w-1 h-6 bg-teal-400 rounded" />
                                                        <h3 className="text-xl font-semibold text-white">📈 Price Charts</h3>
                                                    </div>
                                                    <div className="bg-[#0d1117] p-6 rounded-xl border border-gray-800 h-full">
                                                        {/* Chart Range Selector */}
                                                        <div className="flex gap-2 mb-6 border-b border-gray-800 pb-4">
                                                            {[
                                                                { label: '1 Day', value: '1d' },
                                                                { label: '5 Days', value: '5d' },
                                                                { label: '1 Month', value: '1mo' },
                                                                { label: '3 Months', value: '3mo' },
                                                                { label: '1 Year', value: '1y' }
                                                            ].map(({ label, value }) => (
                                                                <button
                                                                    key={value}
                                                                    onClick={() => setChartRange(value)}
                                                                    className={`text-sm px-3 py-1.5 rounded-lg transition-colors ${chartRange === value
                                                                        ? 'bg-teal-500/10 text-teal-400 border border-teal-500/20 font-semibold'
                                                                        : 'text-gray-400 hover:text-white hover:bg-gray-800'
                                                                        }`}
                                                                >
                                                                    {label}
                                                                </button>
                                                            ))}
                                                        </div>

                                                        {/* Chart Component */}
                                                        {analysisResult.historicalDataMulti ? (
                                                            <CandlestickChart
                                                                data={analysisResult.historicalDataMulti}
                                                                range={chartRange}
                                                                ticker={analysisResult.ticker}
                                                            />
                                                        ) : (
                                                            <div className="h-[300px] flex items-center justify-center text-gray-500">
                                                                <span>No chart data available</span>
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Technical Indicators */}
                                            <div className="mb-10">
                                                <div className="flex items-center gap-2 mb-6">
                                                    <div className="w-1 h-6 bg-teal-400 rounded" />
                                                    <h3 className="text-xl font-semibold text-white">📊 Technical Indicators</h3>
                                                </div>

                                                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                                    {/* RSI */}
                                                    <div className="bg-[#0d1117] p-6 rounded-xl border border-gray-800">
                                                        <div className="flex items-center gap-2 mb-2">
                                                            <span className="text-xs font-semibold text-teal-400 bg-teal-400/10 px-2 py-0.5 rounded">📉 RSI (14)</span>
                                                        </div>
                                                        <div className="text-4xl font-bold text-white mb-2">{analysisResult.rsi}</div>
                                                        <div className="text-sm text-gray-400 flex items-center gap-1">
                                                            <span className="text-yellow-400">🟡 Neutral</span>
                                                        </div>
                                                        <div className="w-full h-1.5 bg-gray-800 rounded-full mt-4 overflow-hidden">
                                                            <div className="h-full bg-blue-500" style={{ width: `${Math.min((analysisResult.rsi / 100) * 100, 100)}%` }} />
                                                        </div>
                                                    </div>

                                                    {/* MACD */}
                                                    <div className="bg-[#0d1117] p-6 rounded-xl border border-gray-800">
                                                        <div className="flex items-center gap-2 mb-2">
                                                            <span className="text-xs font-semibold text-purple-400 bg-purple-400/10 px-2 py-0.5 rounded">📈 MACD</span>
                                                        </div>
                                                        <div className="text-4xl font-bold text-white mb-2">{(analysisResult.macd || 0).toFixed(2)}</div>
                                                        <div className="text-sm text-gray-400 flex items-center gap-1">
                                                            <span className="text-green-400">↑ Bearish</span>
                                                        </div>
                                                        <div className="text-xs text-gray-500 mt-1">Signal: {(analysisResult.macdSignal || 0).toFixed(2)}</div>
                                                        <div className="text-xs text-gray-500">Histogram: {(analysisResult.macdHist || 0).toFixed(2)}</div>
                                                    </div>

                                                    {/* Bollinger Bands */}
                                                    <div className="bg-[#0d1117] p-6 rounded-xl border border-gray-800">
                                                        <div className="flex items-center gap-2 mb-2">
                                                            <span className="text-xs font-semibold text-blue-400 bg-blue-400/10 px-2 py-0.5 rounded">📊 Bollinger Bands</span>
                                                        </div>
                                                        <div className="text-sm text-red-400 font-semibold mb-3">Position: Below Middle (Bearish Zone)</div>
                                                        <div className="space-y-2">
                                                            <div className="flex justify-between text-sm">
                                                                <span className="text-gray-500">Upper:</span>
                                                                <span className="text-gray-300 font-mono">{(analysisResult.bollingerUpper || 0).toFixed(2)}</span>
                                                            </div>
                                                            <div className="flex justify-between text-sm">
                                                                <span className="text-gray-500">Middle:</span>
                                                                <span className="text-gray-300 font-mono">{(analysisResult.bollingerMiddle || 0).toFixed(2)}</span>
                                                            </div>
                                                            <div className="flex justify-between text-sm">
                                                                <span className="text-gray-500">Lower:</span>
                                                                <span className="text-gray-300 font-mono">{(analysisResult.bollingerLower || 0).toFixed(2)}</span>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                            {/* AI Analysis */}
                                            <div className="mb-10">
                                                <div className="flex items-center gap-2 mb-6">
                                                    <div className="w-1 h-6 bg-teal-400 rounded" />
                                                    <h3 className="text-xl font-semibold text-white">🤖 AI Analysis</h3>
                                                </div>
                                                <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 border border-gray-700 p-6 rounded-xl">
                                                    <p className="text-gray-300 leading-relaxed text-base whitespace-pre-wrap">
                                                        {analysisResult.aiAnalysis || 'No analysis available'}
                                                    </p>
                                                </div>
                                            </div>

                                            {/* Disclaimer - shown once after AI Analysis */}
                                            <div className="mb-10 p-4 bg-yellow-500/10 border border-yellow-500/20 rounded-lg flex gap-3">
                                                <AlertTriangle className="text-yellow-500 shrink-0 mt-0.5" size={20} />
                                                <div>
                                                    <h4 className="text-yellow-500 font-semibold text-sm mb-1">⚠️ IMPORTANT DISCLAIMER</h4>
                                                    <p className="text-yellow-500/80 text-xs">
                                                        This analysis is provided for informational and educational purposes only. It does not constitute financial advice, investment recommendations, or an offer to buy or sell any securities.
                                                    </p>
                                                    <div className="mt-3 space-y-1 text-xs text-yellow-500/70">
                                                        <p>• This is AI-generated analysis based on publicly available information</p>
                                                        <p>• Past performance does not guarantee future results</p>
                                                        <p>• Market data and sentiment can change rapidly</p>
                                                        <p>• Always conduct your own research and consult with a qualified financial advisor</p>
                                                        <p>• Investment decisions should be based on your individual financial situation, goals, and risk tolerance</p>
                                                    </div>
                                                </div>
                                            </div>

                                            <div className="mb-10">
                                                <div className="flex items-center gap-2 mb-6">
                                                    <div className="w-1 h-6 bg-teal-400 rounded" />
                                                    <h3 className="text-xl font-semibold text-white">Recent Trends & Key Insights</h3>
                                                </div>
                                                <div className="space-y-3">
                                                    {(analysisResult.insights || []).map((insight: string, idx: number) => (
                                                        <div key={idx} className={`p-4 rounded-lg flex gap-3 items-start ${idx === 3 ? 'bg-red-500/10 border border-red-500/20' : 'bg-blue-500/10 border border-blue-500/20'}`}>
                                                            <Info className={`shrink-0 w-5 h-5 mt-0.5 ${idx === 3 ? 'text-red-400' : 'text-blue-400'}`} />
                                                            <p className="text-gray-200 text-sm">{insight}</p>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>

                                            {/* Future Outlook */}
                                            <div className="mb-10">
                                                <div className="flex items-center gap-2 mb-6">
                                                    <div className="w-1 h-6 bg-teal-400 rounded" />
                                                    <h3 className="text-xl font-semibold text-white">Future Outlook & Prediction</h3>
                                                </div>
                                                <div className="bg-blue-900/20 border border-blue-500/30 p-6 rounded-xl">
                                                    <p className="text-blue-100 leading-relaxed text-sm">
                                                        {analysisResult.futureOutlook}
                                                    </p>
                                                </div>
                                            </div>

                                            {/* Risk Factors */}
                                            <div className="mb-10">
                                                <div className="flex items-center gap-2 mb-6">
                                                    <AlertTriangle className="text-yellow-500" />
                                                    <h3 className="text-xl font-semibold text-white">Risk Factors</h3>
                                                </div>
                                                <ul className="space-y-3 pl-4">
                                                    {(analysisResult.risks || []).map((risk: string, idx: number) => (
                                                        <li key={idx} className="text-gray-300 text-sm list-disc pl-2 marker:text-yellow-500">
                                                            {risk}
                                                        </li>
                                                    ))}
                                                </ul>
                                            </div>

                                            {/* References */}
                                            <div className="mb-10">
                                                <div className="flex items-center gap-2 mb-4">
                                                    <div className="w-1 h-6 bg-teal-400 rounded" />
                                                    <h3 className="text-xl font-semibold text-white">References ({(analysisResult.references || []).length})</h3>
                                                </div>
                                                <div className="space-y-2">
                                                    {(analysisResult.references || []).map((ref: any, idx: number) => (
                                                        <div key={idx} className="flex items-center gap-2">
                                                            <span className="text-gray-500 text-sm">{idx + 1}.</span>
                                                            <a
                                                                href={ref.url || '#'}
                                                                target="_blank"
                                                                rel="noopener noreferrer"
                                                                className="text-blue-400 hover:underline text-sm truncate"
                                                            >
                                                                {ref.source || ref.ticker || 'Reference'}
                                                            </a>
                                                            {ref.timestamp && (
                                                                <span className="text-gray-600 text-xs">({new Date(ref.timestamp).toLocaleDateString()})</span>
                                                            )}
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>

                                            {/* Footer / Login Prompt */}
                                            <div className="mt-12 pt-8 border-t border-gray-800 text-center">
                                                <p className="text-gray-400 mb-4">
                                                    Want more analyses and documentation access?
                                                </p>
                                                <div className="flex justify-center gap-4">
                                                    <button
                                                        onClick={() => router.push('/auth/login')}
                                                        className="text-teal-400 hover:text-teal-300 font-medium hover:underline"
                                                    >
                                                        Login
                                                    </button>
                                                    <span className="text-gray-600">or</span>
                                                    <button
                                                        onClick={() => router.push('/auth/signup')}
                                                        className="text-teal-400 hover:text-teal-300 font-medium hover:underline"
                                                    >
                                                        Sign Up
                                                    </button>
                                                </div>
                                            </div>
                                        </>
                                    )}
                                </motion.div>
                            )}
                        </div>

                        <div className="mt-4 pt-4 border-t border-gray-800/50 text-center">
                            <p className={`text-xs italic ${isDarkMode ? 'text-gray-600' : 'text-gray-400'}`}>
                                Disclaimer: This is for educational purposes only. Not financial advice.
                            </p>
                        </div>
                    </main>

                    {/* Right Sidebar - Real Trending Stocks in India */}
                    <motion.aside
                        initial={{ x: 300 }}
                        animate={{ x: 0 }}
                        className={`w-96 border-l min-h-screen p-6 space-y-6 overflow-y-auto transition-colors ${isDarkMode ? 'bg-[#0d1117] border-gray-800' : 'bg-white border-gray-200'}`}
                    >
                        <div>
                            <h3 className={`text-sm font-semibold mb-4 flex items-center gap-2 ${isDarkMode ? 'text-gray-400' : 'text-gray-700'}`}>
                                <TrendingUp size={16} className="text-teal-400" />
                                Trending Now
                            </h3>

                            {realTrendingStocks.length === 0 ? (
                                <p className={`text-xs ${isDarkMode ? 'text-gray-500' : 'text-gray-400'}`}>Loading market data...</p>
                            ) : (
                                <div className="space-y-2">
                                    {realTrendingStocks.map((stock, index) => (
                                        <div
                                            key={stock.ticker}
                                            className={`p-3 rounded-lg border ${isDarkMode ? 'bg-[#161b22] border-gray-800' : 'bg-gray-50 border-gray-200'}`}
                                        >
                                            <div className="flex items-center justify-between">
                                                <div>
                                                    <p className={`text-sm font-medium ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>{stock.name || stock.ticker}</p>
                                                    <p className={`text-xs ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>₹{stock.price || 0}</p>
                                                </div>
                                                <span className={`px-2 py-1 text-xs font-medium rounded ${stock.change && stock.change > 0 ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                                                    }`}>
                                                    {stock.change && stock.change > 0 ? '↗' : '↘'} {stock.change ? stock.change.toFixed(2) : '0.00'}%
                                                </span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}

                            {/* Market Overview */}
                            <div className={`pt-6 border-t ${isDarkMode ? 'border-gray-800' : 'border-gray-200'}`}>
                                <h3 className={`text-sm font-semibold mb-4 flex items-center gap-2 ${isDarkMode ? 'text-gray-400' : 'text-gray-700'}`}>
                                    <span className="text-teal-400">📊</span>
                                    Market Overview
                                </h3>
                                <div className="space-y-2">
                                    <div className={`p-4 rounded-lg border ${isDarkMode ? 'bg-[#161b22] border-gray-800' : 'bg-gray-50 border-gray-200'}`}>
                                        <p className={`text-xs font-semibold mb-1 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>NSE Market Cap</p>
                                        <p className={`text-sm font-bold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>₹300+ Trillion (2024)</p>
                                    </div>
                                    <div className={`p-4 rounded-lg border ${isDarkMode ? 'bg-[#161b22] border-gray-800' : 'bg-gray-50 border-gray-200'}`}>
                                        <p className={`text-xs font-semibold mb-1 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>Listed Companies</p>
                                        <p className={`text-xs ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>5,500+ on BSE, 2,000+ on NSE</p>
                                    </div>
                                </div>
                            </div>

                            {/* Facts & Trivia */}
                            <div className={`pt-6 border-t ${isDarkMode ? 'border-gray-800' : 'border-gray-200'}`}>
                                <h3 className={`text-sm font-semibold mb-4 flex items-center gap-2 ${isDarkMode ? 'text-gray-400' : 'text-gray-700'}`}>
                                    <span className="text-teal-400">💡</span>
                                    Facts & Trivia
                                </h3>
                                <div className="space-y-2">
                                    <div className={`p-3 rounded-lg border ${isDarkMode ? 'bg-[#161b22] border-gray-800' : 'bg-gray-50 border-gray-200'}`}>
                                        <p className={`text-xs ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                                            SENSEX established in 1986
                                        </p>
                                    </div>
                                    <div className={`p-3 rounded-lg border ${isDarkMode ? 'bg-[#161b22] border-gray-800' : 'bg-gray-50 border-gray-200'}`}>
                                        <p className={`text-xs ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                                            SEBI (1992): Regulates India's securities market
                                        </p>
                                    </div>
                                    <div className={`p-3 rounded-lg border ${isDarkMode ? 'bg-[#161b22] border-gray-800' : 'bg-gray-50 border-gray-200'}`}>
                                        <p className={`text-xs ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                                            Investors: 90M+ registered on BSE & NSE (2024)
                                        </p>
                                    </div>
                                    <div className={`p-3 rounded-lg border ${isDarkMode ? 'bg-[#161b22] border-gray-800' : 'bg-gray-50 border-gray-200'}`}>
                                        <p className={`text-xs ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                                            Circuit Breakers: 10%, 15%, 20% limits halt volatility
                                        </p>
                                    </div>
                                    <div className={`p-3 rounded-lg border ${isDarkMode ? 'bg-[#161b22] border-gray-800' : 'bg-gray-50 border-gray-200'}`}>
                                        <p className={`text-xs ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                                            T+1 Settlement: Trades clear in 24 hours
                                        </p>
                                    </div>
                                    <div className={`p-3 rounded-lg border ${isDarkMode ? 'bg-[#161b22] border-gray-800' : 'bg-gray-50 border-gray-200'}`}>
                                        <p className={`text-xs ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                                            NIFTY 50: Benchmarks 66% of Indian market cap
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </motion.aside>
                </div>
            </div >
            {/* Hard Block Modal */}
            <AnimatePresence>
                {
                    showBlockModal && (
                        <HardBlockModal onClose={() => setShowBlockModal(false)} />
                    )
                }
            </AnimatePresence >
        </div >
    );

}

// Quick Info Component (unchanged)
function QuickInfoCard({ isDarkMode }: { isDarkMode: boolean }) {
    const features = [
        { text: 'Search any stock', icon: '🔍' },
        { text: 'Get AI-based report', icon: '🤖' },
        { text: 'User-friendly interface', icon: '✨' },
        { text: 'Provides insights', icon: '💡' }
    ];

    const dataSources = [
        { text: 'DuckDuckGo Search', icon: '🔍' },
        { text: 'RSS Feeds', icon: '📰' },
        { text: 'Financial APIs', icon: '📊' }
    ];

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className={`border rounded-xl p-6 ${isDarkMode ? 'bg-[#0d1117] border-gray-800' : 'bg-white border-gray-200'}`}
        >
            <div className="flex items-center gap-2 mb-6">
                <Info className="text-teal-400" size={20} />
                <h3 className="text-lg font-semibold text-white">Quick Info</h3>
            </div>

            <div className="space-y-6">
                <div>
                    <h4 className="text-teal-400 text-sm font-semibold mb-3">How it works:</h4>
                    <ul className="space-y-2">
                        {features.map((feature, i) => (
                            <motion.li
                                key={i}
                                initial={{ opacity: 0, x: -10 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: i * 0.1 }}
                                whileHover={{ x: 5 }}
                                className="text-gray-400 text-sm flex items-start gap-2 cursor-default transition-colors hover:text-teal-400"
                            >
                                <span className="text-teal-400">{feature.icon}</span>
                                {feature.text}
                            </motion.li>
                        ))}
                    </ul>
                </div>

                <div>
                    <h4 className="text-teal-400 text-sm font-semibold mb-3">Data Sources:</h4>
                    <ul className="space-y-2">
                        {dataSources.map((source, i) => (
                            <motion.li
                                key={i}
                                initial={{ opacity: 0, x: -10 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: 0.4 + i * 0.1 }}
                                whileHover={{ x: 5 }}
                                className="text-gray-400 text-sm flex items-start gap-2 cursor-default transition-colors hover:text-teal-400"
                            >
                                <span className="text-teal-400">{source.icon}</span>
                                {source.text}
                            </motion.li>
                        ))}
                    </ul>
                </div>
            </div>
        </motion.div>
    );
}

// Why Choose Platform Component (unchanged)
function WhyChooseCard({ isDarkMode }: { isDarkMode: boolean }) {
    const benefits = [
        {
            title: 'AI-Powered Analysis',
            description: 'Advanced machine learning algorithms analyze market trends and historical data to provide actionable insights.'
        },
        {
            title: 'Real-Time Predictions',
            description: 'Get instant stock predictions based on current market conditions and sentiment analysis.'
        },
        {
            title: 'Smart Recommendations',
            description: 'Receive personalized investment recommendations tailored to your risk profile and goals.'
        }
    ];

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            whileHover={{ y: -5, borderColor: 'rgba(20, 184, 166, 0.3)' }}
            className={`border rounded-2xl p-6 transition-all ${isDarkMode ? 'bg-[#0d1117] border-gray-800' : 'bg-white border-gray-200'}`}
        >
            <div className="flex items-center gap-2 mb-6">
                <BookOpen className="text-teal-400" size={20} />
                <h3 className="text-lg font-semibold text-white">Why Choose Our Platform?</h3>
            </div>

            <div className="space-y-4">
                {benefits.map((benefit, i) => (
                    <motion.div
                        key={i}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 + i * 0.1 }}
                        whileHover={{ x: 5, backgroundColor: 'rgba(20, 184, 166, 0.05)' }}
                        className="pb-4 border-b border-gray-800 last:border-0 last:pb-0 rounded-lg p-3 -mx-3 transition-colors cursor-default"
                    >
                        <h4 className="text-teal-400 text-sm font-semibold mb-2">{benefit.title}</h4>
                        <p className="text-gray-400 text-sm leading-relaxed">{benefit.description}</p>
                    </motion.div>
                ))}
            </div>

        </motion.div>
    );
}

// Hard Block Modal (unchanged)
function HardBlockModal({ onClose }: { onClose: () => void }) {
    const router = useRouter();
    const { isDarkMode } = useThemeStore();

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4"
            onClick={onClose}
        >
            <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.9, opacity: 0 }}
                onClick={(e) => e.stopPropagation()}
                className="bg-[#0d1117] border border-red-500/50 rounded-2xl p-10 max-w-md w-full text-center"
            >
                <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-red-500/10 flex items-center justify-center">
                    <AlertCircle className="text-red-400" size={32} />
                </div>

                <h2 className="text-2xl font-bold text-white mb-4">
                    Guest Limit Reached
                </h2>

                <p className="text-gray-400 text-base mb-8">
                    You've used all free guest analyses. Create a free account to get 5 analyses per day!
                </p>

                <div className="space-y-3">
                    <button
                        onClick={() => router.push('/auth/signup')}
                        className="w-full bg-gradient-to-r from-teal-500 to-cyan-500 text-white py-3 rounded-lg font-semibold hover:shadow-lg hover:shadow-teal-500/20 transition-all"
                    >
                        Sign Up Free - No Credit Card
                    </button>

                    <button
                        onClick={() => router.push('/auth/signin')}
                        className={`w-full py-3 rounded-lg font-semibold border transition-all ${isDarkMode ? 'border-gray-700 text-gray-300 hover:bg-gray-800' : 'border-gray-300 text-gray-700 hover:bg-gray-100'}`}
                    >
                        Sign In
                    </button>

                    <button
                        onClick={onClose}
                        className="w-full text-gray-400 hover:text-white py-2 text-sm transition-colors"
                    >
                        Maybe Later
                    </button>
                </div>
            </motion.div>
        </motion.div>
    );
}
