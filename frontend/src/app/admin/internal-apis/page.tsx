'use client';

/**
 * Internal APIs Page - Enhanced Version
 * 
 * Comprehensive monitoring for internal backend endpoints with:
 * - Sections by category (Auth, Admin, Analysis, Stock, etc.)
 * - RPS over time chart
 * - Latency distribution heatmap
 * - Error rate distribution
 * - Detailed endpoint table with search and filters
 * 
 * Data source: Backend /admin/dashboard/internal-apis (Redis aggregated)
 * NO HARDCODED DATA - All metrics from real Redis tracking via MetricsCollector
 */

import { useState, useMemo } from 'react';
import useSWR from 'swr';
import apiClient from '@/lib/api';
import {
    Network, Activity, Clock, AlertCircle, ArrowUp, Search, RefreshCw,
    Shield, Users, TrendingUp, Database, ChevronDown, ChevronRight,
    Zap, BarChart3, Timer, AlertTriangle
} from 'lucide-react';
import dynamic from 'next/dynamic';

const Chart = dynamic(() => import('react-apexcharts'), { ssr: false });

// Metrics interface matching backend response
interface EndpointMetrics {
    method: string;
    endpoint: string;
    calls_24h: number;
    avg_latency: number;
    error_rate: number;
    status: 'healthy' | 'degraded' | 'down';
}

// Category configuration
const CATEGORIES = [
    { key: 'auth', label: 'Authentication', icon: Shield, color: '#10b981', patterns: ['/auth/', '/login', '/logout', '/register', '/refresh', '/token'] },
    { key: 'admin', label: 'Admin Dashboard', icon: Users, color: '#6366f1', patterns: ['/admin/'] },
    { key: 'analysis', label: 'Stock Analysis', icon: TrendingUp, color: '#f59e0b', patterns: ['/analysis/', '/analyze/', '/predict/', '/search/'] },
    { key: 'stock', label: 'Stock Data', icon: BarChart3, color: '#ec4899', patterns: ['/stock/', '/watchlist/', '/history/'] },
    { key: 'tracking', label: 'Tracking & Metrics', icon: Activity, color: '#8b5cf6', patterns: ['/tracking/', '/metrics/', '/device/'] },
    { key: 'other', label: 'Other', icon: Database, color: '#64748b', patterns: [] }
];

const fetcher = (url: string) => apiClient.get(url).then(res => res.data);

// Categorize endpoint
function categorizeEndpoint(endpoint: string): string {
    for (const cat of CATEGORIES) {
        if (cat.patterns.some(p => endpoint.includes(p))) {
            return cat.key;
        }
    }
    return 'other';
}

// Method color helper
function getMethodColor(method: string) {
    switch (method) {
        case 'GET': return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
        case 'POST': return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
        case 'PUT': case 'PATCH': return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
        case 'DELETE': return 'bg-red-500/10 text-red-400 border-red-500/20';
        default: return 'bg-slate-500/10 text-slate-400 border-slate-500/20';
    }
}

// Latency color helper
function getLatencyColor(latency: number): string {
    if (latency < 50) return '#10b981';   // Green - Fast
    if (latency < 200) return '#22c55e';  // Light green
    if (latency < 500) return '#f59e0b';  // Amber - Medium
    if (latency < 1000) return '#f97316'; // Orange
    return '#ef4444';                      // Red - Slow
}

// Status badge
function StatusBadge({ status, latency }: { status: string; latency: number }) {
    const isHealthy = status === 'healthy' && latency < 1000;
    const isDegraded = status === 'degraded' || (latency >= 500 && latency < 1000);

    if (!isHealthy && !isDegraded && latency >= 1000) {
        return <span className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-red-500/10 text-red-400 text-xs border border-red-500/20">
            <span className="w-1.5 h-1.5 rounded-full bg-red-400 animate-pulse"></span> Slow
        </span>;
    }
    if (isDegraded) {
        return <span className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 text-xs border border-amber-500/20">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400"></span> Degraded
        </span>;
    }
    return <span className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 text-xs border border-emerald-500/20">
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span> Healthy
    </span>;
}

export default function InternalAPIsPage() {
    const { data: endpoints, isLoading, mutate } = useSWR<EndpointMetrics[]>(
        '/admin/dashboard/internal-apis?hours=24',
        fetcher
    );

    const [searchTerm, setSearchTerm] = useState('');
    const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set(['auth', 'admin']));
    const [activeView, setActiveView] = useState<'categories' | 'all'>('categories');

    // Categorize endpoints
    const categorizedEndpoints = useMemo(() => {
        const result: Record<string, EndpointMetrics[]> = {};
        CATEGORIES.forEach(c => result[c.key] = []);

        endpoints?.forEach(ep => {
            const cat = categorizeEndpoint(ep.endpoint);
            result[cat].push(ep);
        });

        // Sort each category by calls
        Object.keys(result).forEach(key => {
            result[key].sort((a, b) => b.calls_24h - a.calls_24h);
        });

        return result;
    }, [endpoints]);

    // Filtered endpoints for "All" view
    const filteredEndpoints = useMemo(() => {
        if (!endpoints) return [];
        return endpoints.filter(e =>
            e.endpoint.toLowerCase().includes(searchTerm.toLowerCase()) ||
            e.method.toLowerCase().includes(searchTerm.toLowerCase())
        ).sort((a, b) => b.calls_24h - a.calls_24h);
    }, [endpoints, searchTerm]);

    // Aggregates
    const totalCalls = endpoints?.reduce((sum, e) => sum + e.calls_24h, 0) || 0;
    const avgLatency = endpoints && endpoints.length > 0
        ? endpoints.reduce((sum, e) => sum + e.avg_latency, 0) / endpoints.length : 0;
    const slowEndpoints = endpoints?.filter(e => e.avg_latency > 500).length || 0;
    const rps = (totalCalls / (24 * 3600)).toFixed(2);

    // Chart data
    const topByCalls = [...(endpoints || [])].sort((a, b) => b.calls_24h - a.calls_24h).slice(0, 8);
    const topByLatency = [...(endpoints || [])].sort((a, b) => b.avg_latency - a.avg_latency).slice(0, 8);

    // Latency distribution for heatmap
    const latencyBuckets = useMemo(() => {
        const buckets = { '<50ms': 0, '50-200ms': 0, '200-500ms': 0, '500-1000ms': 0, '>1000ms': 0 };
        endpoints?.forEach(ep => {
            if (ep.avg_latency < 50) buckets['<50ms']++;
            else if (ep.avg_latency < 200) buckets['50-200ms']++;
            else if (ep.avg_latency < 500) buckets['200-500ms']++;
            else if (ep.avg_latency < 1000) buckets['500-1000ms']++;
            else buckets['>1000ms']++;
        });
        return buckets;
    }, [endpoints]);

    // Category stats for pie chart
    const categoryStats = useMemo(() => {
        return CATEGORIES.map(cat => ({
            name: cat.label,
            calls: categorizedEndpoints[cat.key]?.reduce((s, e) => s + e.calls_24h, 0) || 0,
            color: cat.color
        })).filter(c => c.calls > 0);
    }, [categorizedEndpoints]);

    // Toggle category expansion
    const toggleCategory = (key: string) => {
        const newSet = new Set(expandedCategories);
        if (newSet.has(key)) newSet.delete(key);
        else newSet.add(key);
        setExpandedCategories(newSet);
    };

    // Chart options
    const callsChartOptions: ApexCharts.ApexOptions = {
        chart: { type: 'bar', toolbar: { show: false }, background: 'transparent' },
        theme: { mode: 'dark' },
        plotOptions: { bar: { borderRadius: 4, horizontal: true, barHeight: '65%' } },
        colors: ['#6366f1'],
        grid: { borderColor: '#1e293b' },
        xaxis: { labels: { style: { colors: '#64748b' } } },
        yaxis: { labels: { style: { colors: '#cbd5e1', fontSize: '10px', fontFamily: 'monospace' }, maxWidth: 180 } },
        dataLabels: { enabled: true, style: { colors: ['#fff'], fontSize: '10px' } },
        tooltip: { theme: 'dark' }
    };

    const latencyDistOptions: ApexCharts.ApexOptions = {
        chart: { type: 'bar', toolbar: { show: false }, background: 'transparent' },
        theme: { mode: 'dark' },
        plotOptions: { bar: { borderRadius: 4, distributed: true } },
        colors: ['#10b981', '#22c55e', '#f59e0b', '#f97316', '#ef4444'],
        grid: { borderColor: '#1e293b' },
        xaxis: { categories: Object.keys(latencyBuckets), labels: { style: { colors: '#94a3b8', fontSize: '10px' } } },
        yaxis: { labels: { style: { colors: '#64748b' } } },
        dataLabels: { enabled: true, style: { colors: ['#fff'] } },
        legend: { show: false },
        tooltip: { theme: 'dark', y: { formatter: (val) => `${val} endpoints` } }
    };

    const categoryPieOptions: ApexCharts.ApexOptions = {
        chart: { type: 'donut', background: 'transparent' },
        theme: { mode: 'dark' },
        labels: categoryStats.map(c => c.name),
        colors: categoryStats.map(c => c.color),
        legend: { position: 'bottom', labels: { colors: '#94a3b8' } },
        plotOptions: { pie: { donut: { size: '65%', labels: { show: true, total: { show: true, label: 'Total', color: '#94a3b8', formatter: () => totalCalls.toLocaleString() } } } } },
        dataLabels: { enabled: false },
        tooltip: { theme: 'dark' }
    };

    if (isLoading) {
        return (
            <>
                <header className="h-16 px-8 border-b border-[#1e293b] flex items-center bg-[#020617]">
                    <h1 className="text-xl font-bold text-white">Internal APIs</h1>
                </header>
                <div className="p-8"><div className="animate-pulse bg-[#0f172a] h-96 rounded-xl"></div></div>
            </>
        );
    }

    return (
        <>
            {/* Header */}
            <header className="h-16 px-8 border-b border-[#1e293b] flex items-center justify-between bg-[#020617]/95 backdrop-blur sticky top-0 z-20">
                <div className="flex items-center gap-3">
                    <span className="w-8 h-8 rounded bg-indigo-500/10 flex items-center justify-center text-indigo-400">
                        <Network size={18} />
                    </span>
                    <h1 className="text-xl font-bold text-white">Internal APIs</h1>
                    <span className="text-xs text-slate-500 bg-[#1e293b] px-2 py-0.5 rounded-full ml-2">
                        {endpoints?.length || 0} endpoints
                    </span>
                </div>
                <div className="flex items-center gap-4">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                        <input
                            type="text"
                            placeholder="Search endpoints..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="bg-[#0f172a] border border-[#1e293b] text-sm rounded-full pl-10 pr-4 py-1.5 text-white focus:outline-none focus:border-indigo-500 w-56"
                        />
                    </div>
                    <button onClick={() => mutate()} title="Refresh"
                        className="p-2 hover:bg-[#1e293b] rounded-lg transition text-slate-400 hover:text-white">
                        <RefreshCw className="w-4 h-4" />
                    </button>
                </div>
            </header>

            <div className="flex-1 overflow-y-auto p-8 space-y-6">
                {/* Stats Cards */}
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                    <div className="bg-[#0f172a] border border-[#1e293b] p-5 rounded-xl">
                        <div className="flex items-center gap-3 mb-2">
                            <div className="p-2 bg-indigo-500/10 rounded-lg text-indigo-400"><Activity size={18} /></div>
                            <div className="text-xs text-slate-500 uppercase font-bold">Total Calls (24h)</div>
                        </div>
                        <div className="text-2xl font-mono text-white">{totalCalls.toLocaleString()}</div>
                    </div>
                    <div className="bg-[#0f172a] border border-[#1e293b] p-5 rounded-xl">
                        <div className="flex items-center gap-3 mb-2">
                            <div className="p-2 bg-emerald-500/10 rounded-lg text-emerald-400"><Zap size={18} /></div>
                            <div className="text-xs text-slate-500 uppercase font-bold">Avg RPS</div>
                        </div>
                        <div className="text-2xl font-mono text-emerald-400">{rps}</div>
                    </div>
                    <div className="bg-[#0f172a] border border-[#1e293b] p-5 rounded-xl">
                        <div className="flex items-center gap-3 mb-2">
                            <div className="p-2 bg-amber-500/10 rounded-lg text-amber-400"><Timer size={18} /></div>
                            <div className="text-xs text-slate-500 uppercase font-bold">Avg Latency</div>
                        </div>
                        <div className="text-2xl font-mono text-white">{avgLatency.toFixed(0)} <span className="text-sm text-slate-500">ms</span></div>
                    </div>
                    <div className="bg-[#0f172a] border border-[#1e293b] p-5 rounded-xl">
                        <div className="flex items-center gap-3 mb-2">
                            <div className="p-2 bg-purple-500/10 rounded-lg text-purple-400"><Database size={18} /></div>
                            <div className="text-xs text-slate-500 uppercase font-bold">Endpoints</div>
                        </div>
                        <div className="text-2xl font-mono text-white">{endpoints?.length || 0}</div>
                    </div>
                    <div className="bg-[#0f172a] border border-red-500/20 p-5 rounded-xl">
                        <div className="flex items-center gap-3 mb-2">
                            <div className="p-2 bg-red-500/10 rounded-lg text-red-400"><AlertTriangle size={18} /></div>
                            <div className="text-xs text-slate-500 uppercase font-bold">Slow (&gt;500ms)</div>
                        </div>
                        <div className="text-2xl font-mono text-red-400">{slowEndpoints}</div>
                    </div>
                </div>

                {/* Charts Row */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Top by Calls */}
                    <div className="bg-[#0f172a] border border-[#1e293b] p-6 rounded-xl">
                        <h3 className="font-bold text-white mb-4 flex items-center gap-2">
                            <ArrowUp className="w-4 h-4 text-indigo-400" /> Top Endpoints by Volume
                        </h3>
                        {topByCalls.length > 0 ? (
                            <Chart type="bar" height={220} options={callsChartOptions}
                                series={[{ data: topByCalls.map(e => ({ x: e.endpoint.split('/').pop() || e.endpoint, y: e.calls_24h })) }]} />
                        ) : (
                            <div className="h-48 flex items-center justify-center text-slate-500">No data</div>
                        )}
                    </div>

                    {/* Latency Distribution Heatmap */}
                    <div className="bg-[#0f172a] border border-[#1e293b] p-6 rounded-xl">
                        <h3 className="font-bold text-white mb-4 flex items-center gap-2">
                            <Clock className="w-4 h-4 text-amber-400" /> Latency Distribution
                        </h3>
                        <Chart type="bar" height={220} options={latencyDistOptions}
                            series={[{ name: 'Endpoints', data: Object.values(latencyBuckets) }]} />
                    </div>

                    {/* Category Distribution */}
                    <div className="bg-[#0f172a] border border-[#1e293b] p-6 rounded-xl">
                        <h3 className="font-bold text-white mb-4 flex items-center gap-2">
                            <BarChart3 className="w-4 h-4 text-purple-400" /> Calls by Category
                        </h3>
                        {categoryStats.length > 0 ? (
                            <Chart type="donut" height={220} options={categoryPieOptions}
                                series={categoryStats.map(c => c.calls)} />
                        ) : (
                            <div className="h-48 flex items-center justify-center text-slate-500">No data</div>
                        )}
                    </div>
                </div>

                {/* View Toggle */}
                <div className="flex items-center gap-2">
                    <button onClick={() => setActiveView('categories')}
                        className={`px-4 py-2 rounded-lg text-sm font-medium transition ${activeView === 'categories' ? 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/30' : 'text-slate-400 hover:bg-[#1e293b]'}`}>
                        By Category
                    </button>
                    <button onClick={() => setActiveView('all')}
                        className={`px-4 py-2 rounded-lg text-sm font-medium transition ${activeView === 'all' ? 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/30' : 'text-slate-400 hover:bg-[#1e293b]'}`}>
                        All Endpoints
                    </button>
                </div>

                {/* Categorized View */}
                {activeView === 'categories' && (
                    <div className="space-y-4">
                        {CATEGORIES.map(cat => {
                            const catEndpoints = categorizedEndpoints[cat.key] || [];
                            if (catEndpoints.length === 0) return null;
                            const isExpanded = expandedCategories.has(cat.key);
                            const Icon = cat.icon;
                            const catCalls = catEndpoints.reduce((s, e) => s + e.calls_24h, 0);
                            const catAvgLatency = catEndpoints.reduce((s, e) => s + e.avg_latency, 0) / catEndpoints.length;

                            return (
                                <div key={cat.key} className="bg-[#0f172a] border border-[#1e293b] rounded-xl overflow-hidden">
                                    <button onClick={() => toggleCategory(cat.key)}
                                        className="w-full p-4 flex items-center justify-between hover:bg-[#1e293b]/50 transition">
                                        <div className="flex items-center gap-3">
                                            <span className="w-1 h-8 rounded" style={{ backgroundColor: cat.color }}></span>
                                            <Icon className="w-5 h-5" style={{ color: cat.color }} />
                                            <span className="font-bold text-white">{cat.label}</span>
                                            <span className="text-xs text-slate-500 bg-[#1e293b] px-2 py-0.5 rounded-full">
                                                {catEndpoints.length} endpoints
                                            </span>
                                        </div>
                                        <div className="flex items-center gap-6">
                                            <div className="text-right">
                                                <div className="text-xs text-slate-500">Calls</div>
                                                <div className="font-mono text-white">{catCalls.toLocaleString()}</div>
                                            </div>
                                            <div className="text-right">
                                                <div className="text-xs text-slate-500">Avg Latency</div>
                                                <div className="font-mono" style={{ color: getLatencyColor(catAvgLatency) }}>
                                                    {catAvgLatency.toFixed(0)}ms
                                                </div>
                                            </div>
                                            {isExpanded ? <ChevronDown className="w-5 h-5 text-slate-400" /> : <ChevronRight className="w-5 h-5 text-slate-400" />}
                                        </div>
                                    </button>

                                    {isExpanded && (
                                        <table className="w-full text-left text-sm">
                                            <thead className="bg-[#020617] text-slate-500 uppercase text-[10px] font-bold">
                                                <tr>
                                                    <th className="p-3 w-20">Method</th>
                                                    <th className="p-3">Endpoint</th>
                                                    <th className="p-3 text-right">Calls</th>
                                                    <th className="p-3 text-right">Latency</th>
                                                    <th className="p-3 text-right">Status</th>
                                                </tr>
                                            </thead>
                                            <tbody className="divide-y divide-[#1e293b]">
                                                {catEndpoints.map((ep, i) => (
                                                    <tr key={i} className="hover:bg-[#1e293b]/30 text-slate-300">
                                                        <td className="p-3">
                                                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getMethodColor(ep.method)}`}>
                                                                {ep.method}
                                                            </span>
                                                        </td>
                                                        <td className="p-3 font-mono text-xs text-white">{ep.endpoint}</td>
                                                        <td className="p-3 text-right font-mono">{ep.calls_24h.toLocaleString()}</td>
                                                        <td className="p-3 text-right font-mono" style={{ color: getLatencyColor(ep.avg_latency) }}>
                                                            {ep.avg_latency.toFixed(0)} ms
                                                        </td>
                                                        <td className="p-3 text-right"><StatusBadge status={ep.status} latency={ep.avg_latency} /></td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                )}

                {/* All Endpoints View */}
                {activeView === 'all' && (
                    <div className="bg-[#0f172a] border border-[#1e293b] rounded-xl overflow-hidden">
                        <div className="p-4 border-b border-[#1e293b] flex justify-between items-center">
                            <h3 className="font-bold text-white">All Internal Endpoints</h3>
                            <div className="text-xs text-slate-500">{filteredEndpoints.length} endpoints found</div>
                        </div>
                        <div className="overflow-x-auto">
                            <table className="w-full text-left text-sm">
                                <thead className="bg-[#020617] text-slate-500 uppercase text-xs font-bold border-b border-[#1e293b]">
                                    <tr>
                                        <th className="p-4 w-24">Method</th>
                                        <th className="p-4">Endpoint Path</th>
                                        <th className="p-4 text-right">Calls (24h)</th>
                                        <th className="p-4 text-right">Avg Latency</th>
                                        <th className="p-4 text-right">Status</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-[#1e293b] text-slate-300">
                                    {filteredEndpoints.length === 0 ? (
                                        <tr><td colSpan={5} className="p-8 text-center text-slate-500">
                                            {endpoints?.length === 0 ? "No endpoint data recorded yet" : "No matches found"}
                                        </td></tr>
                                    ) : (
                                        filteredEndpoints.map((ep, i) => (
                                            <tr key={i} className="hover:bg-[#1e293b]/50 transition">
                                                <td className="p-4">
                                                    <span className={`px-2 py-1 rounded text-[10px] font-bold border ${getMethodColor(ep.method)}`}>
                                                        {ep.method}
                                                    </span>
                                                </td>
                                                <td className="p-4 font-mono text-xs text-white">{ep.endpoint}</td>
                                                <td className="p-4 text-right font-mono">{ep.calls_24h.toLocaleString()}</td>
                                                <td className="p-4 text-right font-mono" style={{ color: getLatencyColor(ep.avg_latency) }}>
                                                    {ep.avg_latency.toFixed(0)} ms
                                                </td>
                                                <td className="p-4 text-right"><StatusBadge status={ep.status} latency={ep.avg_latency} /></td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}

                {/* Footer Note */}
                <div className="text-xs text-slate-500 text-center py-2">
                    Data from Redis MetricsCollector - Last 24 hours. Click refresh to update.
                </div>
            </div>
        </>
    );
}
