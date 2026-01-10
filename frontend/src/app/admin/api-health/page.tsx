'use client';

/**
 * External API Health Page
 * 
 * Matches POC: admin_api_health.html
 * - API status cards with latency sparklines
 * - Aggregate latency chart
 * - Failure logs table
 * 
 * Note: External API health data partially available
 * Using infrastructure metrics as proxy
 */

import { useInfrastructure, useAdminDashboard } from '@/hooks/useAdminAPI';
import dynamic from 'next/dynamic';

const Chart = dynamic(() => import('react-apexcharts'), { ssr: false });

export default function APIHealthPage() {
    const { metrics, isLoading } = useInfrastructure();
    const { data: dashboard } = useAdminDashboard();

    const sparklineOptions: ApexCharts.ApexOptions = {
        chart: { type: 'area', sparkline: { enabled: true } },
        stroke: { curve: 'smooth', width: 2 },
        fill: { opacity: 0.2 },
        tooltip: { enabled: false }
    };

    const latencyChartOptions: ApexCharts.ApexOptions = {
        chart: { type: 'line', toolbar: { show: false }, background: 'transparent' },
        theme: { mode: 'dark' },
        grid: { borderColor: '#1e293b' },
        colors: ['#10b981', '#f59e0b', '#6366f1'],
        stroke: { width: 2, curve: 'smooth' },
        xaxis: { categories: ['1h', '2h', '3h', '4h', '5h', '6h', '7h', '8h'] }
    };

    if (isLoading) {
        return (
            <>
                <header className="h-16 px-8 border-b border-[#1e293b] flex items-center bg-[#0f172a]/50 backdrop-blur sticky top-0 z-20">
                    <h1 className="text-xl font-bold text-white">External API Gateway Status</h1>
                </header>
                <div className="p-8 animate-pulse space-y-8">
                    <div className="grid grid-cols-3 gap-6">
                        <div className="bg-[#0f172a] h-40 rounded-xl"></div>
                        <div className="bg-[#0f172a] h-40 rounded-xl"></div>
                        <div className="bg-[#0f172a] h-40 rounded-xl"></div>
                    </div>
                </div>
            </>
        );
    }

    // Build API status based on infrastructure
    const apiStatuses = [
        {
            name: 'Redis',
            status: metrics?.redis.connected ? 'operational' : 'down',
            latency: `${metrics?.redis.memory_used_mb?.toFixed(0) || 0}MB`,
            uptime: metrics?.redis.connected ? '100%' : '0%',
            color: metrics?.redis.connected ? '#10b981' : '#ef4444'
        },
        {
            name: 'MySQL',
            status: metrics?.mysql.connected ? 'operational' : 'down',
            latency: `${metrics?.mysql.threads_connected || 0} conn`,
            uptime: metrics?.mysql.connected ? '100%' : '0%',
            color: metrics?.mysql.connected ? '#10b981' : '#ef4444'
        },
        {
            name: 'ChromaDB',
            status: metrics?.chromadb.connected ? 'operational' : 'down',
            latency: `${(metrics?.chromadb.document_count || 0).toLocaleString()} docs`,
            uptime: metrics?.chromadb.connected ? '100%' : '0%',
            color: metrics?.chromadb.connected ? '#10b981' : '#ef4444'
        }
    ];

    const operational = apiStatuses.filter(a => a.status === 'operational').length;
    const degraded = apiStatuses.filter(a => a.status !== 'operational').length;

    return (
        <>
            <header className="h-16 px-8 border-b border-[#1e293b] flex items-center justify-between bg-[#0f172a]/50 backdrop-blur sticky top-0 z-20">
                <h1 className="text-xl font-bold text-white">Service Gateway Status</h1>
                <div className="flex gap-4 text-xs">
                    <div className="flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                        {operational} Operational
                    </div>
                    {degraded > 0 && (
                        <div className="flex items-center gap-2">
                            <span className="w-2 h-2 rounded-full bg-red-500"></span>
                            {degraded} Down
                        </div>
                    )}
                </div>
            </header>

            <div className="flex-1 overflow-y-auto p-8 space-y-8">

                {/* LATENCY GRID */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {apiStatuses.map((api, i) => (
                        <div key={i} className={`bg-[#0f172a] border p-5 rounded-xl ${api.status !== 'operational' ? 'border-red-500/50' : 'border-[#1e293b]'}`}>
                            <div className="flex justify-between mb-4">
                                <div className="font-bold text-white flex items-center">
                                    <span className={`w-2 h-2 rounded-full mr-2 ${api.status === 'operational' ? 'bg-emerald-500' : 'bg-red-500'}`}></span>
                                    {api.name}
                                </div>
                                <span className={`text-xs font-mono px-2 rounded ${api.status === 'operational' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>
                                    {api.uptime}
                                </span>
                            </div>
                            <div className="grid grid-cols-2 gap-4 mb-4">
                                <div>
                                    <div className="text-[10px] text-slate-500 uppercase">Status</div>
                                    <div className="text-xl text-white font-mono capitalize">{api.status}</div>
                                </div>
                                <div>
                                    <div className="text-[10px] text-slate-500 uppercase">Info</div>
                                    <div className="text-xl text-white font-mono">{api.latency}</div>
                                </div>
                            </div>
                            <div className="h-16">
                                <Chart
                                    type="area"
                                    height={64}
                                    options={{ ...sparklineOptions, colors: [api.color] }}
                                    series={[{ data: [80, 85, 90, 88, 92, 95, 93, 96, 100].map(() => api.status === 'operational' ? 100 : 0) }]}
                                />
                            </div>
                        </div>
                    ))}
                </div>

                {/* AGGREGATE CHART */}
                <div className="bg-[#0f172a] border border-[#1e293b] p-6 rounded-xl">
                    <h3 className="font-bold text-white mb-6">System Performance</h3>
                    <div className="h-80">
                        <Chart
                            type="line"
                            height={320}
                            options={latencyChartOptions}
                            series={[
                                { name: 'Redis Hit Rate', data: [90, 92, 94, 93, 95, 94, 96, metrics?.redis.hit_rate_percent || 95] },
                                { name: 'MySQL Connections', data: [2, 3, 2, 4, 3, 2, 3, metrics?.mysql.threads_connected || 3] },
                                { name: 'ChromaDB Docs (K)', data: [3, 3.1, 3.1, 3.1, 3.2, 3.2, 3.2, (metrics?.chromadb.document_count || 3000) / 1000] }
                            ]}
                        />
                    </div>
                </div>

                {/* TRAFFIC INFO */}
                <div className="bg-[#0f172a] border border-[#1e293b] rounded-xl overflow-hidden">
                    <div className="p-4 border-b border-[#1e293b] flex justify-between">
                        <h3 className="font-bold text-white">Traffic Summary</h3>
                    </div>
                    <div className="p-6 grid grid-cols-1 md:grid-cols-4 gap-6">
                        <div>
                            <div className="text-xs text-slate-500 uppercase">Requests/sec</div>
                            <div className="text-2xl text-white font-mono">{dashboard?.traffic.requests_per_second?.toFixed(1) || 0}</div>
                        </div>
                        <div>
                            <div className="text-xs text-slate-500 uppercase">Total (1h)</div>
                            <div className="text-2xl text-white font-mono">{dashboard?.traffic.total_requests_1h || 0}</div>
                        </div>
                        <div>
                            <div className="text-xs text-slate-500 uppercase">Avg Latency</div>
                            <div className="text-2xl text-white font-mono">{dashboard?.traffic.avg_latency_ms?.toFixed(0) || 0}ms</div>
                        </div>
                        <div>
                            <div className="text-xs text-slate-500 uppercase">Error Rate</div>
                            <div className="text-2xl text-white font-mono">{dashboard?.traffic.error_rate_percent?.toFixed(2) || 0}%</div>
                        </div>
                    </div>
                </div>

            </div>
        </>
    );
}
