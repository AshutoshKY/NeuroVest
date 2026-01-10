'use client';

/**
 * AI & RAG Engine Page
 * 
 * Matches POC: admin_ai_rag.html
 * - Token usage chart (input vs output)
 * - Cost by model donut
 * - RAG latency metrics
 * - Guardrail rejections table
 * 
 * ALL DATA FROM REAL APIs
 */

import { useAIMetrics } from '@/hooks/useAdminAPI';
import dynamic from 'next/dynamic';

const Chart = dynamic(() => import('react-apexcharts'), { ssr: false });

export default function AIRAGPage() {
    const { summary, hourly, isLoading, refresh } = useAIMetrics();

    const tokenChartOptions: ApexCharts.ApexOptions = {
        chart: { type: 'bar', toolbar: { show: false }, background: 'transparent', stacked: true },
        theme: { mode: 'dark' },
        grid: { borderColor: '#1e293b' },
        colors: ['#6366f1', '#10b981'],
        xaxis: { categories: hourly?.hourly?.slice(0, 7).map(h => h.hour.split(' ')[1] || h.hour) || [] }
    };

    const donutOptions: ApexCharts.ApexOptions = {
        chart: { type: 'donut', height: 250 },
        labels: ['Azure OpenAI', 'GPT-4', 'Embeddings'],
        colors: ['#6366f1', '#a855f7', '#94a3b8'],
        legend: { position: 'bottom' },
        theme: { mode: 'dark' }
    };

    if (isLoading) {
        return (
            <>
                <header className="h-16 px-8 border-b border-[#1e293b] flex items-center justify-between bg-[#0f172a]/50 backdrop-blur sticky top-0 z-20">
                    <h1 className="text-xl font-bold text-white">AI Engine & Guardrails</h1>
                </header>
                <div className="p-8 animate-pulse space-y-8">
                    <div className="bg-[#0f172a] h-80 rounded-xl"></div>
                </div>
            </>
        );
    }

    return (
        <>
            <header className="h-16 px-8 border-b border-[#1e293b] flex items-center justify-between bg-[#0f172a]/50 backdrop-blur sticky top-0 z-20">
                <h1 className="text-xl font-bold text-white">AI Engine & Guardrails</h1>
                <div className="flex gap-4">
                    <div className="text-right">
                        <div className="text-xs text-slate-500">24h Cost</div>
                        <div className="text-sm font-mono text-yellow-400">${summary?.total_cost_usd?.toFixed(2) || '0.00'}</div>
                    </div>
                    <div className="text-right">
                        <div className="text-xs text-slate-500">Tokens Today</div>
                        <div className="text-sm font-mono text-white">{summary?.total_tokens?.toLocaleString() || 0}</div>
                    </div>
                </div>
            </header>

            <div className="flex-1 overflow-y-auto p-8 space-y-8">

                {/* TOKENOMICS */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <div className="lg:col-span-2 bg-[#0f172a] border border-[#1e293b] p-6 rounded-xl">
                        <h3 className="font-bold text-white mb-4">Token Usage (Input vs Output)</h3>
                        <div className="w-full h-72">
                            <Chart
                                type="bar"
                                height={300}
                                options={tokenChartOptions}
                                series={[
                                    { name: 'Prompt Tokens', data: hourly?.hourly?.slice(0, 7).map(h => h.prompt_tokens) || [] },
                                    { name: 'Completion Tokens', data: hourly?.hourly?.slice(0, 7).map(h => h.completion_tokens) || [] }
                                ]}
                            />
                        </div>
                    </div>
                    <div className="bg-[#0f172a] border border-[#1e293b] p-6 rounded-xl flex flex-col">
                        <h3 className="font-bold text-white mb-2">Cost Distribution</h3>
                        <div className="flex-1 flex items-center justify-center">
                            <Chart
                                type="donut"
                                height={250}
                                width="100%"
                                options={donutOptions}
                                series={[summary?.total_cost_usd || 0, 0, 0]}
                            />
                        </div>
                    </div>
                </div>

                {/* RAG & GUARDRAILS */}
                <section>
                    <h2 className="text-lg font-bold text-white mb-4">RAG Pipeline Health</h2>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        {/* Metrics */}
                        <div className="space-y-4">
                            <div className="bg-[#0f172a] border border-[#1e293b] p-5 rounded-xl">
                                <div className="text-xs text-slate-500 uppercase font-bold">Requests Today</div>
                                <div className="text-2xl text-white font-mono mt-1">{summary?.total_requests || 0}</div>
                            </div>
                            <div className="bg-[#0f172a] border border-[#1e293b] p-5 rounded-xl">
                                <div className="text-xs text-slate-500 uppercase font-bold">Avg Tokens/Request</div>
                                <div className="text-2xl text-white font-mono mt-1">{summary?.avg_tokens_per_request || 0}</div>
                            </div>
                        </div>

                        {/* Guardrail Logs */}
                        <div className="md:col-span-2 bg-[#0f172a] border border-[#1e293b] rounded-xl overflow-hidden">
                            <div className="p-4 border-b border-[#1e293b] bg-red-500/5 flex justify-between items-center">
                                <span className="font-bold text-red-400">Guardrail Rejections (Today)</span>
                                <span className="text-xs bg-red-500 text-white px-2 py-0.5 rounded">
                                    {summary?.guardrail_rejections || 0} Blocked
                                </span>
                            </div>
                            <div className="p-4">
                                {summary?.guardrail_rejections === 0 ? (
                                    <div className="text-sm text-slate-500 text-center py-4">
                                        No guardrail rejections today
                                    </div>
                                ) : (
                                    <div className="text-sm text-slate-400">
                                        {summary?.guardrail_rejections} prompts were blocked by guardrails.
                                        Check the AI metrics API for detailed breakdown.
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </section>

                {/* Hourly Stats */}
                <section>
                    <h2 className="text-lg font-bold text-white mb-4">Hourly Breakdown (Last 24h)</h2>
                    <div className="bg-[#0f172a] border border-[#1e293b] rounded-xl overflow-hidden">
                        <table className="w-full text-left text-xs">
                            <thead className="bg-[#020617] text-slate-500 uppercase">
                                <tr>
                                    <th className="p-3">Hour</th>
                                    <th className="p-3">Requests</th>
                                    <th className="p-3">Tokens</th>
                                    <th className="p-3">Cost</th>
                                    <th className="p-3">Avg Latency</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-[#1e293b] text-slate-300">
                                {(hourly?.hourly || []).slice(0, 12).map((h, i) => (
                                    <tr key={i}>
                                        <td className="p-3 font-mono">{h.hour}</td>
                                        <td className="p-3">{h.total_requests}</td>
                                        <td className="p-3">{h.total_tokens.toLocaleString()}</td>
                                        <td className="p-3 text-yellow-400">${h.total_cost_usd.toFixed(4)}</td>
                                        <td className="p-3">{h.avg_latency_ms.toFixed(0)}ms</td>
                                    </tr>
                                ))}
                                {(!hourly?.hourly || hourly.hourly.length === 0) && (
                                    <tr>
                                        <td colSpan={5} className="p-4 text-center text-slate-500">No data available</td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </section>

            </div>
        </>
    );
}
