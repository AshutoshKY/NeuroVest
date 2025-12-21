'use client';

import { useState } from 'react';
import { useUI } from '@/contexts/UIContext';

/**
 * Tabbed Analysis - Narrative Display
 * Two tabs: "AI Analysis" and "Key Factors"
 * Different content for Lite vs Pro
 * Matches design from analysis_8.html
 */

interface TabbedAnalysisProps {
    narrative: {
        analysis_summary?: string;
        analysis_text: string;
        prediction_summary?: string;
        prediction_text: string;
    };
    factors?: string[];
}

export function TabbedAnalysis({ narrative, factors = [] }: TabbedAnalysisProps) {
    const { mode } = useUI();
    const [activeTab, setActiveTab] = useState<'analysis' | 'factors'>('analysis');

    return (
        <div className="space-y-4">
            {/* Tab Navigation */}
            <div className="flex gap-1 border-b border-gray-200 dark:border-zinc-800">
                <button
                    onClick={() => setActiveTab('analysis')}
                    className={`px-4 py-2.5 text-sm font-bold transition-all tab-btn ${activeTab === 'analysis'
                            ? 'text-primary-600 dark:text-primary-400 active'
                            : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
                        }`}
                >
                    AI Analysis
                </button>
                <button
                    onClick={() => setActiveTab('factors')}
                    className={`px-4 py-2.5 text-sm font-bold transition-all tab-btn ${activeTab === 'factors'
                            ? 'text-primary-600 dark:text-primary-400 active'
                            : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
                        }`}
                >
                    Key Factors
                </button>
            </div>

            {/* Tab Content */}
            <div className="p-6 rounded-xl bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800">
                {activeTab === 'analysis' && (
                    <div className="space-y-6">
                        {/* Lite Mode - Simplified */}
                        <div className="lite-element space-y-4">
                            {narrative.analysis_summary && (
                                <div>
                                    <h4 className="text-sm font-bold text-gray-900 dark:text-white mb-2 flex items-center gap-2">
                                        <span className="text-lg">📊</span>
                                        What's Happening?
                                    </h4>
                                    <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
                                        {narrative.analysis_summary}
                                    </p>
                                </div>
                            )}

                            {narrative.prediction_summary && (
                                <div>
                                    <h4 className="text-sm font-bold text-gray-900 dark:text-white mb-2 flex items-center gap-2">
                                        <span className="text-lg">🔮</span>
                                        What's Next?
                                    </h4>
                                    <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
                                        {narrative.prediction_summary}
                                    </p>
                                </div>
                            )}

                            {/* If no summaries, show full text */}
                            {!narrative.analysis_summary && !narrative.prediction_summary && narrative.analysis_text && (
                                <div>
                                    <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-wrap">
                                        {narrative.analysis_text}
                                    </p>
                                </div>
                            )}
                        </div>

                        {/* Pro Mode - Full Technical */}
                        <div className="pro-element space-y-6">
                            {/* Current Analysis */}
                            <div>
                                <h4 className="text-xs font-bold text-gray-500 font-mono uppercase tracking-wider mb-3 flex items-center gap-2">
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                                    </svg>
                                    Current Market Analysis
                                </h4>
                                <div className="p-4 rounded-lg bg-gray-50 dark:bg-zinc-950 border border-gray-200 dark:border-zinc-800">
                                    <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed font-mono whitespace-pre-wrap">
                                        {narrative.analysis_text || 'No analysis available'}
                                    </p>
                                </div>
                            </div>

                            {/* Prediction */}
                            {narrative.prediction_text && (
                                <div>
                                    <h4 className="text-xs font-bold text-gray-500 font-mono uppercase tracking-wider mb-3 flex items-center gap-2">
                                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                                        </svg>
                                        Forward-Looking Prediction
                                    </h4>
                                    <div className="p-4 rounded-lg bg-primary-500/5 border border-primary-500/20">
                                        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed font-mono whitespace-pre-wrap">
                                            {narrative.prediction_text}
                                        </p>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {activeTab === 'factors' && (
                    <div className="space-y-4">
                        {factors.length > 0 ? (
                            <>
                                <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                                    {mode === 'lite'
                                        ? 'Important things to know about this stock:'
                                        : 'Key technical and fundamental factors influencing current assessment:'}
                                </p>
                                <div className="space-y-2.5">
                                    {factors.map((factor, index) => (
                                        <div
                                            key={index}
                                            className="flex items-start gap-3 p-3 rounded-lg bg-gray-50 dark:bg-zinc-950 border border-gray-200 dark:border-zinc-800"
                                        >
                                            <div className="flex-shrink-0 w-6 h-6 rounded-full bg-primary-500/10 text-primary-600 dark:text-primary-400 flex items-center justify-center text-xs font-bold">
                                                {index + 1}
                                            </div>
                                            <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed flex-1">
                                                {factor}
                                            </p>
                                        </div>
                                    ))}
                                </div>
                            </>
                        ) : (
                            <div className="text-center py-8 text-gray-500">
                                <svg className="w-12 h-12 mx-auto mb-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                </svg>
                                <p className="text-sm">No key factors available</p>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
