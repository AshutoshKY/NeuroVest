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
        hourly_history?: Array<{
            hour: string;
            requests: number;
            errors: number;
            avg_latency_ms: number;
            error_rate_percent: number;
        }>;
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
        guest_sessions: number;
        rate_limited_count: number;
        events_today?: {
            rate_limit: number;
            blocked_ip: number;
            auth_failure: number;
            invalid_token: number;
            other: number;
        };
    };
    accessed_by?: {
        admin_id: number;
        admin_email: string;
        role: string;
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

// ==================== SRE UNIFIED OVERVIEW TYPES ====================

interface GoldenSignal {
    current: number;
    sla: number | null;
    delta_percent: number;
    status: 'normal' | 'warning' | 'critical';
}

export interface SREUnifiedOverview {
    system_state: {
        health: 'healthy' | 'degraded' | 'critical';
        score: number;
        primary_reason: string | null;
        active_incidents: number;
        last_checked: string;
    };
    user_impact: {
        failed_requests_percent: number;
        slow_requests_percent: number;
        active_users_affected: number;
        status: 'none' | 'partial' | 'major' | 'unknown';
        window_minutes: number;
    };
    change_detection: {
        traffic_delta_percent: number;
        error_delta_percent: number;
        latency_delta_percent: number;
        window_minutes: number;
    };
    golden_signals: {
        rps: GoldenSignal;
        error_rate: GoldenSignal;
        p95_latency_ms: GoldenSignal;
        saturation_percent: GoldenSignal;
    };
    service_matrix: Array<{
        name: string;
        health_state: 'healthy' | 'degraded' | 'critical';
        health_score: number;
        error_rate_percent: number;
        p95_latency_ms: number;
        saturation_percent: number;
        uptime_percent: number;
        trend: 'up' | 'down' | 'stable';
        interpretation?: string;
    }>;
    ai_rag_health: {
        success_percent: number;
        empty_context_percent: number;
        p95_retrieval_ms: number;
        tokens_per_request: number;
        cost_per_request_usd: number;
        total_requests_today: number;
        sla_threshold_ms: number;
    };
    alerts: Array<{
        severity: 'critical' | 'warning' | 'info';
        service: string;
        message: string;
        time: string;
        link: string;
    }>;
    recent_events: Array<{
        type: string;
        message: string;
        time: string;
        success?: boolean;
    }>;
    timestamp: string;
    error?: string;
}

interface InfrastructureMetrics {
    redis: {
        connected: boolean;
        version?: string;
        memory_used_mb: number;
        memory_peak_mb?: number;
        memory_rss_mb?: number;
        memory_max_mb?: number;
        hit_rate_percent: number;
        connected_clients: number;
        blocked_clients?: number;
        commands_per_sec?: number;
        total_commands?: number;
        total_connections?: number;
        keyspace_hits?: number;
        keyspace_misses?: number;
        total_keys?: number;
        expired_keys?: number;
        evicted_keys?: number;
        uptime_seconds?: number;
        uptime_days?: number;
        uptime_percent?: number;
        cpu_sys?: number;
        cpu_user?: number;
        latency_ms?: number;
    };
    mysql: {
        connected: boolean;
        threads_connected: number;
        max_connections?: number;
        total_queries?: number;
        slow_queries?: number;
        total_connections?: number;
        uptime_seconds?: number;
        uptime_percent?: number;
        table_count: number;
        total_rows: number;
        total_size_mb?: number;
        tables?: Array<{ name: string; rows: number; size_mb: number }>;
        open_tables?: number;
        bytes_received_mb?: number;
        bytes_sent_mb?: number;
        select_queries?: number;
        insert_queries?: number;
        update_queries?: number;
        delete_queries?: number;
        buffer_pool_size_mb?: number;
        latency_ms?: number;
        cpu_percent?: number;
        ram_mb?: number;
    };
    chromadb: {
        connected: boolean;
        document_count: number;
        total_vectors?: number;
        collections: Array<{ name: string; vectors: number; dimensions?: number; size_mb: number }> | string[];
        collection_count?: number;
        total_size_mb?: number;
        embedding_dimensions?: number;
        avg_query_latency_ms?: number;
        queries_today?: number;
        uptime_percent?: number;
        memory_mb?: number;
        cpu_percent?: number;
    };
    backend?: {
        cpu_percent: number;
        memory_mb: number;
        uptime_percent: number;
    };
    system?: {
        total_memory_mb: number;
        available_memory_mb: number;
        memory_percent: number;
        cpu_percent: number;
        cpu_count: number;
    };
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
 * SRE Unified Overview - Powers the main Overview page
 * Single endpoint with all critical data for incident response
 */
export function useSREUnifiedOverview() {
    const { data, error, isLoading, mutate } = useSWR<SREUnifiedOverview>(
        '/admin/dashboard/sre-unified-overview',
        fetcher,
        { refreshInterval: 0 } // Manual refresh only
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
 * Main dashboard overview - aggregates all key metrics
 */
export function useAdminDashboard() {
    const { data, error, isLoading, mutate } = useSWR<DashboardOverview>(
        '/admin/dashboard/overview',
        fetcher,
        { refreshInterval: 0 } // Manual refresh only
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
        { refreshInterval: 0 } // Manual refresh only
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
        { refreshInterval: 0 } // Manual refresh only
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
 * Audit log entries for Security page System Events Log
 */
export function useAuditLog(limit: number = 50) {
    const { data, error, isLoading, mutate } = useSWR<{
        entries: Array<{
            id: number;
            actor_email: string;
            actor_role: string;
            action: string;
            action_category: string;
            target_type: string | null;
            target_id: string | null;
            changes: Record<string, unknown> | null;
            ip_address: string | null;
            success: boolean;
            error_message: string | null;
            created_at: string;
        }>;
        total: number;
    }>(`/admin/dashboard/audit-log?limit=${limit}`, fetcher);

    return {
        entries: data?.entries || [],
        total: data?.total || 0,
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
        { refreshInterval: 0 } // Manual refresh only
    );

    const activateSwitch = async (switchType: string, confirmation: string, reason: string, pin: string) => {
        const response = await apiClient.post('/admin/killswitch/activate', {
            switch_type: switchType,
            confirmation,
            reason,
            pin
        });
        mutate(); // Refresh state
        return response.data;
    };

    const deactivateSwitch = async (switchType: string, reason?: string, pin?: string) => {
        const response = await apiClient.post('/admin/killswitch/deactivate', {
            switch_type: switchType,
            reason: reason || '',
            pin: pin || ''
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
        { refreshInterval: 0 } // Manual refresh only
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
        { refreshInterval: 0 } // Manual refresh only
    );

    const hourlyResponse = useSWR<AIHourly>(
        '/admin/ai/hourly?hours=24',
        fetcher,
        { refreshInterval: 0 } // Manual refresh only
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
        { refreshInterval: 0 } // Manual refresh only
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
        { refreshInterval: 0 } // Manual refresh only
    );

    return {
        metrics: data,
        isLoading,
        isError: !!error,
        refresh: mutate
    };
}

/**
 * Blocked IPs management
 */
interface BlockedIP {
    ip_address: string;
    reason: string;
    blocked_at: string;
    blocked_by: number | null;
    is_active: boolean;
}

export function useBlockedIPs() {
    const { data, error, isLoading, mutate } = useSWR<{ blocked_ips: BlockedIP[] }>(
        '/admin/ip-blacklist',
        fetcher,
        { refreshInterval: 0 } // Manual refresh only
    );

    const unblockIP = async (ip: string): Promise<void> => {
        await apiClient.delete(`/admin/ip-blacklist/${encodeURIComponent(ip)}`);
        mutate();
    };

    const blockIP = async (ip: string, reason: string): Promise<void> => {
        await apiClient.post('/admin/ip-blacklist/add', { ip_address: ip, reason });
        mutate();
    };

    return {
        blockedIPs: data?.blocked_ips || [],
        isLoading,
        isError: !!error,
        unblockIP,
        blockIP,
        refresh: mutate
    };
}

// =============================================
// SRE DASHBOARD HOOKS
// =============================================

/**
 * SRE Overview - Global system health
 */
interface SREOverview {
    global_health: 'healthy' | 'degraded' | 'critical';
    global_score: number;
    user_impact: {
        affected_users: number | string;
        status: 'none' | 'partial' | 'major';
    };
    active_incidents: number;
    global_error_rate: number;
    p95_latency_ms: number;
    rps: {
        current: number;
        previous: number;
        delta_percent: number;
    };
    timestamp: string;
}

export function useSREOverview() {
    const { data, error, isLoading, mutate } = useSWR<SREOverview>(
        '/admin/dashboard/sre-overview',
        fetcher,
        { refreshInterval: 30000 } // Auto-refresh every 30s
    );

    return {
        data,
        isLoading,
        isError: !!error,
        refresh: mutate
    };
}

/**
 * Service Matrix - All services health
 */
interface ServiceHealthItem {
    name: string;
    health_state: 'healthy' | 'degraded' | 'critical';
    health_score: number;
    error_rate_percent: number;
    p95_latency_ms: number;
    saturation_percent: number;
    uptime_percent: number;
    trend: 'up' | 'down' | 'stable';
    interpretation?: string;
}

interface ServiceMatrix {
    services: ServiceHealthItem[];
    timestamp: string;
}

export function useServiceMatrix() {
    const { data, error, isLoading, mutate } = useSWR<ServiceMatrix>(
        '/admin/dashboard/service-matrix',
        fetcher,
        { refreshInterval: 30000 }
    );

    return {
        services: data?.services || [],
        isLoading,
        isError: !!error,
        refresh: mutate
    };
}

/**
 * Service Deep Dive - Detailed per-service metrics
 */
interface ServiceDeepDive {
    service: string;
    health_state: 'healthy' | 'degraded' | 'critical';
    health_score: number;
    score_breakdown?: {
        availability: number;
        error: number;
        latency: number;
        saturation: number;
    };
    metrics: {
        uptime_percent: number;
        error_rate_percent: number;
        p95_latency_ms: number;
        saturation_percent: number;
    };
    raw_metrics: Record<string, unknown>;
    interpretation?: string;
    trend: 'up' | 'down' | 'stable';
    timestamp: string;
}

export function useServiceDeepDive(serviceName: string) {
    const { data, error, isLoading, mutate } = useSWR<ServiceDeepDive>(
        serviceName ? `/admin/dashboard/service/${serviceName}/deep-dive` : null,
        fetcher,
        { refreshInterval: 0 } // Manual refresh
    );

    return {
        data,
        isLoading,
        isError: !!error,
        refresh: mutate
    };
}

/**
 * RAG Observability - AI/RAG metrics
 */
interface RAGObservability {
    retrieval_success_percent: number;
    empty_context_rate: number;
    avg_docs_per_query: number;
    latency_breakdown: {
        embedding_ms: number;
        retrieval_ms: number;
        llm_ms: number;
        total_ms: number;
        p95_ms: number;
    };
    sla_violation_percent: number;
    total_queries: number;
    period_hours: number;
    sla_threshold_ms: number;
    timestamp: string;
}

export function useRAGObservability(hours: number = 24) {
    const { data, error, isLoading, mutate } = useSWR<RAGObservability>(
        `/admin/dashboard/rag-observability?hours=${hours}`,
        fetcher,
        { refreshInterval: 60000 } // Refresh every minute
    );

    return {
        data: data || {
            retrieval_success_percent: 100,
            empty_context_rate: 0,
            avg_docs_per_query: 0,
            latency_breakdown: { embedding_ms: 0, retrieval_ms: 0, llm_ms: 0, total_ms: 0, p95_ms: 0 },
            sla_violation_percent: 0,
            total_queries: 0,
            period_hours: hours,
            sla_threshold_ms: 500,
            timestamp: new Date().toISOString()
        },
        isLoading,
        isError: !!error,
        refresh: mutate
    };
}

/**
 * User Impact - How infra issues affect users
 */
interface UserImpact {
    failed_requests_percent: number;
    slow_requests_percent: number;
    total_requests_5m: number;
    top_impacted_endpoints: Array<{
        endpoint: string;
        avg_latency_ms: number;
        calls: number;
        status: string;
    }>;
    degraded_services: string[];
    has_user_impact: boolean;
    timestamp: string;
}

export function useUserImpact() {
    const { data, error, isLoading, mutate } = useSWR<UserImpact>(
        '/admin/dashboard/user-impact',
        fetcher,
        { refreshInterval: 30000 }
    );

    return {
        data: data || {
            failed_requests_percent: 0,
            slow_requests_percent: 0,
            total_requests_5m: 0,
            top_impacted_endpoints: [],
            degraded_services: [],
            has_user_impact: false,
            timestamp: new Date().toISOString()
        },
        isLoading,
        isError: !!error,
        refresh: mutate
    };
}

/**
 * Historical Metrics - Real data for charts
 */
interface TrafficDataPoint {
    hour: string;
    requests: number;
    errors: number;
}

interface LatencyDataPoint {
    hour: string;
    avg_latency_ms: number;
}

interface ErrorDataPoint {
    hour: string;
    error_rate_percent: number;
    errors: number;
}

interface HistoricalMetrics {
    traffic: TrafficDataPoint[];
    latency: LatencyDataPoint[];
    errors: ErrorDataPoint[];
    period_hours: number;
    data_points: number;
    timestamp: string;
}

export function useHistoricalMetrics(hours: number = 8) {
    const { data, error, isLoading, mutate } = useSWR<HistoricalMetrics>(
        `/admin/dashboard/historical-metrics?hours=${hours}`,
        fetcher,
        { refreshInterval: 60000 } // Refresh every minute
    );

    return {
        data: data || {
            traffic: [],
            latency: [],
            errors: [],
            period_hours: hours,
            data_points: 0,
            timestamp: new Date().toISOString()
        },
        isLoading,
        isError: !!error,
        refresh: mutate
    };
}

// ==================== CONTAINER METRICS HOOKS ====================

interface ContainerStats {
    name: string;
    display_name: string;
    status: string;
    running: boolean;
    cpu_percent: number;
    memory: {
        used_mb: number;
        limit_mb: number;
        percent: number;
    };
    network: {
        rx_mb: number;
        tx_mb: number;
    };
    error?: string;
}

interface ContainerMetrics {
    containers: ContainerStats[];
    summary: {
        total_containers: number;
        running_containers: number;
        total_cpu_percent: number;
        total_memory_mb: number;
    };
    timestamp: string;
    error?: string;
}

/**
 * Container Metrics - Docker container resource usage (CPU, Memory, Network)
 */
export function useContainerMetrics() {
    const { data, error, isLoading, mutate } = useSWR<ContainerMetrics>(
        '/admin/metrics/infrastructure/containers',
        fetcher,
        { refreshInterval: 10000 } // Refresh every 10 seconds for real-time monitoring
    );

    return {
        containers: data?.containers || [],
        summary: data?.summary || {
            total_containers: 4,
            running_containers: 0,
            total_cpu_percent: 0,
            total_memory_mb: 0
        },
        isLoading,
        isError: !!error,
        error: data?.error,
        refresh: mutate
    };
}


// ==================== USER MANAGEMENT HOOKS ====================

interface UserSearchResult {
    id: number;
    email: string;
    full_name: string;
    is_active: boolean;
    is_admin: boolean;
    created_at: string | null;
    last_login: string | null;
    total_logins: number;
    active_sessions: number;
    has_active_session: boolean;
    analysis_count: number;
}

interface UserSearchResponse {
    users: UserSearchResult[];
    total_users: number;
    page: number;
    limit: number;
    total_pages: number;
    timestamp: string;
}

interface UserDetails {
    user: {
        id: number;
        email: string;
        full_name: string;
        is_active: boolean;
        is_admin: boolean;
        created_at: string | null;
    };
    stats: {
        total_logins: number;
        total_analyses: number;
        unique_ips_count: number;
        unique_devices_count: number;
        active_sessions_count: number;
    };
    unique_ips: string[];
    unique_devices: string[];
    login_history: Array<{
        id: number;
        login_time: string | null;
        logout_time: string | null;
        ip_address: string | null;
        device_name: string | null;
        device_type: string | null;
        browser: string | null;
        os: string | null;
        location: string | null;
        success: boolean;
    }>;
    active_sessions: Array<{
        id: number;
        device: string;
        created_at: string | null;
        expires_at: string | null;
    }>;
    analysis_history: Array<{
        id: number;
        symbol: string;
        analysis_type: string;
        created_at: string | null;
    }>;
    activity_trend: Array<{
        date: string;
        logins: number;
    }>;
    timestamp: string;
}

export function useUserSearch(query: string = '', page: number = 1, limit: number = 20) {
    const { data, error, isLoading, mutate } = useSWR<UserSearchResponse>(
        `/admin/dashboard/users/search?query=${encodeURIComponent(query)}&page=${page}&limit=${limit}`,
        fetcher,
        { refreshInterval: 0 }  // Manual refresh only
    );

    return {
        users: data?.users || [],
        totalUsers: data?.total_users || 0,
        currentPage: data?.page || 1,
        totalPages: data?.total_pages || 0,
        isLoading,
        isError: !!error,
        refresh: mutate
    };
}

export function useUserDetails(userId: number | null) {
    const { data, error, isLoading, mutate } = useSWR<UserDetails>(
        userId ? `/admin/dashboard/users/${userId}/details` : null,
        fetcher,
        { refreshInterval: 0 }
    );

    return {
        data,
        isLoading,
        isError: !!error,
        refresh: mutate
    };
}

export async function forceLogoutUser(userId: number): Promise<{ success: boolean; message?: string; error?: string }> {
    try {
        const response = await apiClient.post(`/admin/dashboard/users/${userId}/force-logout`);
        return response.data;
    } catch (error: unknown) {
        const message = error instanceof Error ? error.message : 'Failed to logout user';
        return { success: false, error: message };
    }
}

export async function deleteUser(userId: number): Promise<{ success: boolean; message?: string; error?: string }> {
    try {
        const response = await apiClient.delete(`/admin/dashboard/users/${userId}`);
        return response.data;
    } catch (error: unknown) {
        const message = error instanceof Error ? error.message : 'Failed to delete user';
        return { success: false, error: message };
    }
}

export type {
    DashboardOverview,
    DashboardAlerts,
    KillSwitch,
    AISummary,
    AIHourly,
    SessionStatus,
    InfrastructureMetrics,
    BlockedIP,
    // SRE types
    SREOverview,
    ServiceHealthItem,
    ServiceMatrix,
    ServiceDeepDive,
    RAGObservability,
    UserImpact,
    HistoricalMetrics,
    TrafficDataPoint,
    LatencyDataPoint,
    ErrorDataPoint,
    // Container metrics types
    ContainerStats,
    ContainerMetrics,
    // User management types
    UserSearchResult,
    UserSearchResponse,
    UserDetails
};
