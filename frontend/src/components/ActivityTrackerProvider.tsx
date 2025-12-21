'use client';

/**
 * Activity Tracker Provider
 * Initializes the activity tracker for automatic token refresh
 */
import { useEffect } from 'react';
import { getActivityTracker } from '@/lib/activity-tracker';
import { useAuthStore } from '@/store/authStore';

export function ActivityTrackerProvider({ children }: { children: React.ReactNode }) {
    const { isAuthenticated } = useAuthStore();

    useEffect(() => {
        // Only start tracker if user is authenticated
        if (isAuthenticated) {
            const tracker = getActivityTracker();
            console.log('[APP] Activity tracker initialized for authenticated user');

            // Cleanup on unmount
            return () => {
                tracker.stopMonitoring();
            };
        }
    }, [isAuthenticated]);

    return <>{children}</>;
}
