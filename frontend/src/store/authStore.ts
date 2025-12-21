/**
 * Authentication Store (Zustand)
 * Manages user authentication state globally
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import apiClient from '../lib/api';

interface User {
    id: number;
    email: string;
    full_name: string;
    display_name?: string;
    role: 'user' | 'admin';
    is_verified: boolean;
    created_at: string;
}

interface AuthState {
    user: User | null;
    isAuthenticated: boolean;
    isLoading: boolean;

    // Guest tracking
    guestRequestsRemaining: number;
    guestLimit: number;
    guestResetAt: Date | null;

    // Actions
    login: (email: string, password: string) => Promise<void>;
    signup: (email: string, password: string, fullName: string, displayName?: string) => Promise<void>;
    logout: () => Promise<void>;
    fetchUser: () => Promise<void>;
    checkGuestLimit: () => Promise<void>;
    setUser: (user: User | null) => void;
}

export const useAuthStore = create<AuthState>()(
    persist(
        (set, get) => ({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            guestRequestsRemaining: 2,
            guestLimit: 2,
            guestResetAt: null,

            login: async (email: string, password: string) => {
                set({ isLoading: true });
                try {
                    // Login to get tokens
                    const response = await apiClient.post('/auth/login', { email, password });
                    // Tokens are in httpOnly cookies, fetch user data
                    const userResponse = await apiClient.get('/auth/me');
                    const user = userResponse.data;
                    set({ user, isAuthenticated: true, isLoading: false });
                } catch (error: any) {
                    set({ isLoading: false });
                    // Enhanced error handling - extract meaningful message
                    console.error('[AUTH] Login failed:', error);

                    // Throw error with proper message for frontend to display
                    if (error.response?.data?.detail) {
                        throw new Error(error.response.data.detail);
                    } else if (error.response?.status === 401) {
                        throw new Error('Incorrect email or password');
                    } else if (error.response?.status === 403) {
                        throw new Error(error.response.data?.detail || 'Access denied');
                    } else if (error.response?.status === 429) {
                        throw new Error('Too many login attempts. Please try again later.');
                    } else if (error.message) {
                        throw new Error(error.message);
                    } else {
                        throw new Error('Login failed. Please try again.');
                    }
                }
            },

            signup: async (email: string, password: string, fullName: string, displayName?: string) => {
                set({ isLoading: true });
                try {
                    await apiClient.post('/auth/register', {
                        email,
                        password,
                        full_name: fullName,
                        display_name: displayName,
                    });
                    // Auto-login after signup
                    await get().login(email, password);
                } catch (error) {
                    set({ isLoading: false });
                    throw error;
                }
            },

            logout: async () => {
                try {
                    await apiClient.post('/auth/logout');
                } finally {
                    set({ user: null, isAuthenticated: false });
                    localStorage.removeItem('auth-storage');
                }
            },

            fetchUser: async () => {
                set({ isLoading: true });
                try {
                    const response = await apiClient.get('/auth/me');
                    set({ user: response.data, isAuthenticated: true, isLoading: false });
                } catch (error) {
                    set({ user: null, isAuthenticated: false, isLoading: false });
                }
            },

            checkGuestLimit: async () => {
                try {
                    // CRITICAL: Include tracking headers for accurate rate limiting
                    const { TrackingHeaders } = await import('../lib/tracking-headers');
                    const trackingHeaders = await TrackingHeaders.getHeaders();

                    // Use new unified endpoint that works for both guests and users
                    const response = await apiClient.get('/tracking/user/check-limit', {
                        withCredentials: true,
                        headers: trackingHeaders as any
                    });

                    set({
                        guestRequestsRemaining: response.data.remaining || 0,
                        guestLimit: response.data.limit || 2,
                        guestResetAt: response.data.reset_at ? new Date(response.data.reset_at) : null,
                    });
                } catch (error) {
                    // If endpoint fails, log but don't block (graceful degradation)
                    console.warn('[AUTH] Rate limit check unavailable, using defaults:', error);
                    set({
                        guestRequestsRemaining: 2, // Default: allow 2 requests
                        guestLimit: 2,
                        guestResetAt: null,
                    });
                }
            },


            setUser: (user: User | null) => {
                set({ user, isAuthenticated: !!user });
            },
        }),
        {
            name: 'auth-storage',
            partialize: (state) => ({
                user: state.user,
                isAuthenticated: state.isAuthenticated,
            }),
        }
    )
);

export default useAuthStore;
