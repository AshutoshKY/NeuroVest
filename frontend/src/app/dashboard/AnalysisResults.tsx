'use client';

import { motion } from 'framer-motion';
import { CheckCircle, Loader, ChevronDown, ChevronUp, AlertTriangle, Info, Zap, X } from 'lucide-react';
import { CandlestickChart } from './components/PlotlyChart';
import { SentimentBadge } from './components';

interface AnalysisResultsProps {
    progressStatus: 'idle' | 'analyzing' | 'complete';
    selectedStock: any;
    analysisSteps: any[];
    isStepsCollapsed: boolean;
    setIsStepsCollapsed: (value: boolean) => void;
    analysisResult: any;
    chartRange: string;
    setChartRange: (value: string) => void;
    onClose: () => void;
    onSave: (analysisData: any) => void;
    onAddToWatchlist: () => void;
    isSaved?: boolean;
    isInWatchlist?: boolean;
}

export function AnalysisResults({
    progressStatus,
    selectedStock,
    analysisSteps,
    isStepsCollapsed,
    setIsStepsCollapsed,
    analysisResult,
    chartRange,
    setChartRange,
    onClose,
    onSave,
    onAddToWatchlist,
    isSaved = false,
    isInWatchlist = false
}: AnalysisResultsProps) {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
        >
            {/* Modern Thinking Steps Panel - Glassmorphism Design */}
            <div className="mb-4">
                <div className="relative bg-gradient-to-br from-slate-900/80 via-slate-800/50 to-slate-900/80 border border-emerald-500/20 rounded-2xl p-6 backdrop-blur-xl shadow-2xl shadow-emerald-500/10">
                    {/* Glow effect */}
                    <div className="absolute inset-0 bg-gradient-to-r from-emerald-500/5 via-transparent to-cyan-500/5 rounded-2xl" />

                    <div className="relative z-10">
                        <div className="flex items-center justify-between mb-6">
                            <h3 className="text-xl font-bold text-white flex items-center gap-3">
                                {progressStatus === 'complete' ? (
                                    <>
                                        <div className="p-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
                                            <CheckCircle className="text-emerald-400" size={24} />
                                        </div>
                                        <span>{isSaved ? 'Saved Analysis' : 'Analysis Complete'} • {selectedStock?.ticker}</span>
                                    </>
                                ) : (
                                    <>
                                        <div className="p-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20 animate-pulse">
                                            <Loader className="animate-spin text-emerald-400" size={24} />
                                        </div>
                                        <span>Analyzing {selectedStock?.ticker}...</span>
                                    </>
                                )}
                            </h3>
                            <motion.button
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                                onClick={() => setIsStepsCollapsed(!isStepsCollapsed)}
                                className="p-2.5 hover:bg-slate-700/50 rounded-xl transition-all duration-200 text-slate-400 hover:text-white border border-slate-700/50 hover:border-emerald-500/30"
                            >
                                {isStepsCollapsed ? <ChevronDown size={20} /> : <ChevronUp size={20} />}
                            </motion.button>
                        </div>

                        {!isStepsCollapsed && (
                            <div className="space-y-3">
                                {analysisSteps.map((step, i) => (
                                    <motion.div
                                        key={i}
                                        initial={{ opacity: 0, x: -20 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        transition={{ delay: i * 0.05 }}
                                        className="group relative p-4 rounded-xl border bg-gradient-to-r from-slate-800/60 to-slate-900/40 border-slate-700/50 hover:border-emerald-500/30 transition-all duration-200 backdrop-blur-sm"
                                    >
                                        <div className="absolute inset-0 bg-gradient-to-r from-emerald-500/0 via-emerald-500/5 to-emerald-500/0 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity" />
                                        <div className="relative flex items-start justify-between gap-3">
                                            <span className="text-sm flex-1 text-slate-200 leading-relaxed">{step.text || step.description || 'Processing...'}</span>
                                            <div className="flex flex-col items-end gap-1">
                                                <span className="text-emerald-400 font-mono text-xs bg-emerald-500/10 px-2 py-1 rounded-lg border border-emerald-500/20 whitespace-nowrap">
                                                    {step.timestamp && new Date(step.timestamp).toLocaleTimeString('en-US', { hour12: false })}
                                                </span>
                                                {step.timeTaken && (
                                                    <span className="text-cyan-400 font-mono text-xs bg-cyan-500/10 px-2 py-1 rounded-lg border border-cyan-500/20">
                                                        {parseFloat(step.timeTaken).toFixed(2)}s
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                    </motion.div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Cache Warning */}
            {analysisResult?.cached && (
                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="mb-4 p-4 bg-gradient-to-r from-yellow-500/10 to-amber-500/10 border border-yellow-500/30 rounded-xl flex items-center gap-3 backdrop-blur-sm"
                >
                    <Zap className="text-yellow-400" size={20} />
                    <p className="text-yellow-400 text-sm font-medium">Fetched from cache (FREE) - Fresh analysis available in less than 1 hour</p>
                </motion.div>
            )}

            {/* Results Content - Only show when complete */}
            {progressStatus === 'complete' && analysisResult && (
                <>
                    {/* Header with Close, Save, & Watchlist */}
                    <div className="flex items-center justify-between mb-8">
                        <h2 className="text-2xl font-semibold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">AI Analysis Results</h2>
                        <div className="flex items-center gap-3">
                            {/* Conditionally show Save button or Saved badge */}
                            {!isSaved ? (
                                <motion.button
                                    whileHover={{ scale: 1.05 }}
                                    whileTap={{ scale: 0.95 }}
                                    onClick={() => onSave(analysisResult)}
                                    className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-cyan-600 border border-emerald-500/50 text-sm text-white hover:from-emerald-500 hover:to-cyan-500 transition-all duration-200 font-medium shadow-lg flex items-center gap-2"
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                        <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" />
                                        <polyline points="17 21 17 13 7 13 7 21" />
                                        <polyline points="7 3 7 8 15 8" />
                                    </svg>
                                    Save Analysis
                                </motion.button>
                            ) : (
                                <div className="px-5 py-2.5 rounded-xl bg-emerald-500/20 border border-emerald-500/50 text-sm text-emerald-400 font-medium flex items-center gap-2">
                                    <CheckCircle className="w-4 h-4" />
                                    Saved Analysis
                                </div>
                            )}

                            {/* Watchlist button - conditional state */}
                            <motion.button
                                whileHover={{ scale: isInWatchlist ? 1 : 1.05 }}
                                whileTap={{ scale: isInWatchlist ? 1 : 0.95 }}
                                onClick={isInWatchlist ? undefined : onAddToWatchlist}
                                disabled={isInWatchlist}
                                className={`px-5 py-2.5 rounded-xl ${isInWatchlist
                                    ? 'bg-cyan-500/20 border border-cyan-500/50 text-cyan-400 cursor-default'
                                    : 'bg-gradient-to-r from-cyan-600 to-blue-600 border border-cyan-500/50 text-white hover:from-cyan-500 hover:to-blue-500'
                                    } text-sm transition-all duration-200 font-medium shadow-lg flex items-center gap-2`}
                                title={isInWatchlist ? "Already in watchlist" : "Add to Watchlist"}
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill={isInWatchlist ? "currentColor" : "none"} stroke="currentColor" strokeWidth="2">
                                    <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
                                </svg>
                                {isInWatchlist ? 'In Watchlist' : 'Add to Watchlist'}
                            </motion.button>

                            {/* Close button */}
                            <motion.button
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                                onClick={onClose}
                                className="p-2.5 rounded-xl bg-slate-800/50 border border-slate-700 text-slate-400 hover:text-white hover:border-red-500/50 hover:bg-red-500/10 transition-all duration-200"
                                title="Close"
                            >
                                <X size={20} />
                            </motion.button>
                        </div>
                    </div>

                    {/* TOP ROW: Key Metrics + Price Charts */}
                    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mb-8 items-start">
                        {/* Key Metrics - Left Column (4/12) */}
                        <div className="lg:col-span-4">
                            <div className="flex items-end gap-2 mb-4 h-10">
                                <div className="w-1 h-6 bg-gradient-to-b from-emerald-400 to-cyan-400 rounded-full" />
                                <h3 className="text-base font-semibold text-white leading-none">Key Metrics</h3>
                            </div>

                            <div className="relative bg-gradient-to-br from-slate-900/90 via-slate-800/50 to-slate-900/90 p-6 rounded-2xl border border-slate-700/50 backdrop-blur-xl shadow-2xl">
                                <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/5 to-cyan-500/5 rounded-2xl" />
                                <div className="relative z-10 space-y-6">
                                    {/* Current Price */}
                                    <div>
                                        <div className="text-xs text-slate-400 font-semibold mb-2 flex items-center gap-2">
                                            <span className="text-lg">💰</span> Current Price
                                        </div>
                                        <div className="text-3xl font-semibold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
                                            {analysisResult.currency || 'INR'} {(analysisResult.price || 0).toFixed(2)}
                                        </div>
                                    </div>

                                    {/* Sentiment Badge */}
                                    <div>
                                        <SentimentBadge sentiment={analysisResult.sentiment} />
                                    </div>

                                    {/* Confidence Score */}
                                    <div className="pt-6 border-t border-slate-700/50">
                                        <div className="flex items-center gap-2 mb-3">
                                            <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                                            <span className="text-slate-300 text-sm font-semibold">🎯 Confidence Score</span>
                                        </div>
                                        <div className="text-2xl font-semibold text-white mb-3">{(analysisResult.confidence || 0).toFixed(2)}%</div>
                                        <div className="w-full h-3 bg-slate-800 rounded-full overflow-hidden shadow-inner">
                                            <div
                                                className="h-full bg-gradient-to-r from-emerald-500 via-emerald-400 to-cyan-400 transition-all duration-500 relative"
                                                style={{ width: `${analysisResult.confidence}%` }}
                                            >
                                                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-pulse" />
                                            </div>
                                        </div>
                                    </div>

                                    {/* Day Range */}
                                    <div className="pt-6 border-t border-slate-700/50">
                                        <div className="text-xs text-slate-400 font-semibold mb-2">Day Range</div>
                                        <div className="text-base font-medium text-slate-200">
                                            {analysisResult.currency || 'INR'} {(analysisResult.dayLow || 0).toFixed(2)} - {analysisResult.currency || 'INR'} {(analysisResult.dayHigh || 0).toFixed(2)}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Price Charts - Right Column (8/12) */}
                        <div className="lg:col-span-8">
                            <div className="flex items-end gap-2 mb-4 h-10">
                                <div className="w-1 h-6 bg-gradient-to-b from-emerald-400 to-cyan-400 rounded-full" />
                                <h3 className="text-base font-semibold text-white leading-none">📈 Price Charts</h3>
                            </div>
                            <div className="relative bg-gradient-to-br from-slate-900/90 via-slate-800/50 to-slate-900/90 p-6 rounded-2xl border border-slate-700/50 backdrop-blur-xl shadow-2xl">
                                <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/5 to-cyan-500/5 rounded-2xl" />
                                <div className="relative z-10">
                                    {/* Chart Range Selector */}
                                    <div className="flex gap-2 mb-6 border-b border-slate-700/50 pb-4">
                                        {[
                                            { label: '1 Day', value: '1d' },
                                            { label: '5 Days', value: '5d' },
                                            { label: '1 Month', value: '1mo' },
                                            { label: '3 Months', value: '3mo' },
                                            { label: '1 Year', value: '1y' }
                                        ].map(({ label, value }) => (
                                            <motion.button
                                                key={value}
                                                whileHover={{ scale: 1.05 }}
                                                whileTap={{ scale: 0.95 }}
                                                onClick={() => setChartRange(value)}
                                                className={`text-sm px-4 py-2 rounded-xl transition-all duration-200 font-medium ${chartRange === value
                                                    ? 'bg-gradient-to-r from-emerald-500 to-cyan-500 text-white shadow-lg shadow-emerald-500/30'
                                                    : 'text-slate-400 hover:text-white hover:bg-slate-800'
                                                    }`}
                                            >
                                                {label}
                                            </motion.button>
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
                                        <div className="h-[300px] flex items-center justify-center text-slate-500">
                                            <span>No chart data available</span>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Technical Indicators */}
                    <div className="mb-8">
                        <div className="flex items-center gap-2 mb-4">
                            <div className="w-1 h-6 bg-gradient-to-b from-emerald-400 to-cyan-400 rounded-full" />
                            <h3 className="text-base font-semibold text-white">📊 Technical Indicators</h3>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                            {/* RSI */}
                            <div className="relative bg-gradient-to-br from-slate-900/90 via-slate-800/50 to-slate-900/90 p-6 rounded-2xl border border-slate-700/50 backdrop-blur-xl shadow-2xl">
                                <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/5 to-emerald-500/5 rounded-2xl" />
                                <div className="relative z-10">
                                    <span className="text-xs font-semibold text-emerald-400 bg-emerald-400/10 px-3 py-1 rounded-lg border border-emerald-500/20">📉 RSI (14)</span>
                                    <div className="text-3xl font-semibold text-white my-4">{analysisResult.rsi || 0}</div>
                                    <div className="text-sm text-slate-400 mb-4">
                                        <span className="text-yellow-400 font-semibold">🟡 Neutral</span>
                                    </div>
                                    <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                                        <div className="h-full bg-gradient-to-r from-blue-500 to-cyan-500" style={{ width: `${Math.min((analysisResult.rsi / 100) * 100, 100)}%` }} />
                                    </div>
                                </div>
                            </div>

                            {/* MACD */}
                            <div className="relative bg-gradient-to-br from-slate-900/90 via-slate-800/50 to-slate-900/90 p-6 rounded-2xl border border-slate-700/50 backdrop-blur-xl shadow-2xl">
                                <div className="absolute inset-0 bg-gradient-to-br from-purple-500/5 to-purple-500/5 rounded-2xl" />
                                <div className="relative z-10">
                                    <span className="text-xs font-semibold text-purple-400 bg-purple-400/10 px-3 py-1 rounded-lg border border-purple-500/20">📈 MACD</span>
                                    <div className="text-3xl font-semibold text-white my-4">{(analysisResult.macd || 0).toFixed(2)}</div>
                                    <div className="text-sm text-slate-400 mb-2">
                                        <span className="text-red-400 font-semibold">↓ Bearish</span>
                                    </div>
                                    <div className="space-y-1 text-xs">
                                        <div className="flex justify-between text-slate-500">
                                            <span>Signal:</span>
                                            <span className="text-slate-300 font-mono">{(analysisResult.macdSignal || 0).toFixed(2)}</span>
                                        </div>
                                        <div className="flex justify-between text-slate-500">
                                            <span>Histogram:</span>
                                            <span className="text-slate-300 font-mono">{(analysisResult.macdHist || 0).toFixed(2)}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Bollinger Bands */}
                            <div className="relative bg-gradient-to-br from-slate-900/90 via-slate-800/50 to-slate-900/90 p-6 rounded-2xl border border-slate-700/50 backdrop-blur-xl shadow-2xl">
                                <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-blue-500/5 rounded-2xl" />
                                <div className="relative z-10">
                                    <span className="text-xs font-semibold text-blue-400 bg-blue-400/10 px-3 py-1 rounded-lg border border-blue-500/20">📊 Bollinger Bands</span>
                                    <div className="text-sm text-red-400 font-semibold my-4">Position: Below Middle (Bearish Zone)</div>
                                    <div className="space-y-2">
                                        <div className="flex justify-between text-sm">
                                            <span className="text-slate-500">Upper:</span>
                                            <span className="text-slate-200 font-mono bg-slate-800/50 px-2 py-1 rounded">{(analysisResult.bollingerUpper || 0).toFixed(2)}</span>
                                        </div>
                                        <div className="flex justify-between text-sm">
                                            <span className="text-slate-500">Middle:</span>
                                            <span className="text-slate-200 font-mono bg-slate-800/50 px-2 py-1 rounded">{(analysisResult.bollingerMiddle || 0).toFixed(2)}</span>
                                        </div>
                                        <div className="flex justify-between text-sm">
                                            <span className="text-slate-500">Lower:</span>
                                            <span className="text-slate-200 font-mono bg-slate-800/50 px-2 py-1 rounded">{(analysisResult.bollingerLower || 0).toFixed(2)}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* AI Analysis */}
                    <div className="mb-8">
                        <div className="flex items-center gap-2 mb-4">
                            <div className="w-1 h-6 bg-gradient-to-b from-emerald-400 to-cyan-400 rounded-full" />
                            <h3 className="text-base font-semibold text-white">🤖 AI Analysis</h3>
                        </div>
                        <div className="relative bg-gradient-to-br from-slate-900/90 via-slate-800/50 to-slate-900/90 border border-slate-700/50 p-8 rounded-2xl backdrop-blur-xl shadow-2xl">
                            <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/5 to-cyan-500/5 rounded-2xl" />

                            <div className="relative z-10 space-y-6">
                                {/* Summary - Executive Overview */}
                                {analysisResult.analysis_structured?.summary ? (
                                    <div className="pb-6 border-b border-slate-700/50">
                                        <h4 className="text-sm font-bold text-emerald-400 mb-3 uppercase tracking-wide">📋 Executive Summary</h4>
                                        <p className="text-slate-100 text-base leading-relaxed font-medium">
                                            {analysisResult.analysis_structured.summary}
                                        </p>
                                    </div>
                                ) : (
                                    <div className="pb-6 border-b border-slate-700/50">
                                        <p className="text-red-400 text-sm">⚠️ No summary available (analysis_structured.summary is missing)</p>
                                    </div>
                                )}

                                {/* Key Points - Bullet List */}
                                {analysisResult.analysis_structured?.key_points && Array.isArray(analysisResult.analysis_structured.key_points) && analysisResult.analysis_structured.key_points.length > 0 ? (
                                    <div className="pb-6 border-b border-slate-700/50">
                                        <h4 className="text-sm font-bold text-cyan-400 mb-4 uppercase tracking-wide">🔑 Key Points</h4>
                                        <ul className="space-y-3">
                                            {analysisResult.analysis_structured.key_points.map((point: string, idx: number) => (
                                                <li key={idx} className="flex items-start gap-3">
                                                    <div className="mt-1 w-1.5 h-1.5 rounded-full bg-emerald-400 shrink-0" />
                                                    <span className="text-slate-200 text-sm leading-relaxed">{point}</span>
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                ) : (
                                    <div className="pb-6 border-b border-slate-700/50">
                                        <p className="text-red-400 text-sm">⚠️ No key points available (analysis_structured.key_points is {typeof analysisResult.analysis_structured?.key_points})</p>
                                    </div>
                                )}

                                {/* Full Detailed Analysis */}
                                <div>
                                    <h4 className="text-sm font-bold text-slate-400 mb-4 uppercase tracking-wide">📊 Detailed Analysis</h4>
                                    <p className="text-slate-200 leading-relaxed text-base whitespace-pre-wrap">
                                        {analysisResult.analysis_structured?.full_text || analysisResult.analysis || '⚠️ No analysis text available'}
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* SINGLE Disclaimer - Yellow Only */}
                    <div className="mb-8 p-5 bg-gradient-to-r from-yellow-500/10 to-amber-500/10 border border-yellow-500/30 rounded-2xl flex gap-4 backdrop-blur-sm shadow-lg">
                        <AlertTriangle className="text-yellow-400 shrink-0" size={24} />
                        <div>
                            <h4 className="text-yellow-400 font-semibold text-sm mb-2">⚠️ IMPORTANT DISCLAIMER</h4>
                            <p className="text-yellow-400/80 text-sm mb-3">
                                This analysis is provided for informational and educational purposes only. It does not constitute financial advice, investment recommendations, or an offer to buy or sell any securities.
                            </p>
                            <div className="space-y-1.5 text-xs text-yellow-400/70">
                                <p>• This is AI-generated analysis based on publicly available information</p>
                                <p>• Past performance does not guarantee future results</p>
                                <p>• Market data and sentiment can change rapidly</p>
                                <p>• Always conduct your own research and consult with a qualified financial advisor</p>
                                <p>• Investment decisions should be based on your individual financial situation, goals, and risk tolerance</p>
                            </div>
                        </div>
                    </div>

                    {/* Key Insights */}
                    {analysisResult.insights?.length > 0 && (
                        <div className="mb-8">
                            <div className="flex items-center gap-2 mb-4">
                                <div className="w-1 h-6 bg-gradient-to-b from-emerald-400 to-cyan-400 rounded-full" />
                                <h3 className="text-base font-semibold text-white">Recent Trends & Key Insights</h3>
                            </div>
                            <div className="space-y-3">
                                {analysisResult.insights.map((insight: string, idx: number) => (
                                    <motion.div
                                        key={idx}
                                        initial={{ opacity: 0, x: -20 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        transition={{ delay: idx * 0.1 }}
                                        className={`p-4 rounded-xl flex gap-3 items-start backdrop-blur-sm ${idx === 3
                                            ? 'bg-gradient-to-r from-red-500/10 to-red-500/5 border border-red-500/30'
                                            : 'bg-gradient-to-r from-blue-500/10 to-cyan-500/5 border border-blue-500/30'}`}
                                    >
                                        <Info className={`shrink-0 w-5 h-5 ${idx === 3 ? 'text-red-400' : 'text-blue-400'}`} />
                                        <p className="text-slate-200 text-sm leading-relaxed">{insight}</p>
                                    </motion.div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Future Outlook - Enhanced */}
                    <div className="mb-8">
                        <div className="flex items-center gap-2 mb-4">
                            <div className="w-1 h-6 bg-gradient-to-b from-emerald-400 to-cyan-400 rounded-full" />
                            <h3 className="text-base font-semibold text-white">🔮 Future Outlook & Prediction</h3>
                        </div>
                        <div className="relative bg-gradient-to-br from-indigo-900/40 via-blue-900/30 to-indigo-900/40 border border-blue-500/40 p-8 rounded-2xl backdrop-blur-sm shadow-2xl overflow-hidden">
                            {/* Animated background effect */}
                            <div className="absolute inset-0 bg-gradient-to-r from-blue-500/5 via-indigo-500/10 to-blue-500/5 rounded-2xl animate-pulse" />
                            <div className="absolute top-4 right-4 text-6xl opacity-10">📊</div>
                            <div className="relative z-10 space-y-6">
                                {/* Prediction Summary */}
                                {analysisResult.prediction_structured?.summary && (
                                    <div className="pb-6 border-b border-blue-500/20">
                                        <h4 className="text-sm font-bold text-blue-300 mb-3 uppercase tracking-wide">Prediction Overview</h4>
                                        <p className="text-blue-50 text-base leading-relaxed font-medium">
                                            {analysisResult.prediction_structured.summary}
                                        </p>
                                    </div>
                                )}

                                {/* Detailed Outlook */}
                                <div>
                                    <h4 className="text-sm font-bold text-blue-400/70 mb-4 uppercase tracking-wide">Detailed Outlook</h4>
                                    <p className="text-blue-50 leading-relaxed text-base whitespace-pre-wrap">
                                        {analysisResult.prediction_structured?.outlook || analysisResult.prediction || analysisResult.futureOutlook || 'No prediction available'}
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Risk Factors - Enhanced with Cards */}
                    {analysisResult.risks?.length > 0 && (
                        <div className="mb-8">
                            <div className="flex items-center gap-2 mb-4">
                                <AlertTriangle className="text-yellow-500" size={20} />
                                <h3 className="text-base font-semibold text-white">⚠️ Risk Factors</h3>
                            </div>
                            <div className="space-y-3">
                                {analysisResult.risks.map((risk: string, idx: number) => (
                                    <motion.div
                                        key={idx}
                                        initial={{ opacity: 0, x: -20 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        transition={{ delay: idx * 0.08 }}
                                        className="group relative p-4 rounded-xl bg-gradient-to-r from-red-900/20 via-orange-900/10 to-red-900/20 border border-red-500/30 hover:border-red-500/50 transition-all duration-200 backdrop-blur-sm"
                                    >
                                        <div className="absolute inset-0 bg-gradient-to-r from-red-500/0 via-red-500/5 to-red-500/0 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity" />
                                        <div className="relative flex items-start gap-3">
                                            <div className="mt-0.5 p-1.5 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
                                                <AlertTriangle className="text-yellow-400" size={16} />
                                            </div>
                                            <p className="text-slate-200 text-sm leading-relaxed flex-1">{risk}</p>
                                        </div>
                                    </motion.div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* References - Enhanced */}
                    {analysisResult.references?.length > 0 && (
                        <div className="mb-8">
                            <div className="flex items-center gap-2 mb-4">
                                <div className="w-1 h-6 bg-gradient-to-b from-emerald-400 to-cyan-400 rounded-full" />
                                <h3 className="text-base font-semibold text-white">📚 References ({analysisResult.references.length})</h3>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                {analysisResult.references.map((ref: any, idx: number) => (
                                    <motion.div
                                        key={idx}
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        transition={{ delay: idx * 0.05 }}
                                        className="group relative p-4 rounded-xl bg-gradient-to-br from-slate-800/60 to-slate-900/60 border border-slate-700/50 hover:border-emerald-500/40 transition-all duration-200 backdrop-blur-sm"
                                    >
                                        <div className="absolute inset-0 bg-gradient-to-r from-emerald-500/0 via-emerald-500/5 to-emerald-500/0 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity" />
                                        <div className="relative flex items-start gap-3">
                                            <div className="mt-0.5 px-2 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-mono text-xs font-semibold">
                                                {idx + 1}
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <a
                                                    href={ref.url || '#'}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className="text-emerald-400 hover:text-emerald-300 text-sm font-medium block truncate transition-colors group-hover:underline"
                                                >
                                                    {ref.source || ref.ticker || 'Reference'}
                                                </a>
                                                {ref.timestamp && (
                                                    <span className="text-slate-500 text-xs mt-1 block">
                                                        📅 {new Date(ref.timestamp).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })}
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                    </motion.div>
                                ))}
                            </div>
                        </div>
                    )}
                </>
            )}
        </motion.div>
    );
}
