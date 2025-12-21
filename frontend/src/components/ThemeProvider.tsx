/**
 * Simple global theme provider that applies dark/light mode classes
 */
'use client';

import { useEffect } from 'react';
import { useThemeStore } from '@/store/themeStore';

export function ThemeProvider({ children }: { children: React.ReactNode }) {
    const { isDarkMode, setTheme } = useThemeStore();

    // Initialize theme on mount - sync with persisted state
    useEffect(() => {
        // Get persisted theme from localStorage
        const stored = localStorage.getItem('theme-storage');
        if (stored) {
            try {
                const { state } = JSON.parse(stored);
                applyTheme(state.isDarkMode);
            } catch (e) {
                // Fallback to default dark mode
                applyTheme(true);
            }
        } else {
            applyTheme(isDarkMode);
        }
    }, []);

    // Apply theme whenever it changes
    useEffect(() => {
        applyTheme(isDarkMode);
    }, [isDarkMode]);

    const applyTheme = (isDark: boolean) => {
        const html = document.documentElement;

        if (isDark) {
            html.classList.add('dark');
            html.style.setProperty('--bg-primary', '#0f172a');
            html.style.setProperty('--bg-secondary', '#1e293b');
            html.style.setProperty('--bg-tertiary', '#334155');
            html.style.setProperty('--text-primary', '#f1f5f9');
            html.style.setProperty('--text-secondary', '#cbd5e1');
            html.style.setProperty('--text-muted', '#94a3b8');
            html.style.setProperty('--border-color', '#334155');
        } else {
            html.classList.remove('dark');
            html.style.setProperty('--bg-primary', '#ffffff');
            html.style.setProperty('--bg-secondary', '#f8fafc');
            html.style.setProperty('--bg-tertiary', '#e2e8f0');
            html.style.setProperty('--text-primary', '#1e293b');
            html.style.setProperty('--text-secondary', '#475569');
            html.style.setProperty('--text-muted', '#64748b');
            html.style.setProperty('--border-color', '#e2e8f0');
        }
    };

    return <>{children}</>;
}
