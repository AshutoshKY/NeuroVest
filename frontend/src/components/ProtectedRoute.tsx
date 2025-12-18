'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuthStore } from '@/store/authStore';

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
    const router = useRouter();
    const pathname = usePathname();
    const { isAuthenticated, isLoading, fetchUser } = useAuthStore();
    const [isVerifying, setIsVerifying] = useState(true);

    useEffect(() => {
        const initAuth = async () => {
            // If we're not authenticated, try to fetch user details (token might be in cookies/storage)
            if (!isAuthenticated) {
                await fetchUser();
            }
            setIsVerifying(false);
        };
        initAuth();
    }, [isAuthenticated, fetchUser]);

    useEffect(() => {
        if (!isVerifying && !isAuthenticated) {
            router.push(`/auth/login?redirect=${encodeURIComponent(pathname)}`);
        }
    }, [isVerifying, isAuthenticated, router, pathname]);

    if (isLoading || isVerifying) {
        return (
            <div className="flex h-screen w-full items-center justify-center bg-slate-950">
                <div className="h-8 w-8 animate-spin rounded-full border-4 border-emerald-500 border-t-transparent"></div>
            </div>
        );
    }

    if (!isAuthenticated) {
        return null; // Will redirect
    }

    return <>{children}</>;
}
