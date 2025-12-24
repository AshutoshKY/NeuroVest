'use client';

import { Search } from 'lucide-react';

/**
 * Search Bar Component - POC Design Match
 * Exactly matches design_poc_1/index.html
 */

interface SearchResult {
    ticker: string;
    name: string;
    exchange: string;
}

interface SearchBarProps {
    value: string;
    onChange: (value: string) => void;
    onSelect: (stock: SearchResult) => void;
    onKeyDown?: (e: React.KeyboardEvent<HTMLInputElement>) => void;
    results: SearchResult[];
    isSearching: boolean;
    showDropdown: boolean;
    disabled?: boolean;
    placeholder?: string;
}

export function SearchBar({
    value,
    onChange,
    onSelect,
    onKeyDown,
    results,
    isSearching,
    showDropdown,
    disabled = false,
    placeholder = "Search ticker (e.g. RELIANCE)..."
}: SearchBarProps) {
    return (
        <div className="relative w-full max-w-[600px] group z-10">
            {/* Search Icon */}
            <div className="absolute inset-y-0 left-5 flex items-center pointer-events-none">
                <Search className="w-6 h-6 text-gray-400" />
            </div>

            {/* Search Input */}
            <input
                type="text"
                value={value}
                onChange={(e) => onChange(e.target.value)}
                onKeyDown={onKeyDown}
                className="w-full bg-white dark:bg-[#18181b] border border-gray-200 dark:border-zinc-800 rounded-full py-7 pl-14 pr-20 text-2xl text-gray-900 dark:text-white shadow-xl dark:shadow-none focus:outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 transition placeholder-gray-400"
                placeholder={placeholder}
                disabled={disabled}
            />

            {/* Enter Button (Circular) */}
            <button
                onClick={(e) => {
                    e.preventDefault();
                    if (onKeyDown) {
                        onKeyDown({ key: 'Enter' } as any);
                    }
                }}
                disabled={disabled || !value}
                className="absolute right-3 top-1/2 -translate-y-1/2 w-12 h-12 rounded-full bg-gradient-to-r from-primary-500 to-purple-600 hover:from-primary-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center transition-all shadow-lg"
            >
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                </svg>
            </button>

            {/* Loading Spinner */}
            {isSearching && (
                <div className="absolute right-5 top-1/2 -translate-y-1/2">
                    <svg className="w-5 h-5 text-primary-500 animate-spin" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                </div>
            )}

            {/* Dropdown Results */}
            {showDropdown && results.length > 0 && (
                <div className="absolute z-50 w-full mt-2 bg-white dark:bg-[#18181b] border border-gray-200 dark:border-zinc-800 rounded-2xl shadow-2xl max-h-64 overflow-y-auto">
                    {results.map((result, index) => (
                        <button
                            key={index}
                            onClick={() => onSelect(result)}
                            className="w-full flex items-center justify-between px-5 py-3 hover:bg-gray-50 dark:hover:bg-zinc-900 transition-colors border-b border-gray-200 dark:border-zinc-800 last:border-b-0 text-left"
                        >
                            <div>
                                <div className="font-semibold text-gray-900 dark:text-white">{result.ticker}</div>
                                <div className="text-sm text-gray-500 dark:text-gray-400">{result.name}</div>
                            </div>
                            <div className="text-xs text-gray-400">{result.exchange}</div>
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
}
