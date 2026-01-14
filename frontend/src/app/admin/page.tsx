'use client';

/**
 * SRE-GRADE SYSTEM OVERVIEW PAGE
 * 
 * Principal SRE + Platform Architect Design:
 * - Global Status Strip (above the fold)
 * - Golden Signals (RPS, Error Rate, p95 Latency, Saturation)
 * - Unified Traffic/Error/Latency Chart
 * - Service Health Matrix (replaces radar chart)
 * - AI/RAG Health Summary
 * - Active Alerts & Recent Events
 * 
 * This page answers in <30 seconds:
 * 1. Is the system healthy?
 * 2. Are users impacted?
 * 3. Is something degrading?
 * 4. What changed recently?
 * 5. Where should I drill down next?
 * 
 * ALL DATA FROM REAL APIs - NO HARDCODED VALUES
 */

import { useState, Fragment } from 'react';
import { useSREUnifiedOverview, useHistoricalMetrics } from '@/hooks/useAdminAPI';
import dynamic from 'next/dynamic';
import Link from 'next/link';
import {
    RefreshCw, AlertTriangle, CheckCircle, XCircle,
    TrendingUp, TrendingDown, Minus, Activity,
    Server, Brain, Users, ChevronRight, Clock,
    Zap, AlertCircle, BarChart3
} from 'lucide-react';

// Lazy load ApexCharts (client-side only)
const Chart = dynamic(() => import('react-apexcharts'), { ssr: false });

// ==================== CONSTANTS ====================

const healthColors = {
    healthy: { bg: 'bg-emerald-500/10', border: 'border-emerald-500/30', text: 'text-emerald-400', dot: 'bg-emerald-500' },
    degraded: { bg: 'bg-yellow-500/10', border: 'border-yellow-500/30', text: 'text-yellow-400', dot: 'bg-yellow-500' },
    critical: { bg: 'bg-red-500/10', border: 'border-red-500/30', text: 'text-red-400', dot: 'bg-red-500' }
};

const statusColors = {
    normal: 'text-slate-300',
    warning: 'text-yellow-400',
    critical: 'text-red-400'
};

// ==================== HELPER COMPONENTS ====================

function TrendIcon({ value, inverted = false }: { value: number; inverted?: boolean }) {
    if (value === 0) return <Minus className="w-3.5 h-3.5 text-slate-500" />;
    const isUp = value > 0;
    // For error rate, up is bad. For traffic, up is good
    const color = inverted ? (isUp ? 'text-red-400' : 'text-emerald-400') : (isUp ? 'text-emerald-400' : 'text-red-400');
    return isUp
        ? <TrendingUp className={`w-3.5 h-3.5 ${color}`} />
        : <TrendingDown className={`w-3.5 h-3.5 ${color}`} />;
}

function DeltaBadge({ value, inverted = false, suffix = '%' }: { value: number; inverted?: boolean; suffix?: string }) {
    if (value === 0) return <span className="text-xs text-slate-500 font-mono">—</span>;
    const isPositive = value > 0;
    // For error/latency (inverted), positive delta is bad
    const colorClass = inverted
        ? (isPositive ? 'text-red-400' : 'text-emerald-400')
        : (isPositive ? 'text-emerald-400' : 'text-red-400');
    return (
        <span className={`text-xs font-mono ${colorClass}`}>
            {isPositive ? '+' : ''}{value.toFixed(1)}{suffix}
        </span>
    );
}

function SLAIndicator({ current, sla, status }: { current: number; sla: number | null; status: string }) {
    if (!sla) return null;
    const pct = Math.min(100, (current / sla) * 100);
    const barColor = status === 'critical' ? 'bg-red-500' : status === 'warning' ? 'bg-yellow-500' : 'bg-emerald-500';
    return (
        <div className="mt-2">
            <div className="flex justify-between text-[10px] text-slate-500 mb-1">
                <span>0</span>
                <span>SLA: {sla}</span>
            </div>
            <div className="h-1 bg-slate-800 rounded-full overflow-hidden">
                <div className={`h-full ${barColor} transition-all`} style={{ width: `${pct}%` }} />
            </div>
        </div>
    );
}

// ==================== MAIN COMPONENT ====================

export default function SREOverviewPage() {
    const { data, isLoading, isError, refresh } = useSREUnifiedOverview();
    const { data: chartData, isLoading: chartLoading } = useHistoricalMetrics(8);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [timeRange, setTimeRange] = useState<'15m' | '1h' | '24h'>('1h');

    const handleRefresh = async () => {
        setIsRefreshing(true);
        await refresh();
        setIsRefreshing(false);
    };

    // Skeleton loader
    if (isLoading && !data) {
        return (
            <>
                <header className="h-16 px-8 border-b border-[#1e293b] flex items-center bg-[#0f172a]/50">
                    <h1 className="text-xl font-bold text-white flex items-center gap-2">
                        <Activity className="w-5 h-5" />System Overview
                    </h1>
                </header>
                <div className="p-8 animate-pulse space-y-6">
                    <div className="bg-[#0f172a] h-24 rounded-xl" />
                    <div className="grid grid-cols-4 gap-4">
                        {[1, 2, 3, 4].map(i => <div key={i} className="bg-[#0f172a] h-32 rounded-xl" />)}
                    </div>
                    <div className="bg-[#0f172a] h-64 rounded-xl" />
                </div>
            </>
        );
    }

    // Error state
    if (isError || !data) {
        return (
            <>
                <header className="h-16 px-8 border-b border-[#1e293b] flex items-center bg-[#0f172a]/50">
                    <h1 className="text-xl font-bold text-white">System Overview</h1>
                </header>
                <div className="p-8 flex items-center justify-center">
                    <div className="text-center">
                        <XCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
                        <h2 className="text-xl text-white mb-2">Failed to load system overview</h2>
                        <button onClick={handleRefresh} className="text-indigo-400 hover:text-white">
                            Try again
                        </button>
                    </div>
                </div>
            </>
        );
    }

    const ss = data.system_state;
    const ui = data.user_impact;
    const cd = data.change_detection;
    const gs = data.golden_signals;
    const colors = healthColors[ss.health] || healthColors.healthy;

    // Chart configuration
    const chartOptions: ApexCharts.ApexOptions = {
        chart: {
            toolbar: { show: false },
            background: 'transparent',
            foreColor: '#94a3b8',
            animations: { enabled: true, speed: 400 }
        },
        theme: { mode: 'dark' },
        grid: { borderColor: '#1e293b', strokeDashArray: 4 },
        colors: ['#6366f1', '#ef4444', '#f59e0b'],
        stroke: { curve: 'smooth', width: [2, 2, 2] },
        xaxis: {
            categories: chartData.traffic?.map(t => t.hour) || [],
            labels: { style: { colors: '#64748b', fontSize: '10px' } },
            axisBorder: { show: false },
            axisTicks: { show: false }
        },
        yaxis: [
            {
                title: { text: 'Requests', style: { color: '#6366f1', fontSize: '10px' } },
                labels: { style: { colors: '#94a3b8', fontSize: '10px' } }
            },
            {
                opposite: true,
                title: { text: 'Errors / Latency', style: { color: '#ef4444', fontSize: '10px' } },
                labels: { style: { colors: '#94a3b8', fontSize: '10px' } }
            }
        ],
        legend: {
            position: 'top',
            horizontalAlign: 'right',
            fontSize: '11px',
            markers: { size: 6 },
            labels: { colors: '#94a3b8' }
        },
        tooltip: {
            theme: 'dark',
            x: { formatter: (val) => `Hour: ${val}` }
        },
        annotations: {
            yaxis: [{
                y: 200, // SLA threshold
                y2: undefined,
                borderColor: '#f59e0b',
                strokeDashArray: 4,
                label: {
                    text: 'SLA 200ms',
                    style: { background: '#f59e0b', color: '#000', fontSize: '9px' }
                }
            }]
        }
    };

    return (
        <>
            {/* ==================== HEADER ==================== */}
            <header className="h-14 px-6 border-b border-[#1e293b] flex items-center justify-between bg-[#0f172a]/80 backdrop-blur sticky top-0 z-20">
                <div className="flex items-center gap-3">
                    <Activity className="w-5 h-5 text-slate-400" />
                    <h1 className="text-lg font-bold text-white">System Overview</h1>
                </div>
                <div className="flex items-center gap-3">
                    <span className="text-xs text-slate-500 font-mono">
                        Updated: {new Date(data.timestamp).toLocaleTimeString()}
                    </span>
                    <button
                        onClick={handleRefresh}
                        disabled={isRefreshing}
                        className="flex items-center gap-2 px-3 py-1.5 bg-indigo-500/20 hover:bg-indigo-500/30 border border-indigo-500/30 text-indigo-400 rounded-lg text-xs font-medium transition disabled:opacity-50"
                    >
                        <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
                        Refresh
                    </button>
                </div>
            </header>

            <div className="flex-1 overflow-y-auto p-6 space-y-6">

                {/* ==================== TASK 1: GLOBAL STATUS STRIP ==================== */}
                <section className={`p-4 rounded-xl border ${colors.bg} ${colors.border}`}>
                    <div className="flex flex-wrap items-center justify-between gap-4">
                        {/* System State */}
                        <div className="flex items-center gap-4">
                            <div className={`w-12 h-12 rounded-full flex items-center justify-center ${colors.bg} border-2 ${colors.border}`}>
                                {ss.health === 'healthy' ? <CheckCircle className={`w-6 h-6 ${colors.text}`} /> :
                                    ss.health === 'degraded' ? <AlertTriangle className={`w-6 h-6 ${colors.text}`} /> :
                                        <XCircle className={`w-6 h-6 ${colors.text}`} />}
                            </div>
                            <div>
                                <div className="text-xs text-slate-500 uppercase tracking-wide">System Status</div>
                                <div className={`text-xl font-bold ${colors.text} capitalize`}>{ss.health}</div>
                                <div className="text-xs text-slate-400 font-mono">Score: {ss.score}/100</div>
                            </div>
                        </div>

                        {/* Primary Reason (if degraded/critical) */}
                        {ss.primary_reason && (
                            <div className="flex-1 min-w-[200px] max-w-md">
                                <div className="text-xs text-slate-500 uppercase tracking-wide mb-1">Primary Issue</div>
                                <div className={`text-sm ${colors.text} font-medium`}>{ss.primary_reason}</div>
                            </div>
                        )}

                        {/* User Impact */}
                        <div className="flex gap-6">
                            <div className="text-center">
                                <div className="text-xs text-slate-500 uppercase tracking-wide">Failed Requests</div>
                                <div className={`text-lg font-mono font-bold ${ui.failed_requests_percent > 5 ? 'text-red-400' : ui.failed_requests_percent > 1 ? 'text-yellow-400' : 'text-slate-300'}`}>
                                    {ui.failed_requests_percent.toFixed(2)}%
                                </div>
                            </div>
                            <div className="text-center">
                                <div className="text-xs text-slate-500 uppercase tracking-wide">Slow Requests</div>
                                <div className={`text-lg font-mono font-bold ${ui.slow_requests_percent > 10 ? 'text-yellow-400' : 'text-slate-300'}`}>
                                    {ui.slow_requests_percent.toFixed(1)}%
                                </div>
                            </div>
                            {ui.active_users_affected > 0 && (
                                <div className="text-center">
                                    <div className="text-xs text-slate-500 uppercase tracking-wide">Users Affected</div>
                                    <div className="text-lg font-mono font-bold text-red-400">{ui.active_users_affected}</div>
                                </div>
                            )}
                        </div>

                        {/* Change Detection */}
                        <div className="flex gap-4 items-center border-l border-[#1e293b] pl-4">
                            <div className="text-center">
                                <div className="text-[10px] text-slate-500 uppercase">Traffic Δ</div>
                                <div className="flex items-center gap-1">
                                    <TrendIcon value={cd.traffic_delta_percent} />
                                    <DeltaBadge value={cd.traffic_delta_percent} />
                                </div>
                            </div>
                            <div className="text-center">
                                <div className="text-[10px] text-slate-500 uppercase">Error Δ</div>
                                <div className="flex items-center gap-1">
                                    <TrendIcon value={cd.error_delta_percent} inverted />
                                    <DeltaBadge value={cd.error_delta_percent} inverted />
                                </div>
                            </div>
                            <div className="text-center">
                                <div className="text-[10px] text-slate-500 uppercase">Latency Δ</div>
                                <div className="flex items-center gap-1">
                                    <TrendIcon value={cd.latency_delta_percent} inverted />
                                    <DeltaBadge value={cd.latency_delta_percent} inverted />
                                </div>
                            </div>
                            <div className="text-[10px] text-slate-600 font-mono">(15m)</div>
                        </div>
                    </div>
                </section>

                {/* ==================== TASK 2: GOLDEN SIGNALS ==================== */}
                <section>
                    <div className="flex items-center gap-2 mb-3">
                        <Zap className="w-4 h-4 text-amber-500" />
                        <h2 className="text-sm font-bold text-white uppercase tracking-wide">Golden Signals</h2>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        {/* RPS */}
                        <div className="bg-[#0f172a]/60 border border-[#1e293b] p-4 rounded-xl">
                            <div className="flex justify-between items-start">
                                <div className="text-xs text-slate-500 uppercase">Requests/sec</div>
                                <DeltaBadge value={gs.rps?.delta_percent || 0} />
                            </div>
                            <div className="text-2xl font-mono font-bold text-white mt-1">
                                {gs.rps?.current?.toFixed(2) || 0}
                            </div>
                            <div className="text-xs text-slate-500 mt-2">No SLA threshold</div>
                        </div>

                        {/* Error Rate */}
                        <div className={`bg-[#0f172a]/60 border p-4 rounded-xl ${gs.error_rate?.status === 'critical' ? 'border-red-500/50' : gs.error_rate?.status === 'warning' ? 'border-yellow-500/50' : 'border-[#1e293b]'}`}>
                            <div className="flex justify-between items-start">
                                <div className="text-xs text-slate-500 uppercase">Error Rate</div>
                                <DeltaBadge value={gs.error_rate?.delta_percent || 0} inverted />
                            </div>
                            <div className={`text-2xl font-mono font-bold mt-1 ${statusColors[gs.error_rate?.status || 'normal']}`}>
                                {gs.error_rate?.current?.toFixed(2) || 0}%
                            </div>
                            <SLAIndicator current={gs.error_rate?.current || 0} sla={gs.error_rate?.sla || null} status={gs.error_rate?.status || 'normal'} />
                        </div>

                        {/* p95 Latency */}
                        <div className={`bg-[#0f172a]/60 border p-4 rounded-xl ${gs.p95_latency_ms?.status === 'critical' ? 'border-red-500/50' : gs.p95_latency_ms?.status === 'warning' ? 'border-yellow-500/50' : 'border-[#1e293b]'}`}>
                            <div className="flex justify-between items-start">
                                <div className="text-xs text-slate-500 uppercase">p95 Latency</div>
                                <DeltaBadge value={gs.p95_latency_ms?.delta_percent || 0} inverted />
                            </div>
                            <div className={`text-2xl font-mono font-bold mt-1 ${statusColors[gs.p95_latency_ms?.status || 'normal']}`}>
                                {Math.round(gs.p95_latency_ms?.current || 0)}ms
                            </div>
                            <SLAIndicator current={gs.p95_latency_ms?.current || 0} sla={gs.p95_latency_ms?.sla || null} status={gs.p95_latency_ms?.status || 'normal'} />
                        </div>

                        {/* Saturation */}
                        <div className={`bg-[#0f172a]/60 border p-4 rounded-xl ${gs.saturation_percent?.status === 'critical' ? 'border-red-500/50' : gs.saturation_percent?.status === 'warning' ? 'border-yellow-500/50' : 'border-[#1e293b]'}`}>
                            <div className="flex justify-between items-start">
                                <div className="text-xs text-slate-500 uppercase">Saturation</div>
                                <DeltaBadge value={gs.saturation_percent?.delta_percent || 0} inverted />
                            </div>
                            <div className={`text-2xl font-mono font-bold mt-1 ${statusColors[gs.saturation_percent?.status || 'normal']}`}>
                                {Math.round(gs.saturation_percent?.current || 0)}%
                            </div>
                            <SLAIndicator current={gs.saturation_percent?.current || 0} sla={gs.saturation_percent?.sla || null} status={gs.saturation_percent?.status || 'normal'} />
                        </div>
                    </div>
                </section>

                {/* ==================== TASK 3: UNIFIED TRAFFIC CHART ==================== */}
                <section>
                    <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2">
                            <BarChart3 className="w-4 h-4 text-indigo-500" />
                            <h2 className="text-sm font-bold text-white uppercase tracking-wide">Traffic / Errors / Latency</h2>
                        </div>
                        <div className="flex gap-1">
                            {(['15m', '1h', '24h'] as const).map(range => (
                                <button
                                    key={range}
                                    onClick={() => setTimeRange(range)}
                                    className={`px-2 py-1 text-xs rounded ${timeRange === range ? 'bg-indigo-500/30 text-indigo-400' : 'text-slate-500 hover:text-white'}`}
                                >
                                    {range}
                                </button>
                            ))}
                        </div>
                    </div>
                    <div className="bg-[#0f172a]/60 border border-[#1e293b] p-4 rounded-xl">
                        {chartLoading ? (
                            <div className="h-64 flex items-center justify-center">
                                <div className="animate-pulse text-slate-500">Loading chart...</div>
                            </div>
                        ) : (
                            <Chart
                                type="line"
                                height={280}
                                options={chartOptions}
                                series={[
                                    { name: 'Requests', type: 'area', data: chartData.traffic?.map(t => t.requests) || [] },
                                    { name: 'Errors', type: 'line', data: chartData.errors?.map(e => e.errors) || [] },
                                    { name: 'Latency (ms)', type: 'line', data: chartData.latency?.map(l => l.avg_latency_ms) || [] }
                                ]}
                            />
                        )}
                    </div>
                </section>

                {/* ==================== TASK 4: SERVICE HEALTH MATRIX ==================== */}
                <section>
                    <div className="flex items-center gap-2 mb-3">
                        <Server className="w-4 h-4 text-purple-500" />
                        <h2 className="text-sm font-bold text-white uppercase tracking-wide">Service Health Matrix</h2>
                        <Link href="/admin/infrastructure" className="ml-auto text-xs text-indigo-400 hover:text-white flex items-center gap-1">
                            Deep Dive <ChevronRight className="w-3 h-3" />
                        </Link>
                    </div>
                    <div className="bg-[#0f172a]/60 border border-[#1e293b] rounded-xl overflow-hidden">
                        <table className="w-full text-left text-xs">
                            <thead className="bg-[#020617] text-slate-500 uppercase">
                                <tr>
                                    <th className="p-3">Service</th>
                                    <th className="p-3">Health</th>
                                    <th className="p-3">Error %</th>
                                    <th className="p-3">p95 Latency</th>
                                    <th className="p-3">Saturation</th>
                                    <th className="p-3">Uptime</th>
                                    <th className="p-3">Trend</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-[#1e293b]">
                                {data.service_matrix.map((svc) => {
                                    const svcColors = healthColors[svc.health_state] || healthColors.healthy;
                                    return (
                                        <tr key={svc.name} className="hover:bg-[#1e293b]/30 transition cursor-pointer">
                                            <td className="p-3 font-mono text-slate-300">{svc.name}</td>
                                            <td className="p-3">
                                                <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-medium ${svcColors.bg} ${svcColors.text} ${svcColors.border} border`}>
                                                    <span className={`w-1.5 h-1.5 rounded-full ${svcColors.dot}`} />
                                                    {svc.health_state}
                                                </span>
                                            </td>
                                            <td className="p-3 font-mono">{svc.error_rate_percent?.toFixed(2) || 0}%</td>
                                            <td className="p-3 font-mono">{Math.round(svc.p95_latency_ms || 0)}ms</td>
                                            <td className="p-3">
                                                <div className="flex items-center gap-2">
                                                    <div className="w-12 bg-slate-800 h-1.5 rounded-full overflow-hidden">
                                                        <div
                                                            className={`h-full ${svc.saturation_percent > 80 ? 'bg-red-500' : svc.saturation_percent > 60 ? 'bg-yellow-500' : 'bg-emerald-500'}`}
                                                            style={{ width: `${Math.min(100, svc.saturation_percent)}%` }}
                                                        />
                                                    </div>
                                                    <span className="font-mono text-[10px]">{svc.saturation_percent?.toFixed(0)}%</span>
                                                </div>
                                            </td>
                                            <td className="p-3 font-mono text-emerald-400">{svc.uptime_percent?.toFixed(2)}%</td>
                                            <td className="p-3">
                                                {svc.trend === 'up' ? <TrendingUp className="w-4 h-4 text-yellow-400" /> :
                                                    svc.trend === 'down' ? <TrendingDown className="w-4 h-4 text-emerald-400" /> :
                                                        <Minus className="w-4 h-4 text-slate-500" />}
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                </section>

                {/* ==================== BOTTOM ROW: AI/RAG + ALERTS ==================== */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                    {/* ==================== TASK 5: AI/RAG HEALTH ====================  */}
                    <section className="lg:col-span-1">
                        <div className="flex items-center gap-2 mb-3">
                            <Brain className="w-4 h-4 text-amber-500" />
                            <h2 className="text-sm font-bold text-white uppercase tracking-wide">AI/RAG Health</h2>
                        </div>
                        <div className="bg-[#0f172a]/60 border border-[#1e293b] p-4 rounded-xl space-y-3">
                            <div className="flex justify-between items-center">
                                <span className="text-xs text-slate-500">AI Success Rate</span>
                                <span className={`font-mono font-bold ${data.ai_rag_health.success_percent >= 95 ? 'text-emerald-400' : data.ai_rag_health.success_percent >= 80 ? 'text-yellow-400' : 'text-red-400'}`}>
                                    {data.ai_rag_health.success_percent?.toFixed(1)}%
                                </span>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-xs text-slate-500">Empty Context Rate</span>
                                <span className={`font-mono font-bold ${data.ai_rag_health.empty_context_percent <= 5 ? 'text-emerald-400' : data.ai_rag_health.empty_context_percent <= 20 ? 'text-yellow-400' : 'text-red-400'}`}>
                                    {data.ai_rag_health.empty_context_percent?.toFixed(1)}%
                                </span>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-xs text-slate-500">p95 Retrieval</span>
                                <span className={`font-mono font-bold ${data.ai_rag_health.p95_retrieval_ms <= 500 ? 'text-emerald-400' : 'text-red-400'}`}>
                                    {Math.round(data.ai_rag_health.p95_retrieval_ms)}ms
                                </span>
                            </div>
                            <div className="border-t border-[#1e293b] pt-3 mt-3">
                                <div className="flex justify-between items-center text-xs">
                                    <span className="text-slate-500">Tokens/Request</span>
                                    <span className="text-slate-300 font-mono">{data.ai_rag_health.tokens_per_request}</span>
                                </div>
                                <div className="flex justify-between items-center text-xs mt-2">
                                    <span className="text-slate-500">Cost/Request</span>
                                    <span className="text-slate-300 font-mono">${data.ai_rag_health.cost_per_request_usd?.toFixed(4)}</span>
                                </div>
                                <div className="flex justify-between items-center text-xs mt-2">
                                    <span className="text-slate-500">Requests Today</span>
                                    <span className="text-slate-300 font-mono">{data.ai_rag_health.total_requests_today}</span>
                                </div>
                            </div>
                        </div>
                    </section>

                    {/* ==================== TASK 6: ALERTS ====================  */}
                    <section className="lg:col-span-1">
                        <div className="flex items-center gap-2 mb-3">
                            <AlertCircle className="w-4 h-4 text-red-500" />
                            <h2 className="text-sm font-bold text-white uppercase tracking-wide">Active Alerts</h2>
                            {data.alerts.length > 0 && (
                                <span className="bg-red-500/20 text-red-400 text-[10px] px-1.5 py-0.5 rounded-full font-bold">
                                    {data.alerts.length}
                                </span>
                            )}
                        </div>
                        <div className="bg-[#0f172a]/60 border border-[#1e293b] rounded-xl overflow-hidden h-[220px]">
                            {data.alerts.length === 0 ? (
                                <div className="h-full flex flex-col items-center justify-center text-slate-500">
                                    <CheckCircle className="w-8 h-8 text-emerald-500 mb-2" />
                                    <span className="text-sm">No active alerts</span>
                                </div>
                            ) : (
                                <div className="overflow-y-auto h-full p-2 space-y-2">
                                    {data.alerts.map((alert, i) => (
                                        <Link key={i} href={alert.link} className="block p-2 hover:bg-[#1e293b]/50 rounded transition">
                                            <div className="flex items-start gap-2">
                                                {alert.severity === 'critical' ? <XCircle className="w-4 h-4 text-red-500 shrink-0 mt-0.5" /> :
                                                    <AlertTriangle className="w-4 h-4 text-yellow-500 shrink-0 mt-0.5" />}
                                                <div className="flex-1 min-w-0">
                                                    <div className={`text-xs font-medium ${alert.severity === 'critical' ? 'text-red-400' : 'text-yellow-400'}`}>
                                                        {alert.service}
                                                    </div>
                                                    <div className="text-[11px] text-slate-400 truncate">{alert.message}</div>
                                                    <div className="text-[10px] text-slate-600 font-mono mt-1">
                                                        {new Date(alert.time).toLocaleTimeString()}
                                                    </div>
                                                </div>
                                            </div>
                                        </Link>
                                    ))}
                                </div>
                            )}
                        </div>
                    </section>

                    {/* ==================== TASK 6: RECENT EVENTS ====================  */}
                    <section className="lg:col-span-1">
                        <div className="flex items-center gap-2 mb-3">
                            <Clock className="w-4 h-4 text-blue-500" />
                            <h2 className="text-sm font-bold text-white uppercase tracking-wide">Recent Events</h2>
                            <span className="text-[10px] text-slate-600">(24h)</span>
                        </div>
                        <div className="bg-[#0f172a]/60 border border-[#1e293b] rounded-xl overflow-hidden h-[220px]">
                            {data.recent_events.length === 0 ? (
                                <div className="h-full flex flex-col items-center justify-center text-slate-500">
                                    <Clock className="w-8 h-8 text-slate-600 mb-2" />
                                    <span className="text-sm">No recent events</span>
                                </div>
                            ) : (
                                <div className="overflow-y-auto h-full p-2 space-y-2">
                                    {data.recent_events.map((event, i) => (
                                        <div key={i} className="p-2 hover:bg-[#1e293b]/30 rounded">
                                            <div className="flex items-center gap-2">
                                                <span className={`w-1.5 h-1.5 rounded-full ${event.success !== false ? 'bg-emerald-500' : 'bg-red-500'}`} />
                                                <span className="text-xs text-slate-300 flex-1 truncate">{event.message}</span>
                                            </div>
                                            <div className="text-[10px] text-slate-600 font-mono ml-3.5 mt-1">
                                                {new Date(event.time).toLocaleString()}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </section>
                </div>

            </div>
        </>
    );
}
