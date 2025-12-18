/**
 * Tracking Configuration
 * Centralized config for all tracking dimensions
 */

export const TrackingConfig = {
    // Storage keys (namespaced to avoid conflicts)
    DEVICE_FINGERPRINT_KEY: 'neurovest_device_fp',
    DEVICE_TOKEN_KEY: 'neurovest_device_token',
    SESSION_ID_KEY: 'neurovest_session_id',

    // HTTP header names (must match backend)
    DEVICE_TOKEN_HEADER: 'X-Device-Token',
    SESSION_ID_HEADER: 'X-Session-ID',

    // Backend endpoints
    DEVICE_REGISTER_ENDPOINT: '/api/device/register',
    DEVICE_VALIDATE_ENDPOINT: '/api/device/validate',

    // Feature flags
    ENABLE_DEVICE_TRACKING: true,
    ENABLE_SESSION_TRACKING: true,
    ENABLE_DEBUG_LOGGING: process.env.NODE_ENV === 'development',

    // Token settings
    DEVICE_TOKEN_CHECK_INTERVAL: 24 * 60 * 60 * 1000, // Check daily

} as const;
