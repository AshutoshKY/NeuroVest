'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

/**
 * UI Context for Frontend v2
 * Manages:
 * - Mode switching (Lite/Pro)
 * - Theme switching (Light/Dark)
 * - Version toggle (v1/v2)
 * - LocalStorage persistence
 */

interface UIContextType {
    mode: 'lite' | 'pro';
    theme: 'light' | 'dark';
    version: 'v1' | 'v2';
    toggleMode: () => void;
    toggleTheme: () => void;
    toggleVersion: () => void;
    setMode: (mode: 'lite' | 'pro') => void;
    setTheme: (theme: 'light' | 'dark') => void;
    setVersion: (version: 'v1' | 'v2') => void;
}

const UIContext = createContext<UIContextType | null>(null);

export function UIProvider({ children }: { children: ReactNode }) {
    // Initialize from localStorage (client-side only)
    const [mode, setModeState] = useState<'lite' | 'pro'>('lite');
    const [theme, setThemeState] = useState<'light' | 'dark'>('dark');
    const [version, setVersionState] = useState<'v1' | 'v2'>('v2');
    const [mounted, setMounted] = useState(false);

    // Initialize from localStorage after mount (avoid hydration mismatch)
    useEffect(() => {
        setMounted(true);
        const savedMode = localStorage.getItem('ui_mode') as 'lite' | 'pro' | null;
        const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' | null;
        const savedVersion = localStorage.getItem('ui_version') as 'v1' | 'v2' | null;

        if (savedMode) setModeState(savedMode);
        if (savedTheme) setThemeState(savedTheme);
        if (savedVersion) setVersionState(savedVersion);
    }, []);

    // Sync mode with body class
    useEffect(() => {
        if (!mounted) return;

        // Remove all mode classes
        document.body.classList.remove('mode-lite', 'mode-pro');

        // Add current mode class
        document.body.classList.add(`mode-${mode}`);

        // Persist to localStorage
        localStorage.setItem('ui_mode', mode);
    }, [mode, mounted]);

    // Sync theme with html class
    useEffect(() => {
        if (!mounted) return;

        // Toggle dark class on html element
        document.documentElement.classList.toggle('dark', theme === 'dark');

        // Persist to localStorage
        localStorage.setItem('theme', theme);
    }, [theme, mounted]);

    // Sync version
    useEffect(() => {
        if (!mounted) return;

        // Add v2-ui class to body for font overrides
        document.body.classList.toggle('v2-ui', version === 'v2');

        localStorage.setItem('ui_version', version);
    }, [version, mounted]);

    // Toggle functions
    const toggleMode = () => {
        setModeState(current => current === 'lite' ? 'pro' : 'lite');
    };

    const toggleTheme = () => {
        setThemeState(current => current === 'light' ? 'dark' : 'light');
    };

    const toggleVersion = () => {
        setVersionState(current => current === 'v1' ? 'v2' : 'v1');
    };

    const contextValue: UIContextType = {
        mode,
        theme,
        version,
        toggleMode,
        toggleTheme,
        toggleVersion,
        setMode: setModeState,
        setTheme: setThemeState,
        setVersion: setVersionState,
    };

    // Don't render until mounted to avoid hydration mismatch
    if (!mounted) {
        return <>{children}</>;
    }

    return (
        <UIContext.Provider value={contextValue}>
            {children}
        </UIContext.Provider>
    );
}

/**
 * Hook to access UI context
 * @throws Error if used outside UIProvider
 */
export function useUI(): UIContextType {
    const context = useContext(UIContext);

    if (!context) {
        throw new Error('useUI must be used within UIProvider');
    }

    return context;
}

// Export context for advanced use cases
export { UIContext };
