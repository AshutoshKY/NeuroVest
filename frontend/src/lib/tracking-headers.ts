/**
 * Tracking Headers Builder
 * Builds all tracking headers for API requests
 */

import { TrackingConfig } from './tracking-config';
import { sessionManager } from './session-manager';
import { deviceTokenManager } from './device-token-manager';

export class TrackingHeaders {
    /**
     * Get all tracking headers for API requests.
     * Call this before every API call that needs rate limiting.
     * 
     * Returns headers object ready to spread into fetch headers.
     */
    static async getHeaders(): Promise<HeadersInit> {
        const headers: HeadersInit = {};

        // 1. Session ID (temporary, per-tab)
        if (TrackingConfig.ENABLE_SESSION_TRACKING) {
            const sessionId = sessionManager.getSessionId();
            headers[TrackingConfig.SESSION_ID_HEADER] = sessionId;

            if (TrackingConfig.ENABLE_DEBUG_LOGGING) {
                console.log('[TRACKING] Session ID:', sessionId.substring(0, 16) + '...');
            }
        }

        // 2. Device Token (persistent, server-validated)
        if (TrackingConfig.ENABLE_DEVICE_TRACKING) {
            try {
                const deviceToken = await deviceTokenManager.getDeviceToken();

                if (deviceToken) {
                    // Send as JSON string
                    headers[TrackingConfig.DEVICE_TOKEN_HEADER] = JSON.stringify(deviceToken);

                    if (TrackingConfig.ENABLE_DEBUG_LOGGING) {
                        console.log('[TRACKING] Device token:', deviceToken.device_fp.substring(0, 16) + '...');
                    }
                } else {
                    console.warn('[TRACKING] No device token available');
                }
            } catch (error) {
                console.error('[TRACKING] Failed to get device token:', error);
            }
        }

        return headers;
    }
}
