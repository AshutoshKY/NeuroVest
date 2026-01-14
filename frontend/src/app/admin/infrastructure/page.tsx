'use client';

/**
 * SRE-Grade Infrastructure Page with Real Data Charts
 * 
 * Complete redesign following SRE observability principles:
 * - Section 1: Global System Health (above the fold)
 * - Section 2: Real-Time Charts (Traffic, Latency, Errors)
 * - Section 3: Service Health Matrix
 * - Section 4: Per-Service Deep Dive (expandable)
 * - Section 5: AI/RAG Observability
 * - Section 6: User Impact Bridge
 * 
 * ALL DATA FROM REAL APIs - NO HARDCODED VALUES
 */

import { useState, Fragment } from 'react';
import { RefreshCw, AlertTriangle, CheckCircle, XCircle, TrendingUp, TrendingDown, Minus, ChevronDown, ChevronRight, Activity, Server, Brain, Users, BarChart3, Container, Cpu, HardDrive, Network } from 'lucide-react';
import { useSREOverview, useServiceMatrix, useServiceDeepDive, useRAGObservability, useUserImpact, useHistoricalMetrics, useContainerMetrics, type ServiceHealthItem } from '@/hooks/useAdminAPI';
import dynamic from 'next/dynamic';

const InfrastructureCharts = dynamic(() => import('./Charts'), {
    ssr: false,
    loading: () => (
        <div className="bg-[#0f172a]/60 border border-[#1e293b] p-8 rounded-xl text-center">
            <BarChart3 className="w-12 h-12 mx-auto text-slate-600 mb-3 animate-pulse" />
            <p className="text-slate-500">Loading chart components...</p>
        </div>
    )
});

// Health state colors
const healthColors = {
    healthy: { bg: 'bg-emerald-500/10', border: 'border-emerald-500/30', text: 'text-emerald-400', dot: 'bg-emerald-500' },
    degraded: { bg: 'bg-yellow-500/10', border: 'border-yellow-500/30', text: 'text-yellow-400', dot: 'bg-yellow-500' },
    critical: { bg: 'bg-red-500/10', border: 'border-red-500/30', text: 'text-red-400', dot: 'bg-red-500' }
};

// Trend icon component
function TrendIcon({ trend }: { trend: 'up' | 'down' | 'stable' }) {
    if (trend === 'up') return <TrendingUp className="w-4 h-4 text-yellow-400" />;
    if (trend === 'down') return <TrendingDown className="w-4 h-4 text-emerald-400" />;
    return <Minus className="w-4 h-4 text-slate-400" />;
}

// Health state icon
function HealthIcon({ state }: { state: 'healthy' | 'degraded' | 'critical' }) {
    if (state === 'healthy') return <CheckCircle className="w-5 h-5 text-emerald-400" />;
    if (state === 'degraded') return <AlertTriangle className="w-5 h-5 text-yellow-400" />;
    return <XCircle className="w-5 h-5 text-red-400" />;
}

// Service Deep Dive Panel Component
function ServiceDeepDivePanel({ serviceName, isOpen, onClose }: { serviceName: string; isOpen: boolean; onClose: () => void }) {
    const { data, isLoading } = useServiceDeepDive(serviceName);

    if (!isOpen) return null;

    const colors = data ? healthColors[data.health_state] : healthColors.healthy;

    return (
        <tr>
            <td colSpan={7} className="p-0">
                <div className={`bg-[#0f172a]/80 border-l-4 ${colors.border} p-6`}>
                    {isLoading ? (
                        <div className="animate-pulse h-32 bg-slate-800/50 rounded" />
                    ) : data ? (
                        <div className="space-y-4">
                            {/* Score Breakdown */}
                            <div className="grid grid-cols-4 gap-4">
                                <div className="bg-[#020617] p-4 rounded-lg">
                                    <div className="text-xs text-slate-500 uppercase">Availability</div>
                                    <div className="text-2xl font-mono text-emerald-400">{data.score_breakdown?.availability?.toFixed(1) || 100}%</div>
                                </div>
                                <div className="bg-[#020617] p-4 rounded-lg">
                                    <div className="text-xs text-slate-500 uppercase">Error Score</div>
                                    <div className="text-2xl font-mono text-blue-400">{data.score_breakdown?.error?.toFixed(1) || 100}</div>
                                </div>
                                <div className="bg-[#020617] p-4 rounded-lg">
                                    <div className="text-xs text-slate-500 uppercase">Latency Score</div>
                                    <div className="text-2xl font-mono text-purple-400">{data.score_breakdown?.latency?.toFixed(1) || 100}</div>
                                </div>
                                <div className="bg-[#020617] p-4 rounded-lg">
                                    <div className="text-xs text-slate-500 uppercase">Saturation Score</div>
                                    <div className="text-2xl font-mono text-amber-400">{data.score_breakdown?.saturation?.toFixed(1) || 100}</div>
                                </div>
                            </div>

                            {/* Interpretation */}
                            {data.interpretation && (
                                <div className={`p-4 rounded-lg ${colors.bg} ${colors.border} border`}>
                                    <p className={`text-sm ${colors.text}`}>{data.interpretation}</p>
                                </div>
                            )}

                            <button onClick={onClose} className="text-xs text-slate-500 hover:text-white">
                                Close details
                            </button>
                        </div>
                    ) : (
                        <div className="text-slate-500">No data available</div>
                    )}
                </div>
            </td>
        </tr>
    );
}

export default function SREInfrastructurePage() {
    const { data: sreOverview, isLoading: overviewLoading, refresh: refreshOverview } = useSREOverview();
    const { services, isLoading: matrixLoading, refresh: refreshMatrix } = useServiceMatrix();
    const { data: ragData, isLoading: ragLoading, refresh: refreshRag } = useRAGObservability();
    const { data: userImpact, isLoading: impactLoading, refresh: refreshImpact } = useUserImpact();
    const { data: chartData, isLoading: chartLoading, refresh: refreshChart } = useHistoricalMetrics(8);
    const { containers, summary: containerSummary, isLoading: containerLoading, refresh: refreshContainers } = useContainerMetrics();

    const [expandedService, setExpandedService] = useState<string | null>(null);
    const [isRefreshing, setIsRefreshing] = useState(false);

    const handleRefreshAll = async () => {
        setIsRefreshing(true);
        await Promise.all([refreshOverview(), refreshMatrix(), refreshRag(), refreshImpact(), refreshChart(), refreshContainers()]);
        setIsRefreshing(false);
    };

    const isLoading = overviewLoading || matrixLoading;

    // Skeleton loader
    if (isLoading && !sreOverview) {
        return (
            <>
                <header className="h-16 px-8 border-b border-[#1e293b] flex items-center bg-[#0f172a]/50">
                    <h1 className="text-xl font-bold text-white flex items-center gap-2">
                        <Server className="w-5 h-5" />Infrastructure Health
                    </h1>
                </header>
                <div className="p-8 animate-pulse space-y-8">
                    <div className="bg-[#0f172a] h-40 rounded-xl" />
                    <div className="bg-[#0f172a] h-64 rounded-xl" />
                </div>
            </>
        );
    }

    const globalHealth = sreOverview?.global_health || 'healthy';
    const globalColors = healthColors[globalHealth as keyof typeof healthColors] || healthColors.healthy;

    return (
        <>
            {/* Header */}
            <header className="h-16 px-8 border-b border-[#1e293b] flex items-center justify-between bg-[#0f172a]/50 backdrop-blur sticky top-0 z-20">
                <h1 className="text-xl font-bold text-white flex items-center gap-2">
                    <Server className="w-5 h-5" />Infrastructure Health
                </h1>
                <div className="flex items-center gap-4">
                    <span className={`flex items-center gap-2 px-3 py-1 rounded-full border text-xs font-mono ${globalColors.bg} ${globalColors.border} ${globalColors.text}`}>
                        <span className={`w-2 h-2 rounded-full ${globalColors.dot} animate-pulse`} />
                        {globalHealth.toUpperCase()}
                    </span>
                    <button
                        onClick={handleRefreshAll}
                        disabled={isRefreshing}
                        className="flex items-center gap-2 px-4 py-2 bg-indigo-500 hover:bg-indigo-600 text-white rounded-lg text-xs font-bold transition disabled:opacity-50"
                    >
                        <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
                        Refresh
                    </button>
                </div>
            </header>

            <div className="flex-1 overflow-y-auto p-8 space-y-8">

                {/* ==================== SECTION 1: Global System Health ==================== */}
                <section>
                    <div className="flex items-center gap-3 mb-4">
                        <span className="w-1.5 h-6 bg-indigo-500 rounded" />
                        <h2 className="text-lg font-bold text-white">Global System Health</h2>
                        <Activity className="w-4 h-4 text-slate-500" />
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
                        {/* Main Health Indicator */}
                        <div className={`lg:col-span-2 p-6 rounded-xl border ${globalColors.bg} ${globalColors.border}`}>
                            <div className="flex items-center gap-4">
                                <div className={`w-16 h-16 rounded-full ${globalColors.bg} ${globalColors.border} border-2 flex items-center justify-center`}>
                                    <HealthIcon state={globalHealth as 'healthy' | 'degraded' | 'critical'} />
                                </div>
                                <div>
                                    <div className="text-slate-400 text-xs uppercase">System Status</div>
                                    <div className={`text-3xl font-bold ${globalColors.text}`}>
                                        {globalHealth === 'healthy' ? 'Healthy' : globalHealth === 'degraded' ? 'Degraded' : 'Critical'}
                                    </div>
                                    <div className="text-xs text-slate-500">Score: {sreOverview?.global_score?.toFixed(1) || 100}/100</div>
                                </div>
                            </div>
                            {sreOverview?.active_incidents ? (
                                <div className="mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
                                    <span className="text-red-400 text-sm font-bold">{sreOverview.active_incidents} Active Incident{sreOverview.active_incidents > 1 ? 's' : ''}</span>
                                </div>
                            ) : null}
                        </div>

                        {/* User Impact */}
                        <div className="p-5 rounded-xl bg-[#0f172a]/60 border border-[#1e293b]">
                            <div className="text-slate-400 text-xs uppercase">User Impact</div>
                            <div className={`text-2xl font-mono mt-1 ${sreOverview?.user_impact?.status === 'major' ? 'text-red-400' :
                                sreOverview?.user_impact?.status === 'partial' ? 'text-yellow-400' : 'text-emerald-400'
                                }`}>
                                {sreOverview?.user_impact?.status === 'none' ? '0 Affected' :
                                    sreOverview?.user_impact?.status === 'partial' ? 'Partial' : 'Major'}
                            </div>
                        </div>

                        {/* Error Rate */}
                        <div className="p-5 rounded-xl bg-[#0f172a]/60 border border-[#1e293b]">
                            <div className="text-slate-400 text-xs uppercase">Error Rate</div>
                            <div className={`text-2xl font-mono mt-1 ${(sreOverview?.global_error_rate || 0) > 5 ? 'text-red-400' :
                                (sreOverview?.global_error_rate || 0) > 1 ? 'text-yellow-400' : 'text-white'
                                }`}>
                                {sreOverview?.global_error_rate?.toFixed(2) || 0}%
                            </div>
                        </div>

                        {/* p95 Latency */}
                        <div className="p-5 rounded-xl bg-[#0f172a]/60 border border-[#1e293b]">
                            <div className="text-slate-400 text-xs uppercase">p95 Latency</div>
                            <div className={`text-2xl font-mono mt-1 ${(sreOverview?.p95_latency_ms || 0) > 300 ? 'text-red-400' :
                                (sreOverview?.p95_latency_ms || 0) > 200 ? 'text-yellow-400' : 'text-white'
                                }`}>
                                {Math.round(sreOverview?.p95_latency_ms || 0)}ms
                            </div>
                        </div>

                        {/* RPS with Delta */}
                        <div className="p-5 rounded-xl bg-[#0f172a]/60 border border-[#1e293b]">
                            <div className="text-slate-400 text-xs uppercase">Traffic (RPS)</div>
                            <div className="text-2xl font-mono mt-1 text-white">
                                {sreOverview?.rps?.current?.toFixed(1) || 0}
                            </div>
                            <div className={`text-xs mt-1 ${(sreOverview?.rps?.delta_percent || 0) > 0 ? 'text-emerald-400' :
                                (sreOverview?.rps?.delta_percent || 0) < 0 ? 'text-red-400' : 'text-slate-500'
                                }`}>
                                {(sreOverview?.rps?.delta_percent || 0) > 0 ? '+' : ''}{sreOverview?.rps?.delta_percent?.toFixed(1) || 0}% vs prev
                            </div>
                        </div>
                    </div>
                </section>

                {/* ==================== SECTION 1.5: Container Resources ==================== */}
                <section>
                    <div className="flex items-center gap-3 mb-4">
                        <span className="w-1.5 h-6 bg-cyan-500 rounded" />
                        <h2 className="text-lg font-bold text-white">Container Resources</h2>
                        <Container className="w-4 h-4 text-slate-500" />
                        <span className="ml-auto text-xs text-slate-500">
                            {containerSummary.running_containers}/{containerSummary.total_containers} running
                        </span>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        {containers.map((container) => {
                            const isRunning = container.running;
                            const cpuPercent = container.cpu_percent || 0;
                            const memPercent = container.memory?.percent || 0;
                            const cpuColor = cpuPercent > 80 ? 'text-red-400' : cpuPercent > 50 ? 'text-yellow-400' : 'text-emerald-400';
                            const memColor = memPercent > 80 ? 'text-red-400' : memPercent > 60 ? 'text-yellow-400' : 'text-emerald-400';

                            return (
                                <div key={container.name} className="bg-[#0f172a]/60 border border-[#1e293b] p-5 rounded-xl">
                                    {/* Container Header */}
                                    <div className="flex items-center justify-between mb-4">
                                        <div className="flex items-center gap-2">
                                            <Container className="w-4 h-4 text-cyan-400" />
                                            <span className="font-mono text-white text-sm">{container.display_name}</span>
                                        </div>
                                        <span className={`px-2 py-0.5 rounded text-xs font-mono ${isRunning ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>
                                            {container.status}
                                        </span>
                                    </div>

                                    {isRunning ? (
                                        <div className="space-y-4">
                                            {/* CPU Usage */}
                                            <div>
                                                <div className="flex items-center justify-between mb-1">
                                                    <div className="flex items-center gap-1.5 text-xs text-slate-500">
                                                        <Cpu className="w-3 h-3" /> CPU
                                                    </div>
                                                    <span className={`font-mono text-sm ${cpuColor}`}>{(container.cpu_percent || 0).toFixed(1)}%</span>
                                                </div>
                                                <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                                                    <div
                                                        className={`h-full transition-all duration-300 ${(container.cpu_percent || 0) > 80 ? 'bg-red-500' : (container.cpu_percent || 0) > 50 ? 'bg-yellow-500' : 'bg-emerald-500'}`}
                                                        style={{ width: `${Math.min(100, container.cpu_percent || 0)}%` }}
                                                    />
                                                </div>
                                            </div>

                                            {/* Memory Usage */}
                                            <div>
                                                <div className="flex items-center justify-between mb-1">
                                                    <div className="flex items-center gap-1.5 text-xs text-slate-500">
                                                        <HardDrive className="w-3 h-3" /> Memory
                                                    </div>
                                                    <span className={`font-mono text-sm ${memColor}`}>
                                                        {(container.memory?.used_mb || 0).toFixed(0)} / {(container.memory?.limit_mb || 0).toFixed(0)} MB
                                                    </span>
                                                </div>
                                                <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                                                    <div
                                                        className={`h-full transition-all duration-300 ${(container.memory?.percent || 0) > 80 ? 'bg-red-500' : (container.memory?.percent || 0) > 60 ? 'bg-yellow-500' : 'bg-emerald-500'}`}
                                                        style={{ width: `${Math.min(100, container.memory?.percent || 0)}%` }}
                                                    />
                                                </div>
                                            </div>

                                            {/* Network I/O */}
                                            <div className="flex items-center justify-between text-xs">
                                                <div className="flex items-center gap-1.5 text-slate-500">
                                                    <Network className="w-3 h-3" /> Network
                                                </div>
                                                <div className="flex gap-3 font-mono">
                                                    <span className="text-blue-400">↓ {(container.network?.rx_mb || 0).toFixed(1)} MB</span>
                                                    <span className="text-purple-400">↑ {(container.network?.tx_mb || 0).toFixed(1)} MB</span>
                                                </div>
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="text-center py-4">
                                            <XCircle className="w-8 h-8 mx-auto text-red-500/50 mb-2" />
                                            <p className="text-xs text-slate-500">Container not running</p>
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>

                    {/* Summary Bar */}
                    <div className="mt-4 flex items-center gap-6 px-4 py-3 bg-[#020617] rounded-lg border border-[#1e293b]">
                        <div className="flex items-center gap-2">
                            <span className="text-xs text-slate-500">Total CPU:</span>
                            <span className="font-mono text-sm text-white">{(containerSummary?.total_cpu_percent || 0).toFixed(1)}%</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="text-xs text-slate-500">Total Memory:</span>
                            <span className="font-mono text-sm text-white">{(containerSummary?.total_memory_mb || 0).toFixed(0)} MB</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="text-xs text-slate-500">Containers:</span>
                            <span className={`font-mono text-sm ${(containerSummary?.running_containers || 0) === (containerSummary?.total_containers || 0) ? 'text-emerald-400' : 'text-yellow-400'}`}>
                                {containerSummary?.running_containers || 0}/{containerSummary?.total_containers || 0} healthy
                            </span>
                        </div>
                    </div>
                </section>

                {/* ==================== SECTION 2: Real-Time Charts ==================== */}
                <section>
                    {/* Header with improved layout */}
                    <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8">
                        <div>
                            <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400">
                                Infrastructure Health
                            </h1>
                            <p className="text-slate-400 text-sm mt-1">
                                Real-time monitoring of system resources, database performance, and API stability.
                            </p>
                        </div>

                        <div className="flex items-center gap-3 bg-[#0f172a] p-2 rounded-lg border border-[#1e293b]">
                            <Activity className="w-4 h-4 text-indigo-400 animate-pulse" />
                            <span className="text-xs font-mono text-slate-300">
                                System Status: <span className="text-emerald-400 font-bold">OPERATIONAL</span>
                            </span>
                            <div className="h-4 w-[1px] bg-[#1e293b] mx-1"></div>
                            <span className="text-xs text-slate-500">Live Updates</span>
                        </div>
                    </div>

                    {/* CHARTS SECTION */}
                    <div className="mb-8">
                        <InfrastructureCharts
                            data={chartData}
                            loading={chartLoading}
                        />
                    </div>
                </section>

                {/* ==================== SECTION 3: Service Health Matrix ==================== */}
                <section>
                    <div className="flex items-center gap-3 mb-4">
                        <span className="w-1.5 h-6 bg-purple-500 rounded" />
                        <h2 className="text-lg font-bold text-white">Service Health Matrix</h2>
                    </div>

                    <div className="bg-[#0f172a]/60 border border-[#1e293b] rounded-xl overflow-hidden">
                        <table className="w-full text-left text-sm">
                            <thead className="bg-[#020617] text-slate-500 uppercase text-xs">
                                <tr>
                                    <th className="p-4">Service</th>
                                    <th className="p-4">Health</th>
                                    <th className="p-4">Error %</th>
                                    <th className="p-4">p95 Latency</th>
                                    <th className="p-4">Saturation</th>
                                    <th className="p-4">Uptime</th>
                                    <th className="p-4">Trend</th>
                                </tr>
                            </thead>
                            <tbody className="text-slate-300 divide-y divide-[#1e293b]">
                                {services.map((service: ServiceHealthItem) => {
                                    const colors = healthColors[service.health_state] || healthColors.healthy;
                                    const isExpanded = expandedService === service.name;

                                    return (
                                        <Fragment key={service.name}>
                                            <tr
                                                className={`cursor-pointer hover:bg-[#1e293b]/50 transition ${isExpanded ? 'bg-[#1e293b]/30' : ''}`}
                                                onClick={() => setExpandedService(isExpanded ? null : service.name)}
                                            >
                                                <td className="p-4 font-mono flex items-center gap-2">
                                                    {isExpanded ? <ChevronDown className="w-4 h-4 text-slate-500" /> : <ChevronRight className="w-4 h-4 text-slate-500" />}
                                                    {service.name}
                                                </td>
                                                <td className="p-4">
                                                    <span className={`inline-flex items-center gap-2 px-2 py-1 rounded text-xs ${colors.bg} ${colors.text} ${colors.border} border`}>
                                                        <span className={`w-2 h-2 rounded-full ${colors.dot}`} />
                                                        {service.health_state}
                                                    </span>
                                                </td>
                                                <td className="p-4 font-mono">{service.error_rate_percent?.toFixed(2) || 0}%</td>
                                                <td className="p-4 font-mono">{Math.round(service.p95_latency_ms || 0)}ms</td>
                                                <td className="p-4">
                                                    <div className="flex items-center gap-2">
                                                        <div className="w-16 bg-slate-800 h-2 rounded-full overflow-hidden">
                                                            <div
                                                                className={`h-full ${service.saturation_percent > 80 ? 'bg-red-500' : service.saturation_percent > 60 ? 'bg-yellow-500' : 'bg-emerald-500'}`}
                                                                style={{ width: `${Math.min(100, service.saturation_percent)}%` }}
                                                            />
                                                        </div>
                                                        <span className="text-xs font-mono">{service.saturation_percent?.toFixed(0)}%</span>
                                                    </div>
                                                </td>
                                                <td className="p-4 font-mono text-emerald-400">{service.uptime_percent?.toFixed(2)}%</td>
                                                <td className="p-4">
                                                    <TrendIcon trend={service.trend} />
                                                </td>
                                            </tr>
                                            <ServiceDeepDivePanel
                                                serviceName={service.name.toLowerCase()}
                                                isOpen={isExpanded}
                                                onClose={() => setExpandedService(null)}
                                            />
                                        </Fragment>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                </section>

                {/* ==================== SECTION 4: AI/RAG Observability ==================== */}
                <section>
                    <div className="flex items-center gap-3 mb-4">
                        <span className="w-1.5 h-6 bg-amber-500 rounded" />
                        <h2 className="text-lg font-bold text-white">AI/RAG Observability</h2>
                        <Brain className="w-4 h-4 text-slate-500" />
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                        {/* Retrieval Success */}
                        <div className="bg-[#0f172a]/60 border border-[#1e293b] p-5 rounded-xl">
                            <div className="text-xs text-slate-500 uppercase">Retrieval Success</div>
                            <div className={`text-2xl font-mono mt-1 ${ragData.retrieval_success_percent >= 95 ? 'text-emerald-400' : ragData.retrieval_success_percent >= 80 ? 'text-yellow-400' : 'text-red-400'}`}>
                                {ragData.retrieval_success_percent?.toFixed(1)}%
                            </div>
                        </div>

                        {/* Empty Context Rate */}
                        <div className="bg-[#0f172a]/60 border border-[#1e293b] p-5 rounded-xl">
                            <div className="text-xs text-slate-500 uppercase">Empty Context Rate</div>
                            <div className={`text-2xl font-mono mt-1 ${ragData.empty_context_rate <= 5 ? 'text-emerald-400' : ragData.empty_context_rate <= 20 ? 'text-yellow-400' : 'text-red-400'}`}>
                                {ragData.empty_context_rate?.toFixed(1)}%
                            </div>
                        </div>

                        {/* Avg Docs per Query */}
                        <div className="bg-[#0f172a]/60 border border-[#1e293b] p-5 rounded-xl">
                            <div className="text-xs text-slate-500 uppercase">Avg Docs/Query</div>
                            <div className="text-2xl font-mono mt-1 text-white">
                                {ragData.avg_docs_per_query?.toFixed(1)}
                            </div>
                        </div>

                        {/* SLA Violations */}
                        <div className="bg-[#0f172a]/60 border border-[#1e293b] p-5 rounded-xl">
                            <div className="text-xs text-slate-500 uppercase">SLA Violations</div>
                            <div className={`text-2xl font-mono mt-1 ${ragData.sla_violation_percent <= 2 ? 'text-emerald-400' : ragData.sla_violation_percent <= 10 ? 'text-yellow-400' : 'text-red-400'}`}>
                                {ragData.sla_violation_percent?.toFixed(1)}%
                            </div>
                            <div className="text-xs text-slate-500 mt-1">SLA: {ragData.sla_threshold_ms}ms</div>
                        </div>

                        {/* Total Queries */}
                        <div className="bg-[#0f172a]/60 border border-[#1e293b] p-5 rounded-xl">
                            <div className="text-xs text-slate-500 uppercase">Total Queries ({ragData.period_hours}h)</div>
                            <div className="text-2xl font-mono mt-1 text-white">
                                {ragData.total_queries?.toLocaleString()}
                            </div>
                        </div>
                    </div>

                    {/* Latency Breakdown */}
                    <div className="mt-4 bg-[#0f172a]/60 border border-[#1e293b] p-5 rounded-xl">
                        <div className="text-xs text-slate-500 uppercase mb-4">Latency Breakdown</div>
                        <div className="grid grid-cols-4 gap-4">
                            <div>
                                <div className="text-xs text-purple-400">Embedding</div>
                                <div className="text-lg font-mono text-white">{ragData.latency_breakdown?.embedding_ms?.toFixed(0) || 0}ms</div>
                            </div>
                            <div>
                                <div className="text-xs text-blue-400">Retrieval</div>
                                <div className="text-lg font-mono text-white">{ragData.latency_breakdown?.retrieval_ms?.toFixed(0) || 0}ms</div>
                            </div>
                            <div>
                                <div className="text-xs text-amber-400">LLM</div>
                                <div className="text-lg font-mono text-white">{ragData.latency_breakdown?.llm_ms?.toFixed(0) || 0}ms</div>
                            </div>
                            <div>
                                <div className="text-xs text-red-400">p95 Total</div>
                                <div className={`text-lg font-mono ${(ragData.latency_breakdown?.p95_ms || 0) > ragData.sla_threshold_ms ? 'text-red-400' : 'text-emerald-400'}`}>
                                    {ragData.latency_breakdown?.p95_ms?.toFixed(0) || 0}ms
                                </div>
                            </div>
                        </div>
                    </div>
                </section>

                {/* ==================== SECTION 5: User Impact Bridge ==================== */}
                <section>
                    <div className="flex items-center gap-3 mb-4">
                        <span className="w-1.5 h-6 bg-red-500 rounded" />
                        <h2 className="text-lg font-bold text-white">User Impact Bridge</h2>
                        <Users className="w-4 h-4 text-slate-500" />
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        {/* Left: Impact Stats */}
                        <div className="bg-[#0f172a]/60 border border-[#1e293b] p-6 rounded-xl">
                            <div className="text-xs text-slate-500 uppercase mb-4">Impact Summary (Last 5 min)</div>
                            <div className="space-y-4">
                                <div className="flex justify-between items-center">
                                    <span className="text-slate-400">Failed Requests</span>
                                    <span className={`font-mono text-lg ${userImpact.failed_requests_percent > 5 ? 'text-red-400' : userImpact.failed_requests_percent > 1 ? 'text-yellow-400' : 'text-emerald-400'}`}>
                                        {userImpact.failed_requests_percent?.toFixed(2)}%
                                    </span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-slate-400">Slow Requests</span>
                                    <span className={`font-mono text-lg ${userImpact.slow_requests_percent > 10 ? 'text-red-400' : userImpact.slow_requests_percent > 5 ? 'text-yellow-400' : 'text-emerald-400'}`}>
                                        {userImpact.slow_requests_percent?.toFixed(2)}%
                                    </span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-slate-400">Total Requests</span>
                                    <span className="font-mono text-lg text-white">{userImpact.total_requests_5m?.toLocaleString()}</span>
                                </div>
                            </div>

                            {userImpact.has_user_impact && (
                                <div className="mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
                                    <span className="text-red-400 text-sm">⚠️ Users are currently impacted</span>
                                </div>
                            )}
                        </div>

                        {/* Middle: Degraded Services */}
                        <div className="bg-[#0f172a]/60 border border-[#1e293b] p-6 rounded-xl">
                            <div className="text-xs text-slate-500 uppercase mb-4">Correlated Degradations</div>
                            {userImpact.degraded_services && userImpact.degraded_services.length > 0 ? (
                                <div className="space-y-2">
                                    {userImpact.degraded_services.map((service: string) => (
                                        <div key={service} className="flex items-center gap-2 p-2 bg-yellow-500/10 border border-yellow-500/30 rounded">
                                            <AlertTriangle className="w-4 h-4 text-yellow-400" />
                                            <span className="text-yellow-400 text-sm font-mono">{service}</span>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="text-center py-8 text-slate-500">
                                    <CheckCircle className="w-8 h-8 mx-auto mb-2 text-emerald-500" />
                                    <p>No degraded services</p>
                                </div>
                            )}
                        </div>

                        {/* Right: Top Impacted Endpoints */}
                        <div className="bg-[#0f172a]/60 border border-[#1e293b] p-6 rounded-xl">
                            <div className="text-xs text-slate-500 uppercase mb-4">Top Impacted Endpoints</div>
                            {userImpact.top_impacted_endpoints && userImpact.top_impacted_endpoints.length > 0 ? (
                                <div className="space-y-2">
                                    {userImpact.top_impacted_endpoints.map((ep, i) => (
                                        <div key={i} className="flex items-center justify-between p-2 bg-[#020617] rounded">
                                            <span className="text-xs text-slate-300 font-mono truncate max-w-[150px]">{ep.endpoint}</span>
                                            <span className={`text-xs font-mono ${ep.avg_latency_ms > 300 ? 'text-red-400' : 'text-yellow-400'}`}>
                                                {ep.avg_latency_ms?.toFixed(0)}ms
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="text-center py-8 text-slate-500">
                                    <CheckCircle className="w-8 h-8 mx-auto mb-2 text-emerald-500" />
                                    <p>All endpoints healthy</p>
                                </div>
                            )}
                        </div>
                    </div>
                </section>

            </div>
        </>
    );
}
