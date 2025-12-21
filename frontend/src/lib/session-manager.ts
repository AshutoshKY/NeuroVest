/**
 * Session Manager
 * Manages browser session tracking using sessionStorage
 * Includes 24-hour session rotation (silent background process)
 */

import { TrackingConfig } from './tracking-config';

export class SessionManager {
    private static instance: SessionManager;
    private readonly ROTATION_INTERVAL_MS = 24 * 60 * 60 * 1000; // 24 hours
    private readonly SESSION_CREATED_KEY = 'session_created_at';

    private constructor() {
        if (TrackingConfig.ENABLE_DEBUG_LOGGING) {
            console.log('[SESSION] SessionManager initialized');
        }
    }

    static getInstance(): SessionManager {
        if (!SessionManager.instance) {
            SessionManager.instance = new SessionManager();
        }
        return SessionManager.instance;
    }

    /**
     * Get session ID - creates new one if doesn't exist.
     * Automatically rotates session after 24 hours (silent).
     * Stored in sessionStorage (clears when tab closes).
     */
    getSessionId(): string {
        if (typeof window === 'undefined') {
            return 'ssr-session';
        }

        // Check if rotation needed before returning session ID
        this.rotateIfNeeded();

        let sessionId = sessionStorage.getItem(TrackingConfig.SESSION_ID_KEY);

        if (!sessionId) {
            // Generate new UUID for this session
            sessionId = crypto.randomUUID();
            sessionStorage.setItem(TrackingConfig.SESSION_ID_KEY, sessionId);
            sessionStorage.setItem(this.SESSION_CREATED_KEY, Date.now().toString());

            if (TrackingConfig.ENABLE_DEBUG_LOGGING) {
                console.log('[SESSION] Created new session:', sessionId.substring(0, 16) + '...');
            }
        }

        return sessionId;
    }

    /**
     * Rotate session ID after 24 hours (silent background process).
     * User stays logged in (JWT unchanged), only session ID refreshes.
     */
    private rotateIfNeeded(): void {
        if (typeof window === 'undefined') {
            return;
        }

        const createdAtStr = sessionStorage.getItem(this.SESSION_CREATED_KEY);

        if (!createdAtStr) {
            // No creation time stored - set it now for existing sessions
            sessionStorage.setItem(this.SESSION_CREATED_KEY, Date.now().toString());
            return;
        }

        const createdAt = parseInt(createdAtStr, 10);
        const age = Date.now() - createdAt;

        if (age > this.ROTATION_INTERVAL_MS) {
            const oldSessionId = sessionStorage.getItem(TrackingConfig.SESSION_ID_KEY);

            // Generate new session ID
            const newSessionId = crypto.randomUUID();
            sessionStorage.setItem(TrackingConfig.SESSION_ID_KEY, newSessionId);
            sessionStorage.setItem(this.SESSION_CREATED_KEY, Date.now().toString());

            // Log rotation event
            console.log(
                `[SESSION] ✅ Session rotated after 24h (silent background process)\n` +
                `  Reason: Session age exceeded rotation interval\n` +
                `  Old: ${oldSessionId?.substring(0, 16)}...\n` +
                `  New: ${newSessionId.substring(0, 16)}...\n` +
                `  User: Remains logged in (JWT unchanged)`
            );
        }
    }

    /**
     * Clear session (logout, session timeout)
     */
    clearSession(): void {
        if (typeof window !== 'undefined') {
            sessionStorage.removeItem(TrackingConfig.SESSION_ID_KEY);
            sessionStorage.removeItem(this.SESSION_CREATED_KEY);

            if (TrackingConfig.ENABLE_DEBUG_LOGGING) {
                console.log('[SESSION] Session cleared');
            }
        }
    }

    /**
     * Check if session is active
     */
    hasActiveSession(): boolean {
        if (typeof window === 'undefined') {
            return false;
        }
        return sessionStorage.getItem(TrackingConfig.SESSION_ID_KEY) !== null;
    }

    /**
     * Get session age in milliseconds
     */
    getSessionAge(): number {
        if (typeof window === 'undefined') {
            return 0;
        }

        const createdAtStr = sessionStorage.getItem(this.SESSION_CREATED_KEY);
        if (!createdAtStr) {
            return 0;
        }

        return Date.now() - parseInt(createdAtStr, 10);
    }
}

// Singleton export
export const sessionManager = SessionManager.getInstance();
