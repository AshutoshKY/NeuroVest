'use client';

/**
 * User Intelligence Page
 * 
 * Real-time user session monitoring with:
 * - Active sessions from backend (deduplicated by user)
 * - Login/logout capabilities  
 * - Device, IP, location breakdown
 * - Rate limited users
 * - Real activity stats from LoginHistory
 * - User Management: Search, view, logout, delete users
 * 
 * NO AUTO-POLLING - manual refresh only
 */

import { useState } from 'react';
import useSWR from 'swr';
import apiClient from '@/lib/api';
import { useUserSearch, forceLogoutUser, deleteUser } from '@/hooks/useAdminAPI';
import { Users, Globe, Smartphone, Monitor, Tablet, Clock, LogOut, RefreshCw, MapPin, Wifi, Ban, Activity, TrendingUp, Calendar, Search, Trash2, ChevronDown, ChevronUp, User2, Shield, BarChart3 } from 'lucide-react';
import dynamic from 'next/dynamic';

const Chart = dynamic(() => import('react-apexcharts'), { ssr: false });

const fetcher = async (url: string) => {
    const response = await apiClient.get(url);
    return response.data;
};

// Session type from backend
interface UserSession {
    user_id: number;
    email: string;
    role: string;
    session_id: number;
    ip: string;
    device: 'desktop' | 'mobile' | 'tablet';
    browser: string;
    device_name: string;
    location: string;
    login_time: string;
    last_active: string;
    request_count: number;
    is_rate_limited: boolean;
}

interface ActivityStats {
    logins_24h: number;
    logouts_24h: number;
    rate_limited_24h: number;
    jwt_resets_24h: number;
    jwt_refreshes_24h: number;
    failed_logins_24h: number;
    unique_users_24h: number;
    unique_users_week: number;
    unique_users_month: number;
    unique_users_year: number;
    total_registered_users: number;
    total_logins: number;
    total_logouts: number;
    active_now: number;
}

interface BehavioralStats {
    user_segments: {
        power_users: number;
        normal_users: number;
        idle_users: number;
        abusive_users: number;
    };
    segment_traffic: {
        power_users: number;
        normal_users: number;
        idle_users: number;
        abusive_users: number;
    };
    action_breakdown: {
        ai_requests: number;
        analysis_requests: number;
        api_requests: number;
    };
    traffic_concentration: {
        top_10_percent_traffic: number;
        top_users_count: number;
    };
    per_user_averages: {
        avg_requests: number;
        avg_errors: number;
    };
    total_active_users_today: number;
    total_requests_today: number;
}

interface SessionsResponse {
    sessions: UserSession[];
    total_sessions: number;
    unique_ips: number;
    rate_limited_count: number;
    device_breakdown: { desktop: number; mobile: number; tablet: number };
    locations: Record<string, number>;
    activity: ActivityStats;
    behavioral_stats?: BehavioralStats;
}

// Device icon component
function DeviceIcon({ device }: { device: string }) {
    const deviceLower = device?.toLowerCase() || 'desktop';
    switch (deviceLower) {
        case 'mobile': return <Smartphone className="w-4 h-4 text-emerald-400" />;
        case 'tablet': return <Tablet className="w-4 h-4 text-amber-400" />;
        default: return <Monitor className="w-4 h-4 text-blue-400" />;
    }
}

// User Management Section Component
function UserManagementSection() {
    const [searchQuery, setSearchQuery] = useState('');
    const [debouncedQuery, setDebouncedQuery] = useState('');
    const [page, setPage] = useState(1);
    const [actionLoading, setActionLoading] = useState<number | null>(null);
    const [confirmDelete, setConfirmDelete] = useState<number | null>(null);

    const { users, totalUsers, totalPages, isLoading, refresh } = useUserSearch(debouncedQuery, page, 15);

    // Debounce search
    const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
        setSearchQuery(e.target.value);
        setTimeout(() => {
            setDebouncedQuery(e.target.value);
            setPage(1);
        }, 300);
    };

    const handleForceLogout = async (userId: number) => {
        setActionLoading(userId);
        const result = await forceLogoutUser(userId);
        if (result.success) {
            refresh();
        } else {
            alert(result.error || 'Failed to logout user');
        }
        setActionLoading(null);
    };

    const handleDelete = async (userId: number) => {
        setActionLoading(userId);
        const result = await deleteUser(userId);
        if (result.success) {
            setConfirmDelete(null);
            refresh();
        } else {
            alert(result.error || 'Failed to delete user');
        }
        setActionLoading(null);
    };

    return (
        <section>
            <div className="flex items-center gap-3 mb-4">
                <span className="w-1.5 h-6 bg-orange-500 rounded" />
                <h2 className="text-lg font-bold text-white">User Management</h2>
                <span className="text-xs text-slate-500">({totalUsers} total users)</span>
            </div>

            {/* Search Bar */}
            <div className="mb-4 flex gap-4">
                <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                    <input
                        type="text"
                        placeholder="Search by email or name..."
                        value={searchQuery}
                        onChange={handleSearch}
                        className="w-full bg-[#0f172a] border border-[#1e293b] rounded-lg pl-10 pr-4 py-2.5 text-white text-sm focus:border-indigo-500 focus:outline-none"
                    />
                </div>
                <button
                    onClick={() => refresh()}
                    disabled={isLoading}
                    className="px-4 py-2 bg-indigo-500 hover:bg-indigo-600 text-white rounded-lg text-sm font-bold transition flex items-center gap-2 disabled:opacity-50"
                >
                    <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
                    Refresh
                </button>
            </div>

            {/* Users Table */}
            <div className="bg-[#0f172a] border border-[#1e293b] rounded-xl overflow-hidden">
                {isLoading ? (
                    <div className="p-8 text-center text-slate-500">Loading users...</div>
                ) : users.length === 0 ? (
                    <div className="p-8 text-center text-slate-500">No users found</div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead className="bg-[#020617] border-b border-[#1e293b]">
                                <tr className="text-slate-500 text-xs uppercase">
                                    <th className="py-3 px-4 text-left">User</th>
                                    <th className="py-3 px-4 text-center">Status</th>
                                    <th className="py-3 px-4 text-center">Sessions</th>
                                    <th className="py-3 px-4 text-center">Logins</th>
                                    <th className="py-3 px-4 text-center">Analyses</th>
                                    <th className="py-3 px-4 text-center">Last Login</th>
                                    <th className="py-3 px-4 text-right">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-[#1e293b]">
                                {users.map(user => (
                                    <tr key={user.id} className="hover:bg-[#020617]/50 transition">
                                        <td className="py-3 px-4">
                                            <div className="flex items-center gap-3">
                                                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${user.is_admin ? 'bg-amber-500/20' : 'bg-indigo-500/20'}`}>
                                                    {user.is_admin ? (
                                                        <Shield className="w-4 h-4 text-amber-400" />
                                                    ) : (
                                                        <User2 className="w-4 h-4 text-indigo-400" />
                                                    )}
                                                </div>
                                                <div>
                                                    <div className="text-white font-medium">{user.email}</div>
                                                    <div className="text-xs text-slate-500">{user.full_name || 'No name'}</div>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="py-3 px-4 text-center">
                                            {user.has_active_session ? (
                                                <span className="inline-flex items-center gap-1 px-2 py-1 bg-emerald-500/20 text-emerald-400 rounded text-xs font-bold">
                                                    <Wifi className="w-3 h-3" /> Online
                                                </span>
                                            ) : (
                                                <span className="text-slate-500 text-xs">Offline</span>
                                            )}
                                        </td>
                                        <td className="py-3 px-4 text-center">
                                            <span className={`font-mono ${user.active_sessions > 0 ? 'text-emerald-400' : 'text-slate-500'}`}>
                                                {user.active_sessions}
                                            </span>
                                        </td>
                                        <td className="py-3 px-4 text-center">
                                            <span className="font-mono text-blue-400">{user.total_logins}</span>
                                        </td>
                                        <td className="py-3 px-4 text-center">
                                            <span className="font-mono text-purple-400">{user.analysis_count}</span>
                                        </td>
                                        <td className="py-3 px-4 text-center text-xs text-slate-400">
                                            {user.last_login ? new Date(user.last_login).toLocaleString() : 'Never'}
                                        </td>
                                        <td className="py-3 px-4 text-right">
                                            <div className="flex items-center justify-end gap-2">
                                                {user.has_active_session && !user.is_admin && (
                                                    <button
                                                        onClick={() => handleForceLogout(user.id)}
                                                        disabled={actionLoading === user.id}
                                                        className="px-2 py-1 bg-amber-500/10 text-amber-400 hover:bg-amber-500 hover:text-white rounded text-xs font-bold transition disabled:opacity-50"
                                                    >
                                                        <LogOut className="w-3 h-3 inline-block" />
                                                    </button>
                                                )}
                                                {!user.is_admin && (
                                                    confirmDelete === user.id ? (
                                                        <div className="flex items-center gap-1">
                                                            <button
                                                                onClick={() => handleDelete(user.id)}
                                                                disabled={actionLoading === user.id}
                                                                className="px-2 py-1 bg-red-500 text-white rounded text-xs font-bold"
                                                            >
                                                                {actionLoading === user.id ? '...' : 'Confirm'}
                                                            </button>
                                                            <button
                                                                onClick={() => setConfirmDelete(null)}
                                                                className="px-2 py-1 bg-slate-600 text-white rounded text-xs"
                                                            >
                                                                Cancel
                                                            </button>
                                                        </div>
                                                    ) : (
                                                        <button
                                                            onClick={() => setConfirmDelete(user.id)}
                                                            className="px-2 py-1 bg-red-500/10 text-red-400 hover:bg-red-500 hover:text-white rounded text-xs font-bold transition"
                                                        >
                                                            <Trash2 className="w-3 h-3 inline-block" />
                                                        </button>
                                                    )
                                                )}
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}

                {/* Pagination */}
                {totalPages > 1 && (
                    <div className="flex items-center justify-between p-4 border-t border-[#1e293b]">
                        <div className="text-xs text-slate-500">
                            Page {page} of {totalPages} ({totalUsers} users)
                        </div>
                        <div className="flex gap-2">
                            <button
                                onClick={() => setPage(p => Math.max(1, p - 1))}
                                disabled={page === 1}
                                className="px-3 py-1 bg-[#1e293b] text-white rounded text-xs disabled:opacity-50"
                            >
                                Previous
                            </button>
                            <button
                                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                                disabled={page === totalPages}
                                className="px-3 py-1 bg-[#1e293b] text-white rounded text-xs disabled:opacity-50"
                            >
                                Next
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </section>
    );
}

export default function UsersPage() {
    // NO AUTO-POLLING - refreshInterval: 0
    const { data: sessionsData, isLoading, mutate: refreshSessions } = useSWR<SessionsResponse>(
        '/admin/dashboard/active-sessions',
        fetcher,
        { refreshInterval: 0 }  // Manual refresh only
    );

    const [loggingOut, setLoggingOut] = useState<number | null>(null);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [activeTab, setActiveTab] = useState<'now' | '24h' | 'week' | 'month' | 'year'>('24h');

    // Use real data or fallback
    const sessions = sessionsData?.sessions || [];
    const totalSessions = sessionsData?.total_sessions || 0;
    const uniqueIPs = sessionsData?.unique_ips || 0;
    const rateLimited = sessionsData?.rate_limited_count || 0;
    const deviceBreakdown = sessionsData?.device_breakdown || { desktop: 0, mobile: 0, tablet: 0 };
    const locations = sessionsData?.locations || {};
    const activity = sessionsData?.activity || {
        logins_24h: 0,
        logouts_24h: 0,
        rate_limited_24h: 0,
        jwt_resets_24h: 0,
        jwt_refreshes_24h: 0,
        failed_logins_24h: 0,
        unique_users_24h: 0,
        unique_users_week: 0,
        unique_users_month: 0,
        unique_users_year: 0,
        total_registered_users: 0,
        total_logins: 0,
        total_logouts: 0,
        active_now: 0
    };

    // Behavioral stats from real per-user tracking
    const behavioralStats = sessionsData?.behavioral_stats || {
        user_segments: { power_users: 0, normal_users: 0, idle_users: 0, abusive_users: 0 },
        segment_traffic: { power_users: 0, normal_users: 0, idle_users: 0, abusive_users: 0 },
        action_breakdown: { ai_requests: 0, analysis_requests: 0, api_requests: 0 },
        traffic_concentration: { top_10_percent_traffic: 0, top_users_count: 0 },
        per_user_averages: { avg_requests: 0, avg_errors: 0 },
        total_active_users_today: 0,
        total_requests_today: 0
    };

    // Refresh handler
    const handleRefresh = async () => {
        setIsRefreshing(true);
        await refreshSessions();
        setIsRefreshing(false);
    };

    // Logout user
    const handleLogout = async (userId: number) => {
        setLoggingOut(userId);
        try {
            await apiClient.post(`/admin/dashboard/logout-user/${userId}`);
            await refreshSessions();
        } catch (e) {
            console.error('Failed to logout user:', e);
        }
        setLoggingOut(null);
    };

    // Flush all sessions
    const handleFlushAll = async () => {
        if (!confirm('Are you sure you want to logout ALL users?')) return;
        for (const session of sessions) {
            await apiClient.post(`/admin/dashboard/logout-user/${session.user_id}`);
        }
        await refreshSessions();
    };

    // Chart configs
    const deviceChartOptions: ApexCharts.ApexOptions = {
        chart: { type: 'bar', toolbar: { show: false }, background: 'transparent' },
        theme: { mode: 'dark' },
        grid: { borderColor: '#1e293b', strokeDashArray: 3 },
        colors: ['#3b82f6', '#10b981', '#f59e0b'],
        plotOptions: { bar: { borderRadius: 6, horizontal: false, columnWidth: '50%', distributed: true } },
        xaxis: {
            categories: ['Desktop', 'Mobile', 'Tablet'],
            labels: { style: { colors: '#94a3b8' } }
        },
        yaxis: {
            min: 0,
            max: Math.max(deviceBreakdown.desktop, deviceBreakdown.mobile, deviceBreakdown.tablet, 3) + 1,
            labels: { style: { colors: '#94a3b8' }, formatter: (val) => Math.round(val).toString() },
            title: { text: 'Sessions', style: { color: '#64748b' } }
        },
        legend: { show: false },
        dataLabels: { enabled: true, style: { colors: ['#fff'] } },
        tooltip: { theme: 'dark', y: { formatter: (val) => `${val} sessions` } }
    };

    const activityChartOptions: ApexCharts.ApexOptions = {
        chart: { type: 'bar', toolbar: { show: false }, background: 'transparent' },
        theme: { mode: 'dark' },
        grid: { borderColor: '#1e293b' },
        colors: ['#10b981', '#6366f1', '#ef4444', '#f59e0b'],
        plotOptions: { bar: { borderRadius: 4, horizontal: false, columnWidth: '70%' } },
        xaxis: {
            categories: ['Logins', 'Unique Users', 'Logouts', 'Rate Limited'],
            labels: { style: { colors: '#94a3b8', fontSize: '10px' } }
        },
        yaxis: { labels: { style: { colors: '#94a3b8' } } },
        legend: { show: false },
        dataLabels: { enabled: true, style: { colors: ['#fff'], fontSize: '10px' } },
        tooltip: { theme: 'dark' }
    };

    if (isLoading) {
        return (
            <>
                <header className="h-16 px-8 border-b border-[#1e293b] flex items-center bg-[#0f172a]/50">
                    <h1 className="text-xl font-bold text-white flex items-center gap-2"><Users className="w-5 h-5" />User Intelligence</h1>
                </header>
                <div className="p-8 animate-pulse space-y-8"><div className="bg-[#0f172a] h-96 rounded-xl"></div></div>
            </>
        );
    }

    // Location data for chart
    const topLocations = Object.entries(locations)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5);

    return (
        <>
            <header className="h-16 px-8 border-b border-[#1e293b] flex items-center justify-between bg-[#0f172a]/50 backdrop-blur sticky top-0 z-20">
                <h1 className="text-xl font-bold text-white flex items-center gap-2"><Users className="w-5 h-5" />User Intelligence</h1>
                <div className="flex items-center gap-6">
                    <div className="flex gap-4 text-xs">
                        <div className="flex items-center gap-2"><Wifi className="w-4 h-4 text-emerald-400" /><span className="text-emerald-400 font-bold">{totalSessions} Active</span></div>
                        <div className="flex items-center gap-2"><Globe className="w-4 h-4" /><span>{uniqueIPs} IPs</span></div>
                        <div className="flex items-center gap-2"><Ban className="w-4 h-4 text-red-400" /><span className="text-red-400">{rateLimited} Rate Limited</span></div>
                    </div>
                    <button
                        onClick={handleRefresh}
                        disabled={isRefreshing}
                        className="flex items-center gap-2 px-4 py-2 bg-indigo-500 hover:bg-indigo-600 text-white rounded-lg text-xs font-bold transition disabled:opacity-50"
                    >
                        <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
                        Refresh
                    </button>
                </div>
            </header>

            <div className="flex-1 overflow-y-auto p-8 space-y-6">

                {/* ACTIVE USERS TABS SECTION */}
                <div className="bg-[#0f172a] border border-[#1e293b] rounded-xl p-6">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="font-bold text-white flex items-center gap-2"><Activity className="w-4 h-4" />Active Users</h3>
                        <div className="flex gap-1 bg-[#1e293b] p-1 rounded-lg">
                            {(['now', '24h', 'week', 'month', 'year'] as const).map(tab => (
                                <button
                                    key={tab}
                                    onClick={() => setActiveTab(tab)}
                                    className={`px-3 py-1.5 text-xs font-bold rounded transition ${activeTab === tab ? 'bg-indigo-500 text-white' : 'text-slate-400 hover:text-white'}`}
                                >
                                    {tab === 'now' ? 'Now' : tab === '24h' ? '24h' : tab === 'week' ? 'Week' : tab === 'month' ? 'Month' : 'Year'}
                                </button>
                            ))}
                        </div>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                        <div className={`p-4 rounded-lg border ${activeTab === 'now' ? 'bg-emerald-500/10 border-emerald-500/30' : 'bg-[#020617] border-[#1e293b]'}`}>
                            <div className="text-xs text-slate-500">Active Now (1h)</div>
                            <div className={`text-3xl font-mono mt-1 ${activeTab === 'now' ? 'text-emerald-400' : 'text-white'}`}>{activity.active_now}</div>
                        </div>
                        <div className={`p-4 rounded-lg border ${activeTab === '24h' ? 'bg-indigo-500/10 border-indigo-500/30' : 'bg-[#020617] border-[#1e293b]'}`}>
                            <div className="text-xs text-slate-500">Last 24 Hours</div>
                            <div className={`text-3xl font-mono mt-1 ${activeTab === '24h' ? 'text-indigo-400' : 'text-white'}`}>{activity.unique_users_24h}</div>
                        </div>
                        <div className={`p-4 rounded-lg border ${activeTab === 'week' ? 'bg-purple-500/10 border-purple-500/30' : 'bg-[#020617] border-[#1e293b]'}`}>
                            <div className="text-xs text-slate-500">Last 7 Days</div>
                            <div className={`text-3xl font-mono mt-1 ${activeTab === 'week' ? 'text-purple-400' : 'text-white'}`}>{activity.unique_users_week}</div>
                        </div>
                        <div className={`p-4 rounded-lg border ${activeTab === 'month' ? 'bg-blue-500/10 border-blue-500/30' : 'bg-[#020617] border-[#1e293b]'}`}>
                            <div className="text-xs text-slate-500">Last 30 Days</div>
                            <div className={`text-3xl font-mono mt-1 ${activeTab === 'month' ? 'text-blue-400' : 'text-white'}`}>{activity.unique_users_month}</div>
                        </div>
                        <div className={`p-4 rounded-lg border ${activeTab === 'year' ? 'bg-amber-500/10 border-amber-500/30' : 'bg-[#020617] border-[#1e293b]'}`}>
                            <div className="text-xs text-slate-500">Last Year</div>
                            <div className={`text-3xl font-mono mt-1 ${activeTab === 'year' ? 'text-amber-400' : 'text-white'}`}>{activity.unique_users_year}</div>
                        </div>
                    </div>
                </div>

                {/* USER STATS GRID */}
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-4">
                    <div className="bg-[#0f172a] border border-emerald-500/30 p-4 rounded-xl">
                        <div className="text-xs text-slate-500">Active Sessions</div>
                        <div className="text-2xl font-mono text-emerald-400 mt-1">{totalSessions}</div>
                    </div>
                    <div className="bg-[#0f172a] border border-[#1e293b] p-4 rounded-xl">
                        <div className="text-xs text-slate-500">Total Registered</div>
                        <div className="text-2xl font-mono text-white mt-1">{activity.total_registered_users}</div>
                    </div>
                    <div className="bg-[#0f172a] border border-[#1e293b] p-4 rounded-xl">
                        <div className="text-xs text-slate-500">Logins (24h)</div>
                        <div className="text-2xl font-mono text-emerald-400 mt-1">{activity.logins_24h}</div>
                    </div>
                    <div className="bg-[#0f172a] border border-[#1e293b] p-4 rounded-xl">
                        <div className="text-xs text-slate-500">Logouts (24h)</div>
                        <div className="text-2xl font-mono text-amber-400 mt-1">{activity.logouts_24h}</div>
                    </div>
                    <div className="bg-[#0f172a] border border-[#1e293b] p-4 rounded-xl">
                        <div className="text-xs text-slate-500">All-time Logins</div>
                        <div className="text-2xl font-mono text-indigo-400 mt-1">{activity.total_logins.toLocaleString()}</div>
                    </div>
                    <div className="bg-[#0f172a] border border-[#1e293b] p-4 rounded-xl">
                        <div className="text-xs text-slate-500">All-time Logouts</div>
                        <div className="text-2xl font-mono text-purple-400 mt-1">{activity.total_logouts.toLocaleString()}</div>
                    </div>
                    <div className="bg-[#0f172a] border border-red-500/20 p-4 rounded-xl">
                        <div className="text-xs text-slate-500">Failed (24h)</div>
                        <div className="text-2xl font-mono text-red-400 mt-1">{activity.failed_logins_24h}</div>
                    </div>
                    <div className="bg-[#0f172a] border border-red-500/30 p-4 rounded-xl">
                        <div className="text-xs text-slate-500">Rate Limited</div>
                        <div className="text-2xl font-mono text-red-400 mt-1">{rateLimited}</div>
                    </div>
                    <div className="bg-[#0f172a] border border-cyan-500/20 p-4 rounded-xl">
                        <div className="text-xs text-slate-500">Token Refreshes (24h)</div>
                        <div className="text-2xl font-mono text-cyan-400 mt-1">{activity.jwt_refreshes_24h}</div>
                    </div>
                </div>

                {/* ==================== USER SEGMENTATION SECTION ==================== */}
                <section>
                    <div className="flex items-center gap-3 mb-4">
                        <span className="w-1.5 h-6 bg-purple-500 rounded" />
                        <h2 className="text-lg font-bold text-white">User Segmentation</h2>
                        <span className="text-xs text-slate-500">(Based on today&apos;s request activity)</span>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {/* Power Users */}
                        <div className="bg-[#0f172a] border border-emerald-500/30 p-5 rounded-xl">
                            <div className="flex items-center gap-2 mb-2">
                                <TrendingUp className="w-4 h-4 text-emerald-400" />
                                <span className="text-xs text-emerald-400 uppercase font-bold">Power Users</span>
                            </div>
                            <div className="text-3xl font-mono text-emerald-400">{behavioralStats.user_segments.power_users}</div>
                            <div className="text-xs text-slate-500 mt-1">&gt;100 requests/day</div>
                            <div className="mt-3 w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                                <div className="h-full bg-emerald-500" style={{ width: `${behavioralStats.segment_traffic.power_users}%` }} />
                            </div>
                            <div className="text-xs text-slate-400 mt-1">{behavioralStats.segment_traffic.power_users}% of traffic</div>
                        </div>
                        {/* Normal Users */}
                        <div className="bg-[#0f172a] border border-blue-500/30 p-5 rounded-xl">
                            <div className="flex items-center gap-2 mb-2">
                                <Users className="w-4 h-4 text-blue-400" />
                                <span className="text-xs text-blue-400 uppercase font-bold">Normal</span>
                            </div>
                            <div className="text-3xl font-mono text-blue-400">{behavioralStats.user_segments.normal_users}</div>
                            <div className="text-xs text-slate-500 mt-1">10-100 requests/day</div>
                            <div className="mt-3 w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                                <div className="h-full bg-blue-500" style={{ width: `${behavioralStats.segment_traffic.normal_users}%` }} />
                            </div>
                            <div className="text-xs text-slate-400 mt-1">{behavioralStats.segment_traffic.normal_users}% of traffic</div>
                        </div>
                        {/* Idle Users */}
                        <div className="bg-[#0f172a] border border-slate-500/30 p-5 rounded-xl">
                            <div className="flex items-center gap-2 mb-2">
                                <Clock className="w-4 h-4 text-slate-400" />
                                <span className="text-xs text-slate-400 uppercase font-bold">Idle</span>
                            </div>
                            <div className="text-3xl font-mono text-slate-400">{behavioralStats.user_segments.idle_users}</div>
                            <div className="text-xs text-slate-500 mt-1">&lt;10 requests/day</div>
                            <div className="mt-3 w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                                <div className="h-full bg-slate-500" style={{ width: `${behavioralStats.segment_traffic.idle_users}%` }} />
                            </div>
                            <div className="text-xs text-slate-400 mt-1">{behavioralStats.segment_traffic.idle_users}% of traffic</div>
                        </div>
                        {/* Abusive Users */}
                        <div className="bg-[#0f172a] border border-red-500/30 p-5 rounded-xl">
                            <div className="flex items-center gap-2 mb-2">
                                <Ban className="w-4 h-4 text-red-400" />
                                <span className="text-xs text-red-400 uppercase font-bold">Abusive</span>
                            </div>
                            <div className="text-3xl font-mono text-red-400">{behavioralStats.user_segments.abusive_users}</div>
                            <div className="text-xs text-slate-500 mt-1">&gt;5% errors or rate-limited</div>
                            <div className="mt-3 w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                                <div className="h-full bg-red-500" style={{ width: `${behavioralStats.segment_traffic.abusive_users}%` }} />
                            </div>
                            <div className="text-xs text-slate-400 mt-1">{behavioralStats.segment_traffic.abusive_users}% of traffic</div>
                        </div>
                    </div>
                </section>

                {/* ==================== ACTIVITY INTELLIGENCE SECTION ==================== */}
                <section>
                    <div className="flex items-center gap-3 mb-4">
                        <span className="w-1.5 h-6 bg-indigo-500 rounded" />
                        <h2 className="text-lg font-bold text-white">Activity Intelligence</h2>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        {/* Action Breakdown */}
                        <div className="bg-[#0f172a] border border-[#1e293b] p-6 rounded-xl">
                            <h4 className="text-xs text-slate-500 uppercase font-bold mb-4">Action Breakdown (Today)</h4>
                            <div className="space-y-4">
                                <div>
                                    <div className="flex justify-between text-sm mb-1">
                                        <span className="text-purple-400">AI Requests</span>
                                        <span className="font-mono text-white">{behavioralStats.action_breakdown.ai_requests.toLocaleString()}</span>
                                    </div>
                                    <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                                        <div className="h-full bg-purple-500" style={{
                                            width: `${((behavioralStats.action_breakdown.ai_requests || 0) / (behavioralStats.total_requests_today || 1)) * 100}%`
                                        }} />
                                    </div>
                                </div>
                                <div>
                                    <div className="flex justify-between text-sm mb-1">
                                        <span className="text-blue-400">Analysis Requests</span>
                                        <span className="font-mono text-white">{behavioralStats.action_breakdown.analysis_requests.toLocaleString()}</span>
                                    </div>
                                    <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                                        <div className="h-full bg-blue-500" style={{
                                            width: `${((behavioralStats.action_breakdown.analysis_requests || 0) / (behavioralStats.total_requests_today || 1)) * 100}%`
                                        }} />
                                    </div>
                                </div>
                                <div>
                                    <div className="flex justify-between text-sm mb-1">
                                        <span className="text-slate-400">API Requests</span>
                                        <span className="font-mono text-white">{behavioralStats.action_breakdown.api_requests.toLocaleString()}</span>
                                    </div>
                                    <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                                        <div className="h-full bg-slate-500" style={{
                                            width: `${((behavioralStats.action_breakdown.api_requests || 0) / (behavioralStats.total_requests_today || 1)) * 100}%`
                                        }} />
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Traffic Concentration */}
                        <div className="bg-[#0f172a] border border-[#1e293b] p-6 rounded-xl">
                            <h4 className="text-xs text-slate-500 uppercase font-bold mb-4">Traffic Concentration</h4>
                            <div className="text-center py-4">
                                <div className="text-4xl font-mono text-amber-400">{behavioralStats.traffic_concentration.top_10_percent_traffic}%</div>
                                <div className="text-sm text-slate-400 mt-2">of traffic from top 10% users</div>
                                <div className="text-xs text-slate-500 mt-1">({behavioralStats.traffic_concentration.top_users_count} power users)</div>
                            </div>
                            <div className="mt-4 p-3 bg-[#020617] rounded-lg">
                                <div className="text-xs text-slate-500">Total Requests Today</div>
                                <div className="text-xl font-mono text-white">{behavioralStats.total_requests_today.toLocaleString()}</div>
                            </div>
                        </div>

                        {/* Per-User Averages */}
                        <div className="bg-[#0f172a] border border-[#1e293b] p-6 rounded-xl">
                            <h4 className="text-xs text-slate-500 uppercase font-bold mb-4">Per-User Averages</h4>
                            <div className="space-y-4">
                                <div className="p-4 bg-[#020617] rounded-lg">
                                    <div className="text-xs text-slate-500">Avg Requests/User</div>
                                    <div className="text-2xl font-mono text-emerald-400">{behavioralStats.per_user_averages.avg_requests}</div>
                                </div>
                                <div className="p-4 bg-[#020617] rounded-lg">
                                    <div className="text-xs text-slate-500">Avg Errors/User</div>
                                    <div className="text-2xl font-mono text-red-400">{behavioralStats.per_user_averages.avg_errors}</div>
                                </div>
                                <div className="p-4 bg-[#020617] rounded-lg">
                                    <div className="text-xs text-slate-500">Active Users Today</div>
                                    <div className="text-2xl font-mono text-blue-400">{behavioralStats.total_active_users_today}</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>

                {/* CHARTS ROW */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Device Breakdown - Bar Chart */}
                    <div className="bg-[#0f172a] border border-[#1e293b] p-6 rounded-xl">
                        <h3 className="font-bold text-white mb-4">Device Types</h3>
                        <Chart type="bar" height={220} options={deviceChartOptions}
                            series={[{ name: 'Sessions', data: [deviceBreakdown.desktop, deviceBreakdown.mobile, deviceBreakdown.tablet] }]} />
                        <div className="flex justify-center gap-6 mt-4 text-xs">
                            <div className="flex items-center gap-1"><Monitor className="w-3 h-3 text-blue-400" /><span className="text-slate-400">Desktop: {deviceBreakdown.desktop}</span></div>
                            <div className="flex items-center gap-1"><Smartphone className="w-3 h-3 text-emerald-400" /><span className="text-slate-400">Mobile: {deviceBreakdown.mobile}</span></div>
                            <div className="flex items-center gap-1"><Tablet className="w-3 h-3 text-amber-400" /><span className="text-slate-400">Tablet: {deviceBreakdown.tablet}</span></div>
                        </div>
                    </div>

                    {/* Activity Types - Real Data */}
                    <div className="bg-[#0f172a] border border-[#1e293b] p-6 rounded-xl">
                        <h3 className="font-bold text-white mb-4">User Activity (24h)</h3>
                        <Chart type="bar" height={220} options={activityChartOptions}
                            series={[{
                                name: 'Count', data: [
                                    activity.logins_24h,
                                    activity.unique_users_24h,
                                    activity.logouts_24h,
                                    activity.rate_limited_24h
                                ]
                            }]} />
                    </div>

                    {/* Geolocation */}
                    <div className="bg-[#0f172a] border border-[#1e293b] p-6 rounded-xl">
                        <h3 className="font-bold text-white mb-4">Geolocation</h3>
                        {topLocations.length > 0 ? (
                            <div className="space-y-3">
                                {topLocations.map(([loc, count], i) => (
                                    <div key={i}>
                                        <div className="flex justify-between text-xs mb-1">
                                            <span className="text-slate-400 flex items-center gap-1"><MapPin className="w-3 h-3" />{loc || 'Unknown'}</span>
                                            <span className="text-white font-mono">{count} ({Math.round(count / totalSessions * 100)}%)</span>
                                        </div>
                                        <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                                            <div className="bg-indigo-500 h-full rounded-full" style={{ width: `${(count / totalSessions) * 100}%` }}></div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="h-40 flex items-center justify-center text-slate-500 flex-col gap-2">
                                <Globe className="w-8 h-8 opacity-50" />
                                <span>No location data</span>
                            </div>
                        )}
                    </div>
                </div>

                {/* ACTIVE SESSIONS TABLE */}
                <div className="bg-[#0f172a] border border-[#1e293b] rounded-xl overflow-hidden">
                    <div className="p-4 border-b border-[#1e293b] flex items-center justify-between">
                        <h3 className="font-bold text-white">Active User Sessions (Unique Users)</h3>
                        <div className="flex gap-2">
                            <button onClick={handleRefresh} disabled={isRefreshing} className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-white text-xs font-bold rounded transition flex items-center gap-1 disabled:opacity-50">
                                <RefreshCw className={`w-3 h-3 ${isRefreshing ? 'animate-spin' : ''}`} />Refresh
                            </button>
                            <button onClick={handleFlushAll} className="px-3 py-1.5 bg-red-500/10 text-red-400 hover:bg-red-500 hover:text-white text-xs font-bold rounded transition flex items-center gap-1">
                                <RefreshCw className="w-3 h-3" />Flush All Sessions
                            </button>
                        </div>
                    </div>
                    {sessions.length === 0 ? (
                        <div className="p-8 text-center text-slate-500">No active sessions found</div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full text-xs">
                                <thead>
                                    <tr className="text-slate-500 border-b border-[#1e293b]">
                                        <th className="py-3 px-4 text-left font-medium">User</th>
                                        <th className="py-3 px-4 text-left font-medium">IP Address</th>
                                        <th className="py-3 px-4 text-left font-medium">Device</th>
                                        <th className="py-3 px-4 text-left font-medium">Location</th>
                                        <th className="py-3 px-4 text-left font-medium">Login Time</th>
                                        <th className="py-3 px-4 text-left font-medium">Last Active</th>
                                        <th className="py-3 px-4 text-right font-medium">Requests</th>
                                        <th className="py-3 px-4 text-left font-medium">Status</th>
                                        <th className="py-3 px-4 text-right font-medium">Action</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {sessions.map((session) => (
                                        <tr key={session.session_id} className={`border-b border-[#1e293b]/50 hover:bg-[#1e293b]/30 ${session.is_rate_limited ? 'bg-red-500/5' : ''}`}>
                                            <td className="py-3 px-4">
                                                <div className="font-medium text-white">{session.email}</div>
                                                <div className="text-slate-500">ID: {session.user_id} • {session.role}</div>
                                            </td>
                                            <td className="py-3 px-4 font-mono text-slate-400">{session.ip}</td>
                                            <td className="py-3 px-4">
                                                <div className="flex items-center gap-2">
                                                    <DeviceIcon device={session.device} />
                                                    <span className="text-slate-400">{session.browser}</span>
                                                </div>
                                            </td>
                                            <td className="py-3 px-4 text-slate-400"><span className="flex items-center gap-1"><MapPin className="w-3 h-3" />{session.location || 'Unknown'}</span></td>
                                            <td className="py-3 px-4 text-slate-500">{session.login_time ? new Date(session.login_time).toLocaleTimeString() : '-'}</td>
                                            <td className="py-3 px-4 text-slate-400">{session.last_active ? new Date(session.last_active).toLocaleTimeString() : '-'}</td>
                                            <td className="py-3 px-4 text-right font-mono text-white">{session.request_count}</td>
                                            <td className="py-3 px-4">
                                                {session.is_rate_limited ? (
                                                    <span className="px-2 py-0.5 rounded text-red-400 bg-red-400/10 text-[10px] font-bold">RATE LIMITED</span>
                                                ) : (
                                                    <span className="px-2 py-0.5 rounded text-emerald-400 bg-emerald-400/10 text-[10px] font-bold">ACTIVE</span>
                                                )}
                                            </td>
                                            <td className="py-3 px-4 text-right">
                                                <button
                                                    onClick={() => handleLogout(session.user_id)}
                                                    disabled={loggingOut === session.user_id}
                                                    className="px-2 py-1 rounded bg-red-500/10 text-red-400 hover:bg-red-500 hover:text-white text-[10px] font-bold flex items-center gap-1 ml-auto transition disabled:opacity-50"
                                                >
                                                    <LogOut className="w-3 h-3" />
                                                    {loggingOut === session.user_id ? '...' : 'Logout'}
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>

                {/* RATE LIMITED USERS */}
                {sessions.filter(s => s.is_rate_limited).length > 0 && (
                    <div className="bg-[#0f172a] border border-red-500/30 rounded-xl p-6">
                        <h3 className="font-bold text-red-400 mb-4 flex items-center gap-2"><Ban className="w-4 h-4" />Rate Limited Users</h3>
                        <div className="space-y-2">
                            {sessions.filter(s => s.is_rate_limited).map(s => (
                                <div key={s.session_id} className="flex items-center justify-between bg-red-500/5 border border-red-500/20 rounded p-3">
                                    <div>
                                        <span className="text-white font-medium">{s.email}</span>
                                        <span className="text-slate-500 ml-3">IP: {s.ip}</span>
                                    </div>
                                    <div className="flex items-center gap-4">
                                        <span className="text-red-400 text-xs">{s.request_count} requests</span>
                                        <button className="px-2 py-1 bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500 hover:text-white text-xs rounded transition">Remove Limit</button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* ==================== USER MANAGEMENT SECTION ==================== */}
                <UserManagementSection />

            </div>
        </>
    );
}
