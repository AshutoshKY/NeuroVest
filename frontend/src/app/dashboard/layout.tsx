'use client';

import { Header } from '@/components/Header';
import { BottomNav } from '@/components/BottomNav';
import ProtectedRoute from '@/components/ProtectedRoute';

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <ProtectedRoute>
            <div className="flex flex-col h-screen bg-slate-950 font-sans text-slate-100">
                {/* Header - No hamburger menu needed */}
                <Header />

                {/* Main Content Area - Full width, padding for bottom nav */}
                <main className="flex-1 overflow-y-auto pb-20 md:pb-24">
                    {children}
                </main>

                {/* Bottom Navigation */}
                <BottomNav />
            </div>
        </ProtectedRoute>
    );
}
