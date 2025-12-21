import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface ThemeStore {
    isDarkMode: boolean;
    toggleTheme: () => void;
    setTheme: (isDark: boolean) => void;
}

export const useThemeStore = create<ThemeStore>()(
    persist(
        (set) => ({
            isDarkMode: true, // Default to dark mode
            toggleTheme: () => set((state) => {
                const newMode = !state.isDarkMode;
                console.log('[THEME] Toggling theme:', newMode ? 'dark' : 'light');
                return { isDarkMode: newMode };
            }),
            setTheme: (isDark: boolean) => set(() => {
                console.log('[THEME] Setting theme:', isDark ? 'dark' : 'light');
                return { isDarkMode: isDark };
            }),
        }),
        {
            name: 'theme-storage', // Storage key
        }
    )
);
