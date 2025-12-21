/**
 * Theme-aware utility classes
 * Use these anywhere you need theme-responsive styling
 */
export const themeClasses = {
    // Backgrounds
    bgPrimary: 'bg-white dark:bg-[#0a0e14]',
    bgSecondary: 'bg-gray-50 dark:bg-[#0d1117]',
    bgTertiary: 'bg-gray-100 dark:bg-[#161b22]',
    bgCard: 'bg-white dark:bg-[#0d1117]',
    bgInput: 'bg-gray-50 dark:bg-[#161b22]',
    bgHover: 'hover:bg-gray-100 dark:hover:bg-[#161b22]',

    // Borders
    border: 'border-gray-200 dark:border-gray-800',
    borderLight: 'border-gray-100 dark:border-gray-700',

    // Text
    textPrimary: 'text-gray-900 dark:text-gray-100',
    textSecondary: 'text-gray-600 dark:text-gray-400',
    textTertiary: 'text-gray-500 dark:text-gray-500',

    // Combined common patterns
    cardBase: 'bg-white dark:bg-[#0d1117] border border-gray-200 dark:border-gray-800',
    inputBase: 'bg-gray-50 dark:bg-[#161b22] border border-gray-300 dark:border-gray-700 text-gray-900 dark:text-gray-200',
};

/**
 * Get theme-aware className
 * @param darkClass - Class to use in dark mode
 * @param lightClass - Class to use in light mode
 * @returns Conditional className string
 */
export function themeClass(darkClass: string, lightClass: string, isDark: boolean): string {
    return isDark ? darkClass : lightClass;
}
