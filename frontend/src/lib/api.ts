/**
 * API Client Configuration
 * Handles all backend communication with:
 * - JWT token management (httpOnly cookies)
 * - RSA encryption for sensitive data
 * - Guest tracking integration
 * - Automatic token refresh
 */
import axios, { AxiosInstance, InternalAxiosRequestConfig, AxiosResponse } from 'axios';
import CryptoJS from 'crypto-js';

// Detect if running on server (SSR) vs client
// Server-side needs Docker internal network URL, client-side needs localhost
const isServer = typeof window === 'undefined';
const API_BASE_URL = isServer
    ? (process.env.API_INTERNAL_URL || 'http://backend:8000')  // Docker internal URL for SSR
    : (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000');  // Browser URL

class APIClient {
    private client: AxiosInstance;
    private publicKey: string | null = null;

    constructor() {
        this.client = axios.create({
            baseURL: API_BASE_URL,
            headers: {
                'Content-Type': 'application/json',
            },
            withCredentials: true,
        });

        // Request interceptor
        this.client.interceptors.request.use(
            (config) => this.handleRequest(config),
            (error) => Promise.reject(error)
        );

        // Response interceptor
        this.client.interceptors.response.use(
            (response) => response,
            (error) => this.handleError(error)
        );

        // Fetch public key on initialization
        this.fetchPublicKey();
    }

    /**
   * Fetch RSA public key from backend
   */
    private async fetchPublicKey(): Promise<void> {
        try {
            const response = await axios.get(`${API_BASE_URL}/tracking/encryption/public-key`);
            this.publicKey = response.data.public_key;
            console.log('[API] Public key fetched successfully');
        } catch (error) {
            console.warn('[API] Failed to fetch public key:', error);
            // Don't throw - allow API client to work without encryption
        }
    }

    /**
     * Encrypt sensitive data with RSA public key
     */
    private encryptSensitiveData(data: any): any {
        if (!this.publicKey) {
            console.warn('[API] Public key not available, sending unencrypted');
            return data;
        }

        // Fields to encrypt
        const sensitiveFields = ['email', 'password', 'current_password', 'new_password', 'full_name', 'display_name'];
        const encryptedData = { ...data };

        for (const field of sensitiveFields) {
            if (data[field]) {
                // In production, use actual RSA encryption
                // For now, using AES as placeholder (you'll implement RSA next)
                encryptedData[field] = CryptoJS.AES.encrypt(
                    data[field],
                    this.publicKey
                ).toString();
                encryptedData[`${field}_encrypted`] = true;
            }
        }

        return encryptedData;
    }

    /**
     * Handle outgoing requests
     */
    private async handleRequest(config: InternalAxiosRequestConfig): Promise<InternalAxiosRequestConfig> {
        // CRITICAL: Add full tracking headers to ALL requests
        // Backend requires X-Device-Token (signed) + X-Session-ID + IP
        try {
            const { TrackingHeaders } = await import('./tracking-headers');
            const trackingHeaders = await TrackingHeaders.getHeaders();

            // Merge tracking headers with existing headers
            config.headers = config.headers || {};
            Object.assign(config.headers, trackingHeaders);

            if (process.env.NODE_ENV === 'development') {
                console.log('[API_CLIENT] Request headers:', {
                    url: config.url,
                    hasDeviceToken: !!(trackingHeaders as any)['X-Device-Token'],
                    hasSessionId: !!(trackingHeaders as any)['X-Session-ID']
                });
            }
        } catch (error) {
            console.warn('[API_CLIENT] Failed to get tracking headers:', error);
            // Continue without tracking headers (will fail for protected endpoints)
        }

        // Encrypt sensitive data for auth endpoints with selective exclusions
        // - update-profile: Don't encrypt (causes display issues, already protected by JWT)
        // - change-password: DO encrypt (passwords should be encrypted in transit)
        // - delete-account: Don't encrypt (no sensitive data)
        const unencryptedEndpoints = ['/update-profile', '/delete-account'];
        const isUnencrypted = unencryptedEndpoints.some(endpoint => config.url?.includes(endpoint));

        if (config.url?.includes('/auth/') && config.data && !isUnencrypted) {
            config.data = this.encryptSensitiveData(config.data);
        }

        return config;
    }


    // Guard against infinite refresh loops
    private isRefreshing = false;

    /**
     * Handle errors
     */
    private async handleError(error: any): Promise<any> {
        const url = error.config?.url;

        // Skip refresh logic for:
        // 1. Login/Register endpoints (failed auth should just error)
        // 2. Refresh endpoint itself (prevent loops)
        if (url?.includes('/auth/login') || url?.includes('/auth/register') || url?.includes('/auth/refresh')) {
            return Promise.reject(error);
        }

        // Don't retry if already refreshing 
        if (error.response?.status === 401 && !this.isRefreshing) {
            // Token expired - try to refresh automatically (but only once!)
            try {
                this.isRefreshing = true;
                await this.refreshToken();
                this.isRefreshing = false;
                // Retry original request with new token
                return this.client.request(error.config);
            } catch (refreshError) {
                // Refresh failed - redirect to login
                this.isRefreshing = false;
                console.error('[API] Token refresh failed:', refreshError);
                if (typeof window !== 'undefined' && !window.location.pathname.includes('/auth/')) {
                    window.location.href = '/auth/login';
                }
                return Promise.reject(refreshError);
            }
        }

        return Promise.reject(error);
    }

    /**
     * Refresh JWT access token
     */
    private async refreshToken(): Promise<void> {
        // Check if refresh token exists before attempting
        const hasRefreshToken = typeof document !== 'undefined' &&
            document.cookie.split(';').some(cookie => cookie.trim().startsWith('refresh_token='));

        if (!hasRefreshToken) {
            console.warn('[API] No refresh token available, skipping refresh');
            throw new Error('No refresh token');
        }

        await this.client.post('/auth/refresh');
    }

    // Public methods
    async get<T = any>(url: string, config?: any): Promise<AxiosResponse<T>> {
        return this.client.get<T>(url, config);
    }

    async post<T = any>(url: string, data?: any, config?: any): Promise<AxiosResponse<T>> {
        return this.client.post<T>(url, data, config);
    }

    async put<T = any>(url: string, data?: any, config?: any): Promise<AxiosResponse<T>> {
        return this.client.put<T>(url, data, config);
    }

    async patch<T = any>(url: string, data?: any, config?: any): Promise<AxiosResponse<T>> {
        return this.client.patch<T>(url, data, config);
    }

    async delete<T = any>(url: string, config?: any): Promise<AxiosResponse<T>> {
        return this.client.delete<T>(url, config);
    }

    // Watchlist methods
    async addToWatchlist(ticker: string, name: string, exchange?: string) {
        return this.post('/api/watchlist', { ticker, name, exchange });
    }

    async getWatchlist() {
        return this.get('/api/watchlist');
    }

    async removeFromWatchlist(ticker: string) {
        return this.delete(`/api/watchlist/${ticker}`);
    }

    // Favourites methods
    async addToFavourites(ticker: string, name: string, exchange?: string) {
        return this.post('/api/favourites', { ticker, name, exchange });
    }

    async getFavourites() {
        return this.get('/api/favourites');
    }

    async removeFromFavourites(ticker: string) {
        return this.delete(`/api/favourites/${ticker}`);
    }

    // History methods
    async getAnalysisHistory(limit: number = 50) {
        return this.get(`/api/history?limit=${limit}`);
    }

    async addToHistory(ticker: string, name: string, analysis_data?: any) {
        return this.post('/api/history', { ticker, name, analysis_data });
    }
}

// Singleton instance
export const apiClient = new APIClient();
export default apiClient;
