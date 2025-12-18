'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/authStore';
import ProtectedRoute from './ProtectedRoute';

export default function AdminRoute({ children }: { children: React.ReactNode }) {
    const router = useRouter();
    const { user } = useAuthStore();

    useEffect(() => {
        if (user && user.role !== 'admin') {
            router.push('/dashboard');
        }
    }, [user, router]);

    return (
        <ProtectedRoute>
            {user?.role === 'admin' ? children : null}
        </ProtectedRoute>
    );
}
