import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

/**
 * Maintenance Mode Middleware
 * 
 * When maintenance mode is active:
 * - Redirects all user pages to /maintenance
 * - Allows access to /admin-login for admin access
 * - Allows access to /admin/* for logged-in admins
 * - Allows access to /maintenance page itself
 * - Allows API routes to pass through
 */

// Paths that should always be accessible (even during maintenance)
const MAINTENANCE_BYPASS_PATHS = [
    '/maintenance',
    '/admin-login',
    '/admin',  // Admin panel and its sub-routes
    '/_next',  // Next.js assets
    '/api',    // API routes
    '/favicon.ico',
    '/images',
    '/fonts',
];

// Check if path should bypass maintenance redirect
function shouldBypassMaintenance(pathname: string): boolean {
    return MAINTENANCE_BYPASS_PATHS.some(path => pathname.startsWith(path));
}

export async function middleware(request: NextRequest) {
    const { pathname } = request.nextUrl;

    // Always allow bypass paths
    if (shouldBypassMaintenance(pathname)) {
        return NextResponse.next();
    }

    // Check for maintenance mode by looking at cookies or making a lightweight check
    // For now, we'll check via a custom header that can be set by the backend
    // In a real scenario, you might want to cache this in an edge-compatible way

    try {
        // Check maintenance mode from backend
        // Use internal Docker URL if available (SSR), otherwise localhost
        const backendUrl = process.env.API_INTERNAL_URL || 'http://backend:8000';
        const statusResponse = await fetch(`${backendUrl}/admin/session/status`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
            // Short timeout for edge function
            signal: AbortSignal.timeout(2000),
        });

        if (statusResponse.ok) {
            const data = await statusResponse.json();
            const isMaintenanceMode = data?.kill_switches?.maintenance_mode?.is_active === true;

            if (isMaintenanceMode) {
                // Check if user has admin token in cookies
                const token = request.cookies.get('access_token')?.value;

                // If no token, redirect to maintenance
                if (!token) {
                    const maintenanceUrl = new URL('/maintenance', request.url);
                    return NextResponse.redirect(maintenanceUrl);
                }

                // If has token, try to verify it's an admin
                // For simplicity, we let the frontend handle admin verification
                // The admin pages are protected by RBAC anyway
            }
        }
    } catch (error) {
        // If backend check fails, allow request through.
        // Silent failure is acceptable here as it likely means backend is down or restarting.
        // We don't want to spam logs with connection errors for every request.
        // console.warn('Maintenance check skipped (Backend unreachable)');
    }

    return NextResponse.next();
}

// Configure which routes this middleware runs on
export const config = {
    matcher: [
        /*
         * Match all request paths except for:
         * - _next/static (static files)
         * - _next/image (image optimization files)
         * - favicon.ico (favicon file)
         */
        '/((?!_next/static|_next/image|favicon.ico).*)',
    ],
};
