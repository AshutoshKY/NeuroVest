'use client';

import { BarChart3 } from 'lucide-react';
import {
    LineChart, Line, AreaChart, Area, BarChart, Bar,
    XAxis, YAxis, CartesianGrid, Tooltip, Legend,
    ResponsiveContainer, ComposedChart
} from 'recharts';

// Chart colors
const chartColors = {
    requests: '#3b82f6',    // Blue
    errors: '#ef4444',      // Red
    latency: '#8b5cf6',     // Purple
    errorRate: '#f97316',   // Orange
    success: '#22c55e'      // Green
};

// Custom tooltip for charts
function ChartTooltip({ active, payload, label, unit }: { active?: boolean; payload?: { name: string; value: number; color: string }[]; label?: string; unit?: string }) {
    if (!active || !payload || payload.length === 0) return null;

    return (
        <div className="bg-[#0f172a] border border-[#1e293b] p-3 rounded-lg shadow-xl">
            <p className="text-xs text-slate-400 mb-2">{label}</p>
            {payload.map((entry, index) => (
                <div key={index} className="flex items-center gap-2 text-sm">
                    <span className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }} />
                    <span className="text-slate-300">{entry.name}:</span>
                    <span className="text-white font-mono">{entry.value?.toLocaleString()}{unit || ''}</span>
                </div>
            ))}
        </div>
    );
}

interface ChartsProps {
    data: {
        traffic: any[];
        latency: any[];
        errors: any[];
        period_hours: number;
        data_points: number;
    };
    loading: boolean;
}

export default function InfrastructureCharts({ data, loading }: ChartsProps) {
    if (loading && (!data || !data.traffic || data.data_points === 0)) {
        return (
            <div className="bg-[#0f172a]/60 border border-[#1e293b] p-8 rounded-xl text-center">
                <BarChart3 className="w-12 h-12 mx-auto text-slate-600 mb-3 animate-pulse" />
                <p className="text-slate-500">Loading chart data...</p>
            </div>
        );
    }

    if (!data || data.data_points === 0) {
        return (
            <div className="bg-[#0f172a]/60 border border-[#1e293b] p-8 rounded-xl text-center">
                <BarChart3 className="w-12 h-12 mx-auto text-slate-600 mb-3" />
                <p className="text-slate-500">No historical data available yet.</p>
                <p className="text-xs text-slate-600 mt-1">Data will appear as requests are processed.</p>
            </div>
        );
    }

    return (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Traffic Chart - Requests & Errors */}
            <div className="bg-[#0f172a]/60 border border-[#1e293b] p-6 rounded-xl">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-sm font-semibold text-white">Traffic Overview</h3>
                    <div className="flex items-center gap-4 text-xs">
                        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full" style={{ backgroundColor: chartColors.requests }} /> Requests</span>
                        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full" style={{ backgroundColor: chartColors.errors }} /> Errors</span>
                    </div>
                </div>
                <div className="h-[200px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <ComposedChart data={data.traffic}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                            <XAxis
                                dataKey="hour"
                                tick={{ fill: '#64748b', fontSize: 11 }}
                                axisLine={{ stroke: '#1e293b' }}
                            />
                            <YAxis
                                yAxisId="left"
                                tick={{ fill: '#64748b', fontSize: 11 }}
                                axisLine={{ stroke: '#1e293b' }}
                                label={{ value: 'Requests', angle: -90, position: 'insideLeft', fill: '#64748b', fontSize: 10 }}
                            />
                            <YAxis
                                yAxisId="right"
                                orientation="right"
                                tick={{ fill: '#64748b', fontSize: 11 }}
                                axisLine={{ stroke: '#1e293b' }}
                                label={{ value: 'Errors', angle: 90, position: 'insideRight', fill: '#ef4444', fontSize: 10 }}
                            />
                            <Tooltip content={<ChartTooltip />} />
                            <Bar yAxisId="left" dataKey="requests" fill={chartColors.requests} name="Requests" radius={[4, 4, 0, 0]} />
                            <Line yAxisId="right" type="monotone" dataKey="errors" stroke={chartColors.errors} name="Errors" strokeWidth={2} dot={{ r: 3 }} />
                        </ComposedChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Latency Chart */}
            <div className="bg-[#0f172a]/60 border border-[#1e293b] p-6 rounded-xl">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-sm font-semibold text-white">Average Latency</h3>
                    <div className="flex items-center gap-4 text-xs">
                        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full" style={{ backgroundColor: chartColors.latency }} /> Avg Latency</span>
                        <span className="text-slate-500">SLA: 200ms</span>
                    </div>
                </div>
                <div className="h-[200px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={data.latency}>
                            <defs>
                                <linearGradient id="latencyGradient" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor={chartColors.latency} stopOpacity={0.3} />
                                    <stop offset="95%" stopColor={chartColors.latency} stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                            <XAxis
                                dataKey="hour"
                                tick={{ fill: '#64748b', fontSize: 11 }}
                                axisLine={{ stroke: '#1e293b' }}
                            />
                            <YAxis
                                tick={{ fill: '#64748b', fontSize: 11 }}
                                axisLine={{ stroke: '#1e293b' }}
                                label={{ value: 'ms', angle: -90, position: 'insideLeft', fill: '#64748b', fontSize: 10 }}
                            />
                            <Tooltip content={<ChartTooltip unit="ms" />} />
                            <Area type="monotone" dataKey="avg_latency_ms" stroke={chartColors.latency} fill="url(#latencyGradient)" name="Avg Latency" strokeWidth={2} />
                            {/* SLA Reference Line */}
                            <Line type="monotone" dataKey={() => 200} stroke="#ef4444" strokeDasharray="5 5" name="SLA (200ms)" />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Error Rate Chart */}
            <div className="lg:col-span-2 bg-[#0f172a]/60 border border-[#1e293b] p-6 rounded-xl">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-sm font-semibold text-white">Error Rate Trend</h3>
                    <div className="flex items-center gap-4 text-xs">
                        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full" style={{ backgroundColor: chartColors.errorRate }} /> Error Rate %</span>
                        <span className="text-slate-500">Target: &lt;1%</span>
                    </div>
                </div>
                <div className="h-[150px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={data.errors}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                            <XAxis
                                dataKey="hour"
                                tick={{ fill: '#64748b', fontSize: 11 }}
                                axisLine={{ stroke: '#1e293b' }}
                            />
                            <YAxis
                                tick={{ fill: '#64748b', fontSize: 11 }}
                                axisLine={{ stroke: '#1e293b' }}
                                domain={[0, 'auto']}
                                label={{ value: '%', angle: -90, position: 'insideLeft', fill: '#64748b', fontSize: 10 }}
                            />
                            <Tooltip content={<ChartTooltip unit="%" />} />
                            <Line type="monotone" dataKey="error_rate_percent" stroke={chartColors.errorRate} name="Error Rate" strokeWidth={2} dot={{ r: 4, fill: chartColors.errorRate }} activeDot={{ r: 6 }} />
                            {/* Target Reference Line */}
                            <Line type="monotone" dataKey={() => 1} stroke="#22c55e" strokeDasharray="5 5" name="Target (1%)" />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            </div>
        </div>
    );
}
