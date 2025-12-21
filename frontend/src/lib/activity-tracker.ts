/**
 * Activity Tracker for JWT Token Refresh
 * 
 * Monitors user activity and triggers token refresh when user is active.
 * Runs check every 5 minutes. If user active in last 5 min, refreshes token.
 */

import apiClient from './api';

class ActivityTracker {
    private lastActivityTime: number = Date.now();
    private refreshCheckInterval: NodeJS.Timeout | null = null;
    private readonly CHECK_INTERVAL_MS = 5 * 60 * 1000; // 5 minutes
    private readonly ACTIVITY_WINDOW_MS = 5 * 60 * 1000; // 5 minutes

    constructor() {
        if (typeof window !== 'undefined') {
            this.startMonitoring();
            this.setupActivityListeners();
        }
    }

    /**
     * Record user activity (called on interactions)
     */
    recordActivity = (): void => {
        this.lastActivityTime = Date.now();
    };

    /**
     * Setup event listeners for user activity
     */
    private setupActivityListeners(): void {
        // Track mouse movement (throttled)
        let mouseThrottle: NodeJS.Timeout;
        window.addEventListener('mousemove', () => {
            clearTimeout(mouseThrottle);
            mouseThrottle = setTimeout(() => this.recordActivity(), 1000);
        });

        // Track keyboard activity
        window.addEventListener('keydown', () => this.recordActivity());

        // Track clicks
        window.addEventListener('click', () => this.recordActivity());

        // Track scroll (throttled)
        let scrollThrottle: NodeJS.Timeout;
        window.addEventListener('scroll', () => {
            clearTimeout(scrollThrottle);
            scrollThrottle = setTimeout(() => this.recordActivity(), 1000);
        });

        // Track page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                this.recordActivity();
            }
        });
    }

    /**
     * Start monitoring and checking for refresh
     */
    private startMonitoring(): void {
        console.log('[ACTIVITY_TRACKER] Starting monitoring (check every 5 minutes)');

        // Run initial check
        this.checkAndRefresh();

        // Setup periodic checks
        this.refreshCheckInterval = setInterval(() => {
            this.checkAndRefresh();
        }, this.CHECK_INTERVAL_MS);
    }

    /**
     * Check if user is active and refresh token if needed
     */
    private async checkAndRefresh(): Promise<void> {
        const timeSinceActivity = Date.now() - this.lastActivityTime;

        // Check if page is visible
        const isPageVisible = !document.hidden;

        // Only refresh if user is active AND page is visible
        if (timeSinceActivity < this.ACTIVITY_WINDOW_MS && isPageVisible) {
            console.log(`[ACTIVITY_TRACKER] User active (${Math.floor(timeSinceActivity / 1000)}s ago), refreshing token...`);
            await this.refreshToken();
        } else {
            console.log(`[ACTIVITY_TRACKER] User inactive (${Math.floor(timeSinceActivity / 1000)}s ago) or page hidden, skipping refresh`);
        }
    }

    /**
     * Refresh JWT tokens
     */
    private async refreshToken(): Promise<void> {
        try {
            const response = await apiClient.post('/auth/refresh');
            console.log('[ACTIVITY_TRACKER] ✅ Token refreshed successfully');

            // Update last activity time (refresh succeeded)
            this.recordActivity();
        } catch (error: any) {
            console.error('[ACTIVITY_TRACKER] ❌ Token refresh failed:', error);

            // If refresh fails with 401, user needs to re-login
            if (error.response?.status === 401) {
                console.warn('[ACTIVITY_TRACKER] Refresh token expired, redirecting to login...');
                this.stopMonitoring();

                // Only redirect if not already on login page
                if (!window.location.pathname.includes('/auth/login')) {
                    window.location.href = '/auth/login';
                }
            }
        }
    }

    /**
     * Stop monitoring (e.g., on logout)
     */
    stopMonitoring(): void {
        if (this.refreshCheckInterval) {
            clearInterval(this.refreshCheckInterval);
            this.refreshCheckInterval = null;
            console.log('[ACTIVITY_TRACKER] Monitoring stopped');
        }
    }

    /**
     * Get time since last activity (for debugging)
     */
    getTimeSinceActivity(): number {
        return Date.now() - this.lastActivityTime;
    }

    /**
     * Force an immediate refresh (for testing)
     */
    async forceRefresh(): Promise<void> {
        console.log('[ACTIVITY_TRACKER] Forcing token refresh...');
        await this.refreshToken();
    }
}

// Singleton instance
let activityTrackerInstance: ActivityTracker | null = null;

export function getActivityTracker(): ActivityTracker {
    if (!activityTrackerInstance && typeof window !== 'undefined') {
        activityTrackerInstance = new ActivityTracker();

        // Expose to window for debugging
        (window as any).activityTracker = activityTrackerInstance;
    }
    return activityTrackerInstance!;
}

export default ActivityTracker;
