/**
 * Device Fingerprinting Utility
 * Generates unique device fingerprint using multiple factors
 */
import FingerprintJS from '@fingerprintjs/fingerprintjs';

interface DeviceInfo {
    fingerprint: string;
    screenResolution: string;
    timezone: string;
    language: string;
    platform: string;
    canvasFingerprint: string;
}

class DeviceFingerprintService {
    private fpPromise: Promise<any> | null = null;

    constructor() {
        if (typeof window !== 'undefined') {
            this.fpPromise = FingerprintJS.load();
        }
    }

    /**
     * Generate canvas fingerprint
     */
    private generateCanvasFingerprint(): string {
        try {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            if (!ctx) return 'no-canvas';

            canvas.width = 200;
            canvas.height = 50;

            ctx.textBaseline = 'top';
            ctx.font = '14px Arial';
            ctx.fillStyle = '#f60';
            ctx.fillRect(125, 1, 62, 20);
            ctx.fillStyle = '#069';
            ctx.fillText('Device Fingerprint', 2, 15);
            ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
            ctx.fillText('Browser Canvas', 4, 17);

            return canvas.toDataURL();
        } catch (error) {
            return 'canvas-error';
        }
    }

    /**
     * Get cached fingerprint or generate new one.
     * Only stores the fingerprint hash, not full device info.
     */
    async getFingerprint(): Promise<string> {
        // Check cache first
        const cached = localStorage.getItem('device_fingerprint');
        if (cached) {
            return cached;
        }

        // Generate new fingerprint
        if (!this.fpPromise) {
            throw new Error('Fingerprinting not available (SSR)');
        }

        const fp = await this.fpPromise;
        const result = await fp.get();
        const fingerprint = result.visitorId;

        // Store ONLY the fingerprint hash
        // Do NOT store device_info to prevent conflicts with device token
        localStorage.setItem('device_fingerprint', fingerprint);

        return fingerprint;
    }
}

export const deviceFingerprintService = new DeviceFingerprintService();
export default deviceFingerprintService;
