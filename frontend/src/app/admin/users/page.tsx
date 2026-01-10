'use client';

/**
 * User Intelligence Page
 * 
 * Matches POC: admin_users.html
 * - Global user distribution (placeholder - requires geo data)
 * - Session duration chart
 * - Retention metrics
 * 
 * Note: Geo data not available from backend
 * Will show available user metrics and indicate missing data
 */

import { useAdminDashboard } from '@/hooks/useAdminAPI';
import dynamic from 'next/dynamic';
import { Globe } from 'lucide-react';

const Chart = dynamic(() => import('react-apexcharts'), { ssr: false });

export default function UsersPage() {
    const { data, isLoading } = useAdminDashboard();

    const sessionChartOptions: ApexCharts.ApexOptions = {
        chart: { type: 'line', toolbar: { show: false }, background: 'transparent' },
        theme: { mode: 'dark' },
        grid: { borderColor: '#1e293b' },
        colors: ['#6366f1'],
        stroke: { curve: 'smooth', width: 3 },
        xaxis: { categories: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'] }
    };

    if (isLoading) {
        return (
            <>
                <header className="h-16 px-8 border-b border-[#1e293b] flex items-center bg-[#0f172a]/50 backdrop-blur sticky top-0 z-20">
                    <h1 className="text-xl font-bold text-white">Product & User Analytics</h1>
                </header>
                <div className="p-8 animate-pulse space-y-8">
                    <div className="bg-[#0f172a] h-96 rounded-xl"></div>
                </div>
            </>
        );
    }

    return (
        <>
            <header className="h-16 px-8 border-b border-[#1e293b] flex items-center justify-between bg-[#0f172a]/50 backdrop-blur sticky top-0 z-20">
                <h1 className="text-xl font-bold text-white">Product & User Analytics</h1>
                <div className="text-right">
                    <div className="text-xs text-slate-500">Active Users (1h)</div>
                    <div className="text-sm font-mono text-emerald-400">{data?.traffic.unique_users_1h || 0}</div>
                </div>
            </header>

            <div className="flex-1 overflow-y-auto p-8 space-y-8">

                {/* GEO MAP PLACEHOLDER */}
                <div className="bg-[#0f172a] border border-[#1e293b] p-6 rounded-xl h-96 flex flex-col">
                    <h3 className="text-lg font-bold text-white mb-4">Global User Distribution</h3>
                    <div className="flex-1 bg-[#020617]/50 border border-[#1e293b] border-dashed rounded-lg flex items-center justify-center">
                        <div className="text-center text-slate-500">
                            <Globe className="w-12 h-12 mx-auto mb-2" />
                            <span className="block">Geo-location data not available</span>
                            <span className="text-xs block mt-2">Backend API does not track user locations</span>
                        </div>
                    </div>
                </div>

                {/* METRICS GRID */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <div className="bg-[#0f172a] border border-[#1e293b] p-6 rounded-xl">
                        <div className="text-xs text-slate-500 uppercase font-bold">Unique Users (1h)</div>
                        <div className="text-3xl font-mono text-white mt-2">{data?.traffic.unique_users_1h || 0}</div>
                    </div>
                    <div className="bg-[#0f172a] border border-[#1e293b] p-6 rounded-xl">
                        <div className="text-xs text-slate-500 uppercase font-bold">Total Requests (1h)</div>
                        <div className="text-3xl font-mono text-white mt-2">{data?.traffic.total_requests_1h || 0}</div>
                    </div>
                    <div className="bg-[#0f172a] border border-[#1e293b] p-6 rounded-xl">
                        <div className="text-xs text-slate-500 uppercase font-bold">Requests/Second</div>
                        <div className="text-3xl font-mono text-white mt-2">{data?.traffic.requests_per_second?.toFixed(1) || 0}</div>
                    </div>
                    <div className="bg-[#0f172a] border border-[#1e293b] p-6 rounded-xl">
                        <div className="text-xs text-slate-500 uppercase font-bold">Error Rate</div>
                        <div className="text-3xl font-mono text-white mt-2">{data?.traffic.error_rate_percent?.toFixed(2) || 0}%</div>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Session placeholder */}
                    <div className="bg-[#0f172a] border border-[#1e293b] p-6 rounded-xl">
                        <h3 className="font-bold text-white mb-4">Traffic Trend</h3>
                        <div className="text-sm text-slate-500 mb-4">
                            Hourly request trend data
                        </div>
                        <div className="h-64">
                            <Chart
                                type="line"
                                height={250}
                                options={sessionChartOptions}
                                series={[{ name: 'Requests', data: [0, data?.traffic.requests_per_second || 0, 0, 0, 0, 0, 0] }]}
                            />
                        </div>
                    </div>

                    {/* Latency distribution */}
                    <div className="bg-[#0f172a] border border-[#1e293b] p-6 rounded-xl">
                        <h3 className="font-bold text-white mb-4">Performance</h3>
                        <div className="space-y-4">
                            <div>
                                <div className="flex justify-between text-sm mb-2">
                                    <span className="text-slate-400">Average Latency</span>
                                    <span className="text-white font-mono">{data?.traffic.avg_latency_ms?.toFixed(0) || 0}ms</span>
                                </div>
                                <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                                    <div className="bg-[#6366f1] h-full" style={{ width: `${Math.min(100, (data?.traffic.avg_latency_ms || 0) / 5)}%` }}></div>
                                </div>
                            </div>
                            <div>
                                <div className="flex justify-between text-sm mb-2">
                                    <span className="text-slate-400">Error Rate</span>
                                    <span className="text-white font-mono">{data?.traffic.error_rate_percent?.toFixed(2) || 0}%</span>
                                </div>
                                <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                                    <div className="bg-red-500 h-full" style={{ width: `${Math.min(100, (data?.traffic.error_rate_percent || 0) * 10)}%` }}></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

            </div>
        </>
    );
}
