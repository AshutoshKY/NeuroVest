'use client';

import { AdminNav } from '@/components/AdminNav';
import { Header } from '@/components/Header'; // Reusing header
import AdminRoute from '@/components/AdminRoute';

export default function AdminLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <AdminRoute>
            <div className="flex h-screen bg-slate-950 font-sans text-slate-100">
                <aside className="hidden h-full w-64 border-r border-slate-800 bg-slate-950 md:flex md:flex-col">
                    <AdminNav />
                </aside>

                <div className="flex flex-1 flex-col overflow-hidden">
                    <Header />
                    <main className="flex-1 overflow-y-auto bg-slate-950 p-6">
                        <div className="mx-auto max-w-7xl space-y-8">
                            {children}
                        </div>
                    </main>
                </div>
            </div>
        </AdminRoute>
    );
}
