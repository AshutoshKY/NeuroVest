'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuthStore } from '@/store/authStore';
import { Clock, TrendingUp, TrendingDown, Minus, Trash2, Eye, Loader2, History, Calendar } from 'lucide-react';
import apiClient from '@/lib/api';

interface HistoryItem {
    id: number;
    ticker: string;
    name: string;
    created_at: string;
    analysis_data?: {
        sentiment?: string | { classification: string; confidence: number };
        confidence?: number;
        recommendation?: string;
    };
}

export default function HistoryPage() {
    const router = useRouter();
    const { isAuthenticated } = useAuthStore();
    const [history, setHistory] = useState<HistoryItem[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [deleteLoading, setDeleteLoading] = useState<number | null>(null);

    useEffect(() => {
        if (!isAuthenticated) {
            router.push('/auth/login');
            return;
        }

        fetchHistory();
    }, [isAuthenticated, router]);

    const fetchHistory = async () => {
        try {
            setIsLoading(true);
            const response = await apiClient.get('/api/history');
            const historyData = Array.isArray(response.data) ? response.data : [];
            setHistory(historyData);
        } catch (error) {
            console.error('Failed to fetch history:', error);
            setHistory([]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleView = (item: HistoryItem) => {
        router.push('/dashboard');
    };

    const handleDelete = async (id: number) => {
        if (!confirm('Are you sure you want to delete this history item?')) return;

        try {
            setDeleteLoading(id);
            await apiClient.delete(`/api/history/${id}`);
            setHistory(prev => prev.filter(item => item.id !== id));
        } catch (error) {
            console.error('Failed to delete history item:', error);
            alert('Failed to delete history item');
        } finally {
            setDeleteLoading(null);
        }
    };

    const getSentimentColor = (sentiment?: string | any) => {
        if (!sentiment) return 'text-slate-400';
        const sentimentStr = typeof sentiment === 'string' ? sentiment : sentiment.classification || '';
        const s = sentimentStr.toLowerCase();
        if (s.includes('bull') || s.includes('positive')) return 'text-emerald-400';
        if (s.includes('bear') || s.includes('negative')) return 'text-red-400';
        return 'text-yellow-400';
    };

    const getSentimentBg = (sentiment?: string | any) => {
        if (!sentiment) return 'bg-slate-500/10 border-slate-500/20';
        const sentimentStr = typeof sentiment === 'string' ? sentiment : sentiment.classification || '';
        const s = sentimentStr.toLowerCase();
        if (s.includes('bull') || s.includes('positive')) return 'bg-emerald-500/10 border-emerald-500/20';
        if (s.includes('bear') || s.includes('negative')) return 'bg-red-500/10 border-red-500/20';
        return 'bg-yellow-500/10 border-yellow-500/20';
    };

    const getSentimentIcon = (sentiment?: string | any) => {
        if (!sentiment) return Minus;
        const sentimentStr = typeof sentiment === 'string' ? sentiment : sentiment.classification || '';
        const s = sentimentStr.toLowerCase();
        if (s.includes('bull') || s.includes('positive')) return TrendingUp;
        if (s.includes('bear') || s.includes('negative')) return TrendingDown;
        return Minus;
    };

    const formatDate = (dateString: string) => {
        const date = new Date(dateString);
        const today = new Date();
        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);

        const isToday = date.toDateString() === today.toDateString();
        const isYesterday = date.toDateString() === yesterday.toDateString();

        const timeStr = date.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit'
        });

        if (isToday) return `Today at ${timeStr}`;
        if (isYesterday) return `Yesterday at ${timeStr}`;

        return date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: date.getFullYear() !== today.getFullYear() ? 'numeric' : undefined
        }) + ` at ${timeStr}`;
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-emerald-950/20 py-8 px-4">
            <div className="max-w-5xl mx-auto">
                {/* Header */}
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mb-8"
                >
                    <div className="flex items-center gap-3 mb-3">
                        <div className="p-3 rounded-xl bg-gradient-to-br from-cyan-500/10 to-blue-500/10 border border-cyan-500/20">
                            <History className="w-6 h-6 text-cyan-400" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-bold text-white">Analysis History</h1>
                            <p className="text-slate-400 text-sm">Track and review your past AI predictions</p>
                        </div>
                    </div>

                    {!isLoading && (
                        <div className="flex items-center gap-2 mt-4">
                            <div className="px-4 py-2 rounded-lg bg-slate-800/50 border border-slate-700/50">
                                <span className="text-slate-400 text-sm">Total Analyses: </span>
                                <span className="text-white font-semibold">{history.length}</span>
                            </div>
                        </div>
                    )}
                </motion.div>

                {/* Loading State */}
                {isLoading && (
                    <div className="space-y-3">
                        {[1, 2, 3, 4, 5].map((i) => (
                            <motion.div
                                key={i}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: i * 0.05 }}
                                className="bg-slate-900/50 backdrop-blur-xl border border-slate-800/50 rounded-xl p-6"
                            >
                                <div className="flex items-center justify-center h-20">
                                    <Loader2 className="w-6 h-6 text-cyan-400 animate-spin" />
                                </div>
                            </motion.div>
                        ))}
                    </div>
                )}

                {/* Empty State */}
                {!isLoading && history.length === 0 && (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="bg-slate-900/50 backdrop-blur-xl border border-slate-800/50 rounded-2xl p-12 text-center"
                    >
                        <div className="max-w-md mx-auto">
                            <div className="p-4 rounded-full bg-slate-800/50 w-20 h-20 mx-auto mb-6 flex items-center justify-center">
                                <History className="w-10 h-10 text-slate-600" />
                            </div>
                            <h3 className="text-xl font-semibold text-white mb-2">No analysis history yet</h3>
                            <p className="text-slate-400 mb-6">
                                Analyze stocks from the dashboard to see them here. Your analysis history will help you track your predictions.
                            </p>
                            <button
                                onClick={() => router.push('/dashboard')}
                                className="px-6 py-3 bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-600 hover:to-cyan-600 text-white font-semibold rounded-xl transition-all shadow-lg shadow-emerald-500/20"
                            >
                                Start Analyzing
                            </button>
                        </div>
                    </motion.div>
                )}

                {/* History List */}
                {!isLoading && history.length > 0 && (
                    <div className="space-y-3">
                        <AnimatePresence>
                            {history.map((item, index) => {
                                const SentimentIcon = getSentimentIcon(item.analysis_data?.sentiment);
                                const confidence = item.analysis_data?.confidence || 0;
                                const sentimentStr = typeof item.analysis_data?.sentiment === 'string'
                                    ? item.analysis_data?.sentiment
                                    : item.analysis_data?.sentiment?.classification || 'Neutral';

                                return (
                                    <motion.div
                                        key={item.id}
                                        initial={{ opacity: 0, y: 20 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        exit={{ opacity: 0, scale: 0.95 }}
                                        transition={{ delay: index * 0.03 }}
                                        className="group bg-slate-900/50 backdrop-blur-xl border border-slate-800/50 hover:border-cyan-500/50 rounded-xl transition-all hover:shadow-lg hover:shadow-cyan-500/5"
                                    >
                                        <div className="p-5">
                                            <div className="flex items-center justify-between gap-4">
                                                {/* Left: Stock Info */}
                                                <div className="flex items-center gap-4 flex-1 min-w-0">
                                                    {/* Ticker Badge */}
                                                    <div className="flex-shrink-0">
                                                        <div className="px-4 py-2 rounded-lg bg-gradient-to-br from-slate-800 to-slate-800/50 border border-slate-700/50">
                                                            <div className="text-lg font-bold text-white">{item.ticker}</div>
                                                        </div>
                                                    </div>

                                                    {/* Details */}
                                                    <div className="flex-1 min-w-0">
                                                        <h3 className="text-sm font-semibold text-white truncate mb-1">{item.name}</h3>
                                                        <div className="flex items-center gap-3 text-xs text-slate-400">
                                                            <div className="flex items-center gap-1.5">
                                                                <Clock className="w-3.5 h-3.5" />
                                                                <span>{formatDate(item.created_at)}</span>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>

                                                {/* Middle: Sentiment & Confidence */}
                                                <div className="flex items-center gap-3 flex-shrink-0">
                                                    {/* Sentiment Badge */}
                                                    {item.analysis_data?.sentiment && (
                                                        <div className={`px-3 py-1.5 rounded-lg border ${getSentimentBg(item.analysis_data.sentiment)} flex items-center gap-1.5`}>
                                                            <SentimentIcon className={`w-4 h-4 ${getSentimentColor(item.analysis_data.sentiment)}`} />
                                                            <span className={`text-xs font-semibold ${getSentimentColor(item.analysis_data.sentiment)}`}>
                                                                {sentimentStr}
                                                            </span>
                                                        </div>
                                                    )}

                                                    {/* Confidence */}
                                                    {confidence > 0 && (
                                                        <div className="px-3 py-1.5 rounded-lg bg-slate-800/50 border border-slate-700/50">
                                                            <span className="text-xs text-slate-400">Confidence: </span>
                                                            <span className="text-xs font-semibold text-white">{confidence}%</span>
                                                        </div>
                                                    )}
                                                </div>

                                                {/* Right: Actions */}
                                                <div className="flex items-center gap-2 flex-shrink-0">
                                                    <button
                                                        onClick={() => handleView(item)}
                                                        className="px-4 py-2 bg-gradient-to-r from-emerald-500/10 to-cyan-500/10 hover:from-emerald-500/20 hover:to-cyan-500/20 text-cyan-400 hover:text-cyan-300 border border-cyan-500/20 hover:border-cyan-500/40 rounded-lg transition-all flex items-center gap-2 text-sm font-medium"
                                                    >
                                                        <Eye className="w-4 h-4" />
                                                        <span className="hidden sm:inline">View</span>
                                                    </button>
                                                    <button
                                                        onClick={() => handleDelete(item.id)}
                                                        disabled={deleteLoading === item.id}
                                                        className="p-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 hover:text-red-300 border border-red-500/20 hover:border-red-500/40 rounded-lg transition-all disabled:opacity-50"
                                                        title="Delete"
                                                    >
                                                        {deleteLoading === item.id ? (
                                                            <Loader2 className="w-4 h-4 animate-spin" />
                                                        ) : (
                                                            <Trash2 className="w-4 h-4" />
                                                        )}
                                                    </button>
                                                </div>
                                            </div>
                                        </div>
                                    </motion.div>
                                );
                            })}
                        </AnimatePresence>
                    </div>
                )}
            </div>
        </div>
    );
}
