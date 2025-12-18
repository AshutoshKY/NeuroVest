/**
 * Type definitions for the application
 */

export interface User {
    id: number;
    email: string;
    full_name: string;
    display_name?: string;
    role: 'user' | 'admin';
    is_verified: boolean;
    is_active: boolean;
    created_at: string;
}

export interface StockAnalysis {
    ticker: string;
    company_name: string;
    current_price: number;
    day_high: number;
    day_low: number;
    change_percent: number;
    sentiment_score: number;
    confidence_score: number;
    analysis: string;
    insights: string[];
    trends: string[];
    prediction: {
        direction: 'up' | 'down' | 'neutral';
        timeframe: string;
        confidence: number;
    };
    risks: string[];
    references: Array<{
        title: string;
        url: string;
        source: string;
    }>;
    technical_indicators: {
        rsi?: number;
        macd?: { value: number; signal: number };
        moving_averages?: { ma20: number; ma50: number; ma200: number };
    };
    created_at: string;
}

export interface GuestLimit {
    allowed: boolean;
    remaining: number;
    reset_at: string | null;
    fingerprint: string;
    current_count: number;
}

export interface AdminTrafficData {
    current_users: number;
    last_hour: {
        total_requests: number;
        unique_ips: number;
        analyses: number;
    };
    last_24h: {
        total_requests: number;
        unique_ips: number;
        analyses: number;
        signups: number;
    };
}

export interface AdminSecurityData {
    failed_logins: number;
    locked_accounts: number;
    suspicious_ips: string[];
    rate_limit_hits: number;
}

export interface SystemHealth {
    backend: { status: 'healthy' | 'unhealthy'; latency: number };
    mysql: { status: 'healthy' | 'unhealthy'; connections: number };
    redis: { status: 'healthy' | 'unhealthy'; memory_usage: number };
    chromadb: { status: 'healthy' | 'unhealthy' };
    stock_apis: Array<{
        name: string;
        status: 'healthy' | 'unhealthy' | 'rate_limited';
        latency: number;
    }>;
}
