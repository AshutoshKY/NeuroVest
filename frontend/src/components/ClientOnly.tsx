/**
 * Client-Only Wrapper
 * Prevents SSR/ISR/SSG completely - only renders on client
 * Uses proper React hydration-safe pattern
 */

'use client';

import { useState, useEffect, ReactNode } from 'react';

interface ClientOnlyProps {
    children: ReactNode;
    fallback?: ReactNode;
}

export function ClientOnly({ children, fallback = null }: ClientOnlyProps) {
    const [hasMounted, setHasMounted] = useState(false);

    useEffect(() => {
        setHasMounted(true);
    }, []);

    if (!hasMounted) {
        return <>{fallback}</>;
    }

    return <>{children}</>;
}
