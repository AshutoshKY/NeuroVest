'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/authStore';
import ProtectedRoute from './ProtectedRoute';

// Helper to check if user has admin privileges
const isAdminUser = (role?: string): boolean => {
    if (!role) return false;
    const normalizedRole = role.toLowerCase();
    return normalizedRole === 'admin' || normalizedRole === 'super_admin';
};

export default function AdminRoute({ children }: { children: React.ReactNode }) {
    const router = useRouter();
    const { user, isLoading } = useAuthStore();
    const [hasChecked, setHasChecked] = useState(false);

    useEffect(() => {
        // Wait for auth state to be loaded
        if (isLoading) return;

        // Only check once we have user data
        if (user) {
            if (!isAdminUser(user.role)) {
                router.push('/dashboard');
            }
            setHasChecked(true);
        }
    }, [user, isLoading, router]);

    // Show loading while checking auth
    if (isLoading || (!hasChecked && !user)) {
        return (
            <div className="flex items-center justify-center h-screen bg-[#020617]">
                <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-indigo-500"></div>
            </div>
        );
    }

    return (
        <ProtectedRoute>
            {isAdminUser(user?.role) ? children : null}
        </ProtectedRoute>
    );
}
