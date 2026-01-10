'use client';

/**
 * Security & Audit Page
 * 
 * Matches POC: admin_security.html
 * - Attack vectors chart
 * - WAF blocked requests
 * - Live audit log
 * - Admin team list
 * 
 * Note: Some security metrics not available from current backend
 * Will show available data and indicate missing data clearly
 */

import { useAlerts, useAdminDashboard } from '@/hooks/useAdminAPI';
import dynamic from 'next/dynamic';

const Chart = dynamic(() => import('react-apexcharts'), { ssr: false });

export default function SecurityPage() {
    const { data, isLoading } = useAdminDashboard();
    const { alerts } = useAlerts();

    const chartOptions: ApexCharts.ApexOptions = {
        chart: { type: 'bar', toolbar: { show: false }, background: 'transparent' },
        theme: { mode: 'dark' },
        grid: { borderColor: '#1e293b' },
        colors: ['#ef4444'],
        xaxis: { categories: ['Rate Limit', 'Auth Failure', 'Invalid Token', 'Blocked IP', 'Other'] }
    };

    if (isLoading) {
        return (
            <>
                <header className="h-16 px-8 border-b border-[#1e293b] flex items-center bg-[#0f172a]/50 backdrop-blur sticky top-0 z-20">
                    <h1 className="text-xl font-bold text-white">Security Operations Center (SOC)</h1>
                </header>
                <div className="p-8 animate-pulse space-y-8">
                    <div className="bg-[#0f172a] h-64 rounded-xl"></div>
                </div>
            </>
        );
    }

    return (
        <>
            <header className="h-16 px-8 border-b border-[#1e293b] flex items-center justify-between bg-[#0f172a]/50 backdrop-blur sticky top-0 z-20">
                <h1 className="text-xl font-bold text-white">Security Operations Center (SOC)</h1>
                <div className="flex gap-4">
                    <span className={`text-xs px-3 py-1 rounded font-bold ${(data?.security.blacklisted_ips || 0) > 0
                            ? 'bg-red-500 text-white'
                            : 'bg-emerald-500/10 text-emerald-400'
                        }`}>
                        {data?.security.blacklisted_ips || 0} Blocked IPs
                    </span>
                </div>
            </header>

            <div className="flex-1 overflow-y-auto p-8 space-y-8">

                {/* THREAT LANDSCAPE */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div className="bg-[#0f172a] border border-[#1e293b] p-6 rounded-xl">
                        <h3 className="font-bold text-white mb-4">Security Events (Today)</h3>
                        <div className="h-64">
                            <Chart
                                type="bar"
                                height={250}
                                options={chartOptions}
                                series={[{ name: 'Events', data: [data?.security.rate_limited_count || 0, 0, 0, data?.security.blacklisted_ips || 0, 0] }]}
                            />
                        </div>
                    </div>
                    <div className="bg-[#0f172a] border border-[#1e293b] p-6 rounded-xl">
                        <h3 className="font-bold text-white mb-4">Active Users</h3>
                        <div className="text-5xl font-mono text-white mb-4">{data?.security.active_users || 0}</div>
                        <div className="text-sm text-slate-400">
                            Currently active sessions based on rate limit tracking
                        </div>
                        <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
                            <div className="bg-[#020617] p-3 rounded">
                                <div className="text-slate-500">Rate Limited</div>
                                <div className="text-white font-mono">{data?.security.rate_limited_count || 0}</div>
                            </div>
                            <div className="bg-[#020617] p-3 rounded">
                                <div className="text-slate-500">Blacklisted IPs</div>
                                <div className="text-red-400 font-mono">{data?.security.blacklisted_ips || 0}</div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* AUDIT & ADMINS */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* System Alerts as Audit Log */}
                    <div className="lg:col-span-2 bg-[#0f172a] border border-[#1e293b] rounded-xl p-6">
                        <h3 className="font-bold text-white mb-4">System Events Log</h3>
                        <div className="font-mono text-xs space-y-2 h-64 overflow-y-auto bg-black p-4 rounded border border-[#1e293b]">
                            {alerts.length === 0 ? (
                                <div className="text-slate-500 text-center">No recent system events</div>
                            ) : (
                                alerts.map((alert, i) => (
                                    <div key={i} className="flex gap-4">
                                        <span className="text-slate-500">[{alert.timestamp ? new Date(alert.timestamp).toLocaleTimeString() : 'N/A'}]</span>
                                        <span className={
                                            alert.severity === 'critical' ? 'text-red-400' :
                                                alert.severity === 'warning' ? 'text-yellow-400' : 'text-blue-400'
                                        }>{alert.type}</span>
                                        <span className="text-slate-300">{alert.message}</span>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>

                    {/* Admin Info */}
                    <div className="bg-[#0f172a] border border-[#1e293b] rounded-xl p-6">
                        <h3 className="font-bold text-white mb-4">Current Admin</h3>
                        <div className="flex items-center gap-3 mb-4">
                            <div className="w-10 h-10 rounded-full bg-[#6366f1] flex items-center justify-center text-white font-bold">
                                SA
                            </div>
                            <div>
                                <div className="text-white text-sm font-bold">{data?.accessed_by?.admin_email || 'Unknown'}</div>
                                <div className="text-[10px] text-slate-500 uppercase">{data?.accessed_by?.role || 'Admin'}</div>
                            </div>
                            <span className="ml-auto w-2 h-2 rounded-full bg-emerald-500"></span>
                        </div>
                        <div className="text-xs text-slate-500 mb-4">
                            Admin ID: {data?.accessed_by?.admin_id || 'N/A'}
                        </div>
                        <div className="text-xs text-slate-600 border-t border-[#1e293b] pt-4">
                            Auth Epoch: {data?.system.auth_epoch || 'N/A'}
                        </div>
                    </div>
                </div>

            </div>
        </>
    );
}
