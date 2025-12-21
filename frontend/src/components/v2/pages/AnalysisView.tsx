'use client';

import { useUI } from '@/contexts/UIContext';
import { PositioningBanner } from '@/components/v2/layout/PositioningBanner';
import { TopNav } from '@/components/v2/layout/TopNav';
import { MarketState } from '@/components/v2/analysis/MarketState';
import { PriceChart } from '@/components/v2/analysis/PriceChart';
import { PriceZones } from '@/components/v2/analysis/PriceZones';
import { ScenarioGrid } from '@/components/v2/analysis/ScenarioGrid';
import { ScenarioSummary } from '@/components/v2/analysis/ScenarioSummary';
import { TechnicalMatrix } from '@/components/v2/analysis/TechnicalMatrix';
import { TabbedAnalysis } from '@/components/v2/analysis/TabbedAnalysis';
import { SearchBar } from '@/components/v2/dashboard/SearchBar';
import { TrendingCard } from '@/components/v2/dashboard/TrendingCard';
import { RightDrawer } from '@/components/v2/layout/RightDrawer';
import { mapAnalysisToV2, type AnalysisV2Data } from '@/lib/api/mappers';
import { motion, AnimatePresence } from 'framer-motion';
import { useEffect, useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/authStore';
import apiClient from '@/lib/api';

/**
 * Analysis View Component
 * Displays the full analysis inline (no navigation)
 * Matches POC design from analysis_8.html
 */

interface AnalysisViewProps {
    analysisData: AnalysisV2Data;
    selectedStock: {
        ticker: string;
        name: string;
        exchange: string;
    };
    onClose: () => void;
    onSave: () => void;
    onWatchlist: () => void;
    isAnalyzing: boolean;
    analysisSteps: any[];
}

export function AnalysisView({
    analysisData,
    selectedStock,
    onClose,
    onSave,
    onWatchlist,
    isAnalyzing,
    analysisSteps
}: AnalysisViewProps) {
    const { mode } = useUI();
    const [isStepsCollapsed, setIsStepsCollapsed] = useState(false);

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-emerald-950/20">
            {/* Positioning Banner */}
            <PositioningBanner />

            {/* Top Navigation with Mode Toggle */}
            <TopNav
                ticker={selectedStock.ticker}
                showBack
                showActions
                onClose={onClose}
                onSave={onSave}
                onWatchlist={onWatchlist}
            />

            {/* Main Analysis Content */}
            <div className="pt-48 px-4 md:px-8 max-w-6xl mx-auto pb-20">
                <AnimatePresence>
                    {/* Thinking Steps */}
                    {isAnalyzing && analysisSteps.length > 0 && (
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            className="mb-6"
                        >
                            <div className="bg-gradient-to-br from-slate-900/80 via-slate-800/50 to-slate-900/80 border border-emerald-500/20 rounded-2xl p-6 backdrop-blur-xl shadow-2xl">
                                <div className="flex items-center justify-between mb-4">
                                    <h3 className="text-lg font-bold text-white">
                                        {isAnalyzing ? '🔄 Analyzing...' : '✅ Analysis Complete'}
                                    </h3>
                                    <button
                                        onClick={() => setIsStepsCollapsed(!isStepsCollapsed)}
                                        className="p-2 hover:bg-slate-700/50 rounded-lg transition text-slate-400 hover:text-white"
                                    >
                                        {isStepsCollapsed ? '▼' : '▲'}
                                    </button>
                                </div>

                                {!isStepsCollapsed && (
                                    <div className="space-y-2">
                                        {analysisSteps.map((step, i) => (
                                            <div
                                                key={i}
                                                className="p-3 rounded-lg bg-slate-800/60 border border-slate-700/50"
                                            >
                                                <div className="flex items-start justify-between gap-3">
                                                    <span className="text-sm text-slate-200 flex-1">
                                                        {step.text || step.description || 'Processing...'}
                                                    </span>
                                                    {step.timeTaken && (
                                                        <span className="text-xs text-cyan-400 font-mono">
                                                            {parseFloat(step.timeTaken).toFixed(2)}s
                                                        </span>
                                                    )}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </motion.div>
                    )}

                    {/* Analysis Content - All Components Integrated */}
                    {analysisData && (
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="space-y-8"
                        >
                            {/* Header with ticker and price */}
                            <div className="flex flex-col md:flex-row justify-between items-end border-b border-gray-200 dark:border-zinc-800 pb-6">
                                <div>
                                    <div className="flex items-center gap-3 mb-2">
                                        <span className="text-xs font-mono text-gray-500 bg-gray-100 dark:bg-zinc-900 px-2 py-1 rounded border border-gray-200 dark:border-zinc-800">
                                            {selectedStock.exchange || 'NSE'}
                                        </span>
                                        <h1 className="text-4xl font-bold text-gray-900 dark:text-white tracking-tight">
                                            {selectedStock.ticker}
                                        </h1>
                                    </div>

                                    {/* Mode-specific info */}
                                    <div className="mt-3 pro-element">
                                        <span className="text-xs text-primary-500 font-bold font-mono">
                                            REGIME: {analysisData.market_state?.trend_bias?.toUpperCase() || 'UNKNOWN'}
                                        </span>
                                    </div>

                                    <div className="mt-3 lite-element">
                                        <div className="flex items-center gap-3">
                                            <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-bold border ${analysisData.market_state?.trend_bias === 'bullish'
                                                ? 'bg-success/10 text-success border-success/20'
                                                : analysisData.market_state?.trend_bias === 'bearish'
                                                    ? 'bg-danger/10 text-danger border-danger/20'
                                                    : 'bg-gray-500/10 text-gray-500 border-gray-500/20'
                                                }`}>
                                                <span className="w-2 h-2 rounded-full bg-current" />
                                                {analysisData.sentiment || 'Neutral'}
                                            </span>
                                            <span className="text-xs text-gray-500">Market mood</span>
                                        </div>
                                    </div>
                                </div>

                                {/* Price */}
                                <div className="text-right">
                                    <div className="text-5xl font-mono font-medium text-gray-900 dark:text-white tracking-tighter">
                                        {analysisData.price.toFixed(2)}
                                    </div>
                                    <div className="text-xs text-gray-500 mt-1 font-mono">
                                        LATEST CLOSE ({analysisData.currency || 'INR'})
                                    </div>
                                </div>
                            </div>

                            {/* Market State Component */}
                            <MarketState marketState={analysisData.market_state} />

                            {/* Chart + Zones Layout */}
                            <div className="flex flex-col lg:flex-row gap-6">
                                <PriceChart
                                    data={analysisData.historicalDataMulti}
                                    ticker={selectedStock.ticker}
                                />

                                {/* Price Zones (Pro only) */}
                                {mode === 'pro' && analysisData.price_zones && (
                                    <div className="lg:w-[45%]">
                                        <PriceZones
                                            zones={analysisData.price_zones}
                                            ticker={selectedStock.ticker}
                                        />
                                    </div>
                                )}
                            </div>

                            {/* Scenarios - Conditional based on mode */}
                            {mode === 'lite' ? (
                                <ScenarioSummary scenarios={analysisData.scenarios} />
                            ) : (
                                <ScenarioGrid scenarios={analysisData.scenarios} />
                            )}

                            {/* Technical Matrix (Pro only) */}
                            {mode === 'pro' && (
                                <TechnicalMatrix
                                    indicators={{
                                        rsi: analysisData.rsi,
                                        macd: analysisData.macd,
                                        sma: analysisData.sma,
                                    }}
                                />
                            )}

                            {/* Tabbed Analysis - Narrative */}
                            <TabbedAnalysis
                                narrative={analysisData.narrative}
                                factors={analysisData.insights || []}
                            />
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
}
