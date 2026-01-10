'use client';

/**
 * Admin Dashboard API Hooks
 * 
 * All admin API calls are centralized here.
 * Every hook handles loading, error, and data states.
 */

import useSWR from 'swr';
import { apiClient } from '@/lib/api';

// Types matching backend responses
interface DashboardOverview {
    timestamp: string;
    overall_health: 'healthy' | 'degraded' | 'down';
    system: {
        uptime: string;
        active_kill_switches: number;
        kill_switch_names: string[];
        auth_epoch: number;
        maintenance_mode: boolean;
    };
    infrastructure: {
        redis: { status: string; memory_mb: number; connections: number; hit_rate: number };
        mysql: { status: string; connections: number; tables: number; rows: number };
        chromadb: { status: string; documents: number; collections: number };
    };
    traffic: {
        requests_per_second: number;
        total_requests_1h: number;
        avg_latency_ms: number;
        error_rate_percent: number;
        unique_users_1h: number;
    };
    ai: {
        requests_today: number;
        tokens_today: number;
        cost_today_usd: number;
        guardrail_rejections: number;
    };
    security: {
        blacklisted_ips: number;
        active_users: number;
        rate_limited_count: number;
    };
}

interface DashboardAlerts {
    alert_count: number;
    alerts: Array<{
        severity: 'critical' | 'warning' | 'info';
        type: string;
        message: string;
        details?: Record<string, unknown>;
        timestamp: string | null;
    }>;
    checked_at: string;
}

interface KillSwitch {
    switch_type: string;
    is_active: boolean;
    activated_by: number | null;
    activated_at: string | null;
    reason: string | null;
}

interface KillSwitchStatus {
    switches: Record<string, KillSwitch>;
}

interface AISummary {
    date: string;
    total_requests: number;
    total_tokens: number;
    total_cost_usd: number;
    avg_tokens_per_request: number;
    guardrail_rejections: number;
    timestamp: string;
}

interface AIHourly {
    hours_requested: number;
    data_points: number;
    totals: {
        total_requests: number;
        total_tokens: number;
        total_cost_usd: number;
        total_errors: number;
    };
    hourly: Array<{
        hour: string;
        total_requests: number;
        prompt_tokens: number;
        completion_tokens: number;
        total_tokens: number;
        total_cost_usd: number;
        avg_latency_ms: number;
        errors: number;
    }>;
}

interface SessionStatus {
    auth_epoch: number;
    auth_epoch_iso: string;
    invalidation_method: string;
    per_user_logout_enabled: boolean;
}

interface InfrastructureMetrics {
    redis: { connected: boolean; memory_used_mb: number; hit_rate_percent: number; connected_clients: number };
    mysql: { connected: boolean; threads_connected: number; table_count: number; total_rows: number };
    chromadb: { connected: boolean; document_count: number; collections: string[] };
}

// SWR Fetcher
const fetcher = async <T>(url: string): Promise<T> => {
    const response = await apiClient.get(url);
    return response.data;
};

// =============================================
// HOOKS
// =============================================

/**
 * Main dashboard overview - aggregates all key metrics
 */
export function useAdminDashboard() {
    const { data, error, isLoading, mutate } = useSWR<DashboardOverview>(
        '/admin/dashboard/overview',
        fetcher,
        { refreshInterval: 30000 } // Refresh every 30s
    );

    return {
        data,
        isLoading,
        isError: !!error,
        error,
        refresh: mutate
    };
}

/**
 * Quick stats for header KPIs - lightweight, frequent polling
 */
export function useQuickStats() {
    const { data, error, isLoading } = useSWR(
        '/admin/dashboard/quick-stats',
        fetcher,
        { refreshInterval: 10000 } // Refresh every 10s
    );

    return { data, isLoading, isError: !!error };
}

/**
 * Active system alerts
 */
export function useAlerts() {
    const { data, error, isLoading, mutate } = useSWR<DashboardAlerts>(
        '/admin/dashboard/alerts',
        fetcher,
        { refreshInterval: 15000 }
    );

    return {
        alerts: data?.alerts || [],
        alertCount: data?.alert_count || 0,
        isLoading,
        isError: !!error,
        refresh: mutate
    };
}

/**
 * Kill switch status and controls
 */
export function useKillSwitches() {
    const { data, error, isLoading, mutate } = useSWR<KillSwitchStatus>(
        '/admin/killswitch/status',
        fetcher,
        { refreshInterval: 5000 } // Fast refresh for critical controls
    );

    const activateSwitch = async (switchType: string, confirmation: string, reason: string) => {
        const response = await apiClient.post('/admin/killswitch/activate', {
            switch_type: switchType,
            confirmation,
            reason
        });
        mutate(); // Refresh state
        return response.data;
    };

    const deactivateSwitch = async (switchType: string, reason?: string) => {
        const response = await apiClient.post('/admin/killswitch/deactivate', {
            switch_type: switchType,
            reason: reason || ''
        });
        mutate();
        return response.data;
    };

    return {
        switches: data?.switches || {},
        isLoading,
        isError: !!error,
        activateSwitch,
        deactivateSwitch,
        refresh: mutate
    };
}

/**
 * Session control
 */
export function useSessionControl() {
    const { data, error, isLoading, mutate } = useSWR<SessionStatus>(
        '/admin/session/status',
        fetcher,
        { refreshInterval: 30000 }
    );

    const forceLogoutAll = async (confirmation: string, reason: string) => {
        const response = await apiClient.post('/admin/session/force-logout-all', {
            confirmation,
            reason
        });
        mutate();
        return response.data;
    };

    const syncEpoch = async () => {
        const response = await apiClient.post('/admin/session/sync-epoch');
        mutate();
        return response.data;
    };

    return {
        status: data,
        isLoading,
        isError: !!error,
        forceLogoutAll,
        syncEpoch,
        refresh: mutate
    };
}

/**
 * AI metrics - summary and hourly
 */
export function useAIMetrics() {
    const summaryResponse = useSWR<AISummary>(
        '/admin/ai/summary',
        fetcher,
        { refreshInterval: 60000 }
    );

    const hourlyResponse = useSWR<AIHourly>(
        '/admin/ai/hourly?hours=24',
        fetcher,
        { refreshInterval: 60000 }
    );

    return {
        summary: summaryResponse.data,
        hourly: hourlyResponse.data,
        isLoading: summaryResponse.isLoading || hourlyResponse.isLoading,
        isError: !!summaryResponse.error || !!hourlyResponse.error,
        refresh: () => {
            summaryResponse.mutate();
            hourlyResponse.mutate();
        }
    };
}

/**
 * Infrastructure metrics
 */
export function useInfrastructure() {
    const { data, error, isLoading, mutate } = useSWR<InfrastructureMetrics>(
        '/admin/metrics/infrastructure',
        fetcher,
        { refreshInterval: 30000 }
    );

    return {
        metrics: data,
        isLoading,
        isError: !!error,
        refresh: mutate
    };
}

/**
 * Request metrics overview
 */
export function useRequestMetrics() {
    const { data, error, isLoading, mutate } = useSWR(
        '/admin/metrics/overview',
        fetcher,
        { refreshInterval: 30000 }
    );

    return {
        metrics: data,
        isLoading,
        isError: !!error,
        refresh: mutate
    };
}

export type {
    DashboardOverview,
    DashboardAlerts,
    KillSwitch,
    AISummary,
    AIHourly,
    SessionStatus,
    InfrastructureMetrics
};
