/**
 * Device Token Manager
 * Manages device registration and token lifecycle with backend validation
 */

import { TrackingConfig } from './tracking-config';
import { deviceFingerprintService } from './fingerprint';

interface DeviceToken {
    device_fp: string;
    signature: string;
    issued_at: string;
    issued_ip: string;
    version: string;
}

interface RegistrationResponse {
    device_token: DeviceToken;
    requires_captcha: boolean;
    warning_message?: string;
}

export class DeviceTokenManager {
    private static instance: DeviceTokenManager;
    private apiBaseUrl: string;

    private constructor() {
        this.apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

        if (TrackingConfig.ENABLE_DEBUG_LOGGING) {
            console.log('[DEVICE_TOKEN] Manager initialized, API:', this.apiBaseUrl);
        }
    }

    static getInstance(): DeviceTokenManager {
        if (!DeviceTokenManager.instance) {
            DeviceTokenManager.instance = new DeviceTokenManager();
        }
        return DeviceTokenManager.instance;
    }

    /**
     * Get device token - registers if doesn't exist or invalid
     */
    async getDeviceToken(): Promise<DeviceToken | null> {
        if (typeof window === 'undefined') {
            return null;
        }

        // Try to get from localStorage
        const stored = localStorage.getItem(TrackingConfig.DEVICE_TOKEN_KEY);

        if (stored) {
            try {
                const token: DeviceToken = JSON.parse(stored);

                // Validate token with backend (if needed)
                const isValid = await this.validateToken(token);

                if (isValid) {
                    return token;
                }

                if (TrackingConfig.ENABLE_DEBUG_LOGGING) {
                    console.log('[DEVICE_TOKEN] Stored token invalid, re-registering...');
                }
            } catch (error) {
                console.error('[DEVICE_TOKEN] Failed to parse stored token:', error);
            }
        }

        // Register new device
        return await this.registerDevice();
    }

    /**
     * Register device and get signed token from backend
     */
    private async registerDevice(captchaToken?: string): Promise<DeviceToken | null> {
        try {
            // Get device fingerprint
            const deviceFingerprint = await deviceFingerprintService.getFingerprint();

            console.log('[DEVICE_TOKEN] 🚀 Starting registration...');
            console.log('[DEVICE_TOKEN] Fingerprint:', deviceFingerprint.substring(0, 16) + '...');
            console.log('[DEVICE_TOKEN] API URL:', `${this.apiBaseUrl}${TrackingConfig.DEVICE_REGISTER_ENDPOINT}`);

            // Call backend to register
            const response = await fetch(`${this.apiBaseUrl}${TrackingConfig.DEVICE_REGISTER_ENDPOINT}`, {
                method: 'POST',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    device_fingerprint: deviceFingerprint,
                    captcha_token: captchaToken
                })
            });

            console.log('[DEVICE_TOKEN] ✅ Response status:', response.status);

            if (!response.ok) {
                const errorText = await response.text();
                console.error('[DEVICE_TOKEN] ❌ Registration failed:', response.status, errorText);

                if (response.status === 428) {
                    console.warn('[DEVICE_TOKEN] CAPTCHA required');
                    throw new Error('CAPTCHA verification required');
                }
                throw new Error(`Registration failed: ${response.statusText}`);
            }

            const data: RegistrationResponse = await response.json();

            console.log('[DEVICE_TOKEN] ✅ Token received:');
            console.log('  - device_fp:', data.device_token.device_fp.substring(0, 16) + '...');
            console.log('  - signature:', data.device_token.signature.substring(0, 16) + '...');
            console.log('  - issued_at:', data.device_token.issued_at);
            console.log('  - issued_ip:', data.device_token.issued_ip);
            console.log('  - version:', data.device_token.version);

            // Verify structure before storing
            if (!data.device_token.issued_at || !data.device_token.issued_ip) {
                console.error('[DEVICE_TOKEN] ❌ Invalid token structure from backend!');
                console.error('[DEVICE_TOKEN] Token:', data.device_token);
                throw new Error('Invalid token structure');
            }

            // Store token
            localStorage.setItem(TrackingConfig.DEVICE_TOKEN_KEY, JSON.stringify(data.device_token));
            console.log('[DEVICE_TOKEN] ✅ Token stored to localStorage');

            if (data.warning_message) {
                console.warn('[DEVICE_TOKEN] ⚠️', data.warning_message);
            }

            return data.device_token;

        } catch (error) {
            console.error('[DEVICE_TOKEN] ❌ Registration error:', error);
            throw error; // Don't return null - let it throw
        }
    }

    /**
     * Validate token with backend
     */
    private async validateToken(token: DeviceToken): Promise<boolean> {
        try {
            const response = await fetch(`${this.apiBaseUrl}${TrackingConfig.DEVICE_VALIDATE_ENDPOINT}`, {
                method: 'POST',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(token)
            });

            if (!response.ok) {
                return false;
            }

            const data = await response.json();

            if (!data.valid) {
                if (TrackingConfig.ENABLE_DEBUG_LOGGING) {
                    console.log('[DEVICE_TOKEN] Validation failed:', data.error, 'action:', data.action);
                }

                // Handle different actions
                if (data.action === 'show-warning-and-captcha') {
                    // TODO: Show warning + CAPTCHA dialog
                    console.warn('[DEVICE_TOKEN] IP changed - CAPTCHA required');
                }

                return false;
            }

            return true;

        } catch (error) {
            console.error('[DEVICE_TOKEN] Validation error:', error);
            return false;
        }
    }

    /**
     * Clear device token (logout, reset)
     */
    clearToken(): void {
        if (typeof window !== 'undefined') {
            localStorage.removeItem(TrackingConfig.DEVICE_TOKEN_KEY);

            if (TrackingConfig.ENABLE_DEBUG_LOGGING) {
                console.log('[DEVICE_TOKEN] Token cleared');
            }
        }
    }
}

// Singleton export
export const deviceTokenManager = DeviceTokenManager.getInstance();
