'use client';

/**
 * Admin Layout
 * 
 * Matches POC design: dark theme, sticky header, persistent sidebar
 */

import { AdminNav } from '@/components/AdminNav';
import AdminRoute from '@/components/AdminRoute';

export default function AdminLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <AdminRoute>
            <div className="flex h-screen overflow-hidden text-sm font-sans" style={{ backgroundColor: '#020617', color: '#94a3b8' }}>
                {/* Sidebar */}
                <AdminNav />

                {/* Main Content */}
                <main className="flex-1 flex flex-col relative overflow-hidden">
                    {children}
                </main>
            </div>
        </AdminRoute>
    );
}
