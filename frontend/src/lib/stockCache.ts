/**
 * Stock Data Cache Utility
 * Caches stock info responses to reduce API calls and improve performance
 */

interface StockData {
    ticker: string;
    name: string;
    current_price: number;
    currency: string;
    day_change: number;
    day_change_percent: number;
    day_high: number;
    day_low: number;
    volume: number;
    market_cap: number;
    pe_ratio: number | null;
    timestamp: number; // When cached
}

interface CacheEntry {
    data: StockData;
    cachedAt: number;
}

const CACHE_KEY_PREFIX = 'stock_cache_';
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes in milliseconds

export class StockCache {
    /**
     * Get stock data from cache if valid
     */
    static get(ticker: string): StockData | null {
        try {
            const cacheKey = `${CACHE_KEY_PREFIX}${ticker}`;
            const cached = localStorage.getItem(cacheKey);

            if (!cached) return null;

            const entry: CacheEntry = JSON.parse(cached);
            const now = Date.now();

            // Check if cache is still valid
            if (now - entry.cachedAt > CACHE_TTL) {
                // Cache expired, remove it
                localStorage.removeItem(cacheKey);
                return null;
            }

            console.log(`[CACHE HIT] ${ticker} - age: ${Math.round((now - entry.cachedAt) / 1000)}s`);
            return entry.data;
        } catch (error) {
            console.error('[CACHE ERROR]', error);
            return null;
        }
    }

    /**
     * Save stock data to cache
     */
    static set(ticker: string, data: StockData): void {
        try {
            const cacheKey = `${CACHE_KEY_PREFIX}${ticker}`;
            const entry: CacheEntry = {
                data,
                cachedAt: Date.now()
            };

            localStorage.setItem(cacheKey, JSON.stringify(entry));
            console.log(`[CACHE SET] ${ticker}`);
        } catch (error) {
            console.error('[CACHE ERROR] Failed to save:', error);
        }
    }

    /**
     * Clear all stock cache
     */
    static clearAll(): void {
        try {
            const keys = Object.keys(localStorage);
            keys.forEach(key => {
                if (key.startsWith(CACHE_KEY_PREFIX)) {
                    localStorage.removeItem(key);
                }
            });
            console.log('[CACHE] Cleared all stock data');
        } catch (error) {
            console.error('[CACHE ERROR] Failed to clear:', error);
        }
    }

    /**
     * Clear cache for specific ticker
     */
    static clear(ticker: string): void {
        try {
            const cacheKey = `${CACHE_KEY_PREFIX}${ticker}`;
            localStorage.removeItem(cacheKey);
            console.log(`[CACHE CLEAR] ${ticker}`);
        } catch (error) {
            console.error('[CACHE ERROR]', error);
        }
    }

    /**
     * Get cache age in seconds
     */
    static getAge(ticker: string): number | null {
        try {
            const cacheKey = `${CACHE_KEY_PREFIX}${ticker}`;
            const cached = localStorage.getItem(cacheKey);

            if (!cached) return null;

            const entry: CacheEntry = JSON.parse(cached);
            return Math.round((Date.now() - entry.cachedAt) / 1000);
        } catch (error) {
            return null;
        }
    }
}
