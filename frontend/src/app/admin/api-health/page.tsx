'use client';

/**
 * External APIs Page
 * 
 * Real-time monitoring for external API dependencies:
 * - Stock Data APIs (Alpha Vantage, Finnhub, Yahoo, etc.)
 * - News APIs
 * - LLM/AI APIs (OpenAI, Azure)
 * 
 * ALL DATA FROM REAL BACKEND METRICS - NO HARDCODED VALUES
 */

import useSWR from 'swr';
import apiClient from '@/lib/api';
import { Globe, TrendingUp, Newspaper, Brain, Activity, Clock, CheckCircle, XCircle, AlertTriangle, ArrowUp, RefreshCw } from 'lucide-react';
import dynamic from 'next/dynamic';

const Chart = dynamic(() => import('react-apexcharts'), { ssr: false });

// Types matching backend response
interface APIMetric {
    api_key: string;
    name: string;
    provider: string;
    category: 'stock' | 'news' | 'llm';
    calls_24h: number;
    success_count: number;
    failure_count: number;
    success_rate: number;
    avg_latency_ms: number;
    status: 'healthy' | 'degraded' | 'down' | 'unknown';
    last_error: string | null;
    tokens_today?: number;
    cost_today_usd?: number;
}

interface ExternalAPIsResponse {
    stock_apis: APIMetric[];
    news_apis: APIMetric[];
    llm_apis: APIMetric[];
    summary: {
        total_calls_24h: number;
        total_success: number;
        total_failure: number;
        overall_success_rate: number;
        avg_latency_ms: number;
        healthy_apis: number;
        degraded_apis: number;
        down_apis: number;
    };
    ai_stats: {
        total_requests: number;
        total_tokens: number;
        total_cost_usd: number;
        guardrail_rejections: number;
    };
    timestamp: string;
}

const fetcher = (url: string) => apiClient.get(url).then(res => res.data);

// Status badge component
function StatusBadge({ status }: { status: string }) {
    const colors = {
        healthy: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
        degraded: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
        down: 'bg-red-500/10 text-red-400 border-red-500/20',
        unknown: 'bg-slate-500/10 text-slate-400 border-slate-500/20'
    };
    const icons = {
        healthy: <CheckCircle className="w-3 h-3" />,
        degraded: <AlertTriangle className="w-3 h-3" />,
        down: <XCircle className="w-3 h-3" />,
        unknown: <Activity className="w-3 h-3" />
    };
    return (
        <span className={`inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-bold rounded border ${colors[status as keyof typeof colors] || colors.unknown}`}>
            {icons[status as keyof typeof icons] || icons.unknown}
            {status.toUpperCase()}
        </span>
    );
}

// API Row component for tables
function APIRow({ api }: { api: APIMetric }) {
    return (
        <tr className="border-b border-[#1e293b]/50 hover:bg-[#1e293b]/30 text-xs">
            <td className="py-3 px-4">
                <div className="flex items-center gap-2">
                    <span className={`w-1.5 h-1.5 rounded-full ${api.status === 'healthy' ? 'bg-emerald-500' : api.status === 'degraded' ? 'bg-amber-500' : 'bg-red-500'}`}></span>
                    <div>
                        <div className="text-white font-medium">{api.name}</div>
                        <div className="text-slate-500 text-[10px]">{api.provider}</div>
                    </div>
                </div>
            </td>
            <td className="py-3 px-4 text-right font-mono text-white">{api.calls_24h.toLocaleString()}</td>
            <td className="py-3 px-4 text-right">
                <span className="text-emerald-400">{api.success_count}</span>
                <span className="text-slate-500">/</span>
                <span className="text-red-400">{api.failure_count}</span>
            </td>
            <td className="py-3 px-4 text-right">
                <span className={`font-mono ${api.success_rate >= 95 ? 'text-emerald-400' : api.success_rate >= 80 ? 'text-amber-400' : 'text-red-400'}`}>
                    {api.success_rate.toFixed(1)}%
                </span>
            </td>
            <td className="py-3 px-4 text-right font-mono">
                <span className={api.avg_latency_ms > 1000 ? 'text-amber-400' : 'text-white'}>
                    {api.avg_latency_ms.toFixed(0)}ms
                </span>
            </td>
            <td className="py-3 px-4 text-right"><StatusBadge status={api.status} /></td>
        </tr>
    );
}

export default function ExternalAPIsPage() {
    const { data, error, isLoading, mutate } = useSWR<ExternalAPIsResponse>('/admin/dashboard/external-apis', fetcher, {
        refreshInterval: 30000 // Refresh every 30 seconds
    });

    // Combine all APIs for charts
    const allAPIs = [...(data?.stock_apis || []), ...(data?.news_apis || []), ...(data?.llm_apis || [])];
    const apisWithCalls = allAPIs.filter(a => a.calls_24h > 0);

    // Chart configs
    const successRateChartOptions: ApexCharts.ApexOptions = {
        chart: { type: 'radialBar', background: 'transparent' },
        colors: ['#10b981'],
        plotOptions: {
            radialBar: {
                hollow: { size: '70%' },
                dataLabels: {
                    name: { show: true, color: '#64748b', fontSize: '12px' },
                    value: { show: true, color: '#fff', fontSize: '28px', fontWeight: 'bold', formatter: (val) => `${val}%` }
                }
            }
        },
        labels: ['Success Rate']
    };

    const latencyChartOptions: ApexCharts.ApexOptions = {
        chart: { type: 'bar', toolbar: { show: false }, background: 'transparent' },
        theme: { mode: 'dark' },
        plotOptions: { bar: { borderRadius: 4, horizontal: true, barHeight: '70%' } },
        colors: ['#6366f1'],
        grid: { borderColor: '#1e293b' },
        xaxis: {
            categories: apisWithCalls.slice(0, 8).map(a => a.name),
            labels: { style: { colors: '#64748b' } }
        },
        yaxis: { labels: { style: { colors: '#94a3b8', fontSize: '10px' } } },
        dataLabels: { enabled: true, formatter: (val: number) => `${val}ms`, style: { colors: ['#fff'], fontSize: '10px' } },
        tooltip: { theme: 'dark' }
    };

    if (isLoading) {
        return (
            <>
                <header className="h-16 px-8 border-b border-[#1e293b] flex items-center bg-[#020617]">
                    <h1 className="text-xl font-bold text-white flex items-center gap-2"><Globe className="w-5 h-5" />External APIs</h1>
                </header>
                <div className="p-8"><div className="animate-pulse bg-[#0f172a] h-96 rounded-xl"></div></div>
            </>
        );
    }

    const summary = data?.summary || { total_calls_24h: 0, overall_success_rate: 100, avg_latency_ms: 0, healthy_apis: 0, degraded_apis: 0, down_apis: 0 };
    const aiStats = data?.ai_stats || { total_requests: 0, total_tokens: 0, total_cost_usd: 0, guardrail_rejections: 0 };

    return (
        <>
            {/* Header */}
            <header className="h-16 px-8 border-b border-[#1e293b] flex items-center justify-between bg-[#020617]/95 backdrop-blur sticky top-0 z-20">
                <h1 className="text-xl font-bold text-white flex items-center gap-2"><Globe className="w-5 h-5" />External APIs</h1>
                <div className="flex items-center gap-6">
                    <div className="flex items-center gap-2 text-xs">
                        <ArrowUp className="w-4 h-4 text-emerald-400" />
                        <span className="text-slate-400">Uptime:</span>
                        <span className="font-mono text-emerald-400 font-bold">{summary.overall_success_rate.toFixed(1)}%</span>
                    </div>
                    <div className="text-xs text-slate-400">
                        Total Calls: <span className="font-mono text-white">{summary.total_calls_24h.toLocaleString()}</span>
                    </div>
                    <button onClick={() => mutate()} className="p-2 hover:bg-[#1e293b] rounded-lg transition" title="Refresh">
                        <RefreshCw className="w-4 h-4 text-slate-400 hover:text-white" />
                    </button>
                </div>
            </header>

            <div className="flex-1 overflow-y-auto p-8 space-y-6">
                {/* Summary Stats */}
                <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
                    <div className="bg-[#0f172a] border border-[#1e293b] p-4 rounded-xl">
                        <div className="text-xs text-slate-500 uppercase font-bold">Total Calls</div>
                        <div className="text-2xl font-mono text-white mt-1">{summary.total_calls_24h.toLocaleString()}</div>
                    </div>
                    <div className="bg-[#0f172a] border border-emerald-500/20 p-4 rounded-xl">
                        <div className="text-xs text-slate-500 uppercase font-bold">Success Rate</div>
                        <div className="text-2xl font-mono text-emerald-400 mt-1">{summary.overall_success_rate.toFixed(1)}%</div>
                    </div>
                    <div className="bg-[#0f172a] border border-[#1e293b] p-4 rounded-xl">
                        <div className="text-xs text-slate-500 uppercase font-bold">Avg Latency</div>
                        <div className="text-2xl font-mono text-white mt-1">{summary.avg_latency_ms.toFixed(0)}ms</div>
                    </div>
                    <div className="bg-[#0f172a] border border-[#1e293b] p-4 rounded-xl">
                        <div className="text-xs text-slate-500 uppercase font-bold">AI Tokens</div>
                        <div className="text-2xl font-mono text-purple-400 mt-1">{aiStats.total_tokens.toLocaleString()}</div>
                    </div>
                    <div className="bg-[#0f172a] border border-amber-500/20 p-4 rounded-xl">
                        <div className="text-xs text-slate-500 uppercase font-bold">AI Cost</div>
                        <div className="text-2xl font-mono text-amber-400 mt-1">${aiStats.total_cost_usd.toFixed(2)}</div>
                    </div>
                    <div className="bg-[#0f172a] border border-red-500/20 p-4 rounded-xl">
                        <div className="text-xs text-slate-500 uppercase font-bold">Guardrail Blocks</div>
                        <div className="text-2xl font-mono text-red-400 mt-1">{aiStats.guardrail_rejections}</div>
                    </div>
                </div>

                {/* Charts Row */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Success Rate Gauge */}
                    <div className="bg-[#0f172a] border border-[#1e293b] p-6 rounded-xl">
                        <h3 className="font-bold text-white mb-4">Overall Success Rate</h3>
                        <Chart type="radialBar" height={250} options={successRateChartOptions} series={[summary.overall_success_rate]} />
                    </div>

                    {/* Latency by API */}
                    <div className="lg:col-span-2 bg-[#0f172a] border border-[#1e293b] p-6 rounded-xl">
                        <h3 className="font-bold text-white mb-4">API Latency Comparison</h3>
                        {apisWithCalls.length > 0 ? (
                            <Chart type="bar" height={250} options={latencyChartOptions}
                                series={[{ name: 'Latency', data: apisWithCalls.slice(0, 8).map(a => Math.round(a.avg_latency_ms)) }]} />
                        ) : (
                            <div className="h-64 flex items-center justify-center text-slate-500">No API calls recorded yet</div>
                        )}
                    </div>
                </div>

                {/* API Tables */}
                {[
                    { title: 'Stock Data APIs', icon: TrendingUp, apis: data?.stock_apis || [], color: '#10b981' },
                    { title: 'News APIs', icon: Newspaper, apis: data?.news_apis || [], color: '#f59e0b' },
                    { title: 'LLM/AI APIs', icon: Brain, apis: data?.llm_apis || [], color: '#8b5cf6' }
                ].map(({ title, icon: Icon, apis, color }) => (
                    <div key={title} className="bg-[#0f172a] border border-[#1e293b] rounded-xl overflow-hidden">
                        <div className="p-4 border-b border-[#1e293b] flex items-center gap-3">
                            <span className="w-1 h-5 rounded" style={{ backgroundColor: color }}></span>
                            <Icon className="w-4 h-4" style={{ color }} />
                            <h3 className="font-bold text-white">{title}</h3>
                            <span className="ml-auto text-xs text-slate-500">
                                {apis.reduce((s, a) => s + a.calls_24h, 0).toLocaleString()} calls (24h)
                            </span>
                        </div>
                        <table className="w-full text-left">
                            <thead className="bg-[#020617] text-slate-500 uppercase text-[10px] font-bold">
                                <tr>
                                    <th className="py-3 px-4">API Provider</th>
                                    <th className="py-3 px-4 text-right">Calls (24h)</th>
                                    <th className="py-3 px-4 text-right">Success/Fail</th>
                                    <th className="py-3 px-4 text-right">Rate</th>
                                    <th className="py-3 px-4 text-right">Latency</th>
                                    <th className="py-3 px-4 text-right">Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                {apis.length === 0 ? (
                                    <tr><td colSpan={6} className="py-8 text-center text-slate-500">No API calls recorded yet. Make some analysis requests to populate data.</td></tr>
                                ) : (
                                    apis.map((api, i) => <APIRow key={i} api={api} />)
                                )}
                            </tbody>
                        </table>
                    </div>
                ))}

                {/* Note */}
                <div className="text-xs text-slate-500 text-center py-4">
                    Data refreshes every 30 seconds. Metrics are aggregated from the last 24 hours.
                    {data?.timestamp && <span className="ml-2">Last updated: {new Date(data.timestamp).toLocaleTimeString()}</span>}
                </div>
            </div>
        </>
    );
}
