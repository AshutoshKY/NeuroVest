'use client';

/**
 * Admin Emergency Login Page
 * 
 * This page is accessible during maintenance mode for admins to login.
 * Regular users cannot access admin login - only super_admin/admin roles.
 */

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/authStore';
import { Shield, Lock, AlertTriangle } from 'lucide-react';
import { motion } from 'framer-motion';

export default function AdminLoginPage() {
    const router = useRouter();
    const { login, isAuthenticated, user, isLoading: authLoading } = useAuthStore();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
        // If already logged in as admin, redirect to admin panel
        if (isAuthenticated && user && (user.role === 'admin' || user.role === 'super_admin')) {
            router.push('/admin');
        }
    }, [isAuthenticated, user, router]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);

        try {
            await login(email, password);
            // If we get here, login succeeded
            // Check if user is admin
            const currentUser = useAuthStore.getState().user;
            if (currentUser && (currentUser.role === 'admin' || currentUser.role === 'super_admin')) {
                router.push('/admin');
            } else {
                // Not an admin - logout and show error
                useAuthStore.getState().logout();
                setError('Access denied. Admin credentials required.');
            }
        } catch (err: any) {
            setError(err.message || 'Login failed');
        } finally {
            setIsLoading(false);
        }
    };

    if (authLoading) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-red-950/20 flex items-center justify-center">
                <div className="animate-spin w-8 h-8 border-2 border-red-500 border-t-transparent rounded-full"></div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-red-950/20 flex items-center justify-center p-6">
            {/* Animated background */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
                <motion.div
                    className="absolute top-1/4 -left-1/4 w-96 h-96 bg-red-500/5 rounded-full blur-3xl"
                    animate={{
                        scale: [1, 1.2, 1],
                        opacity: [0.3, 0.5, 0.3],
                    }}
                    transition={{ duration: 8, repeat: Infinity }}
                />
            </div>

            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                className="relative z-10 w-full max-w-md"
            >
                {/* Header */}
                <div className="text-center mb-8">
                    <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ delay: 0.2, type: "spring" }}
                        className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-br from-red-500/20 to-orange-500/20 border border-red-500/30 mb-4"
                    >
                        <Shield className="w-8 h-8 text-red-400" />
                    </motion.div>
                    <h1 className="text-2xl font-bold text-white">Admin Access</h1>
                    <p className="text-slate-400 text-sm mt-2">System is in maintenance mode</p>
                </div>

                {/* Warning Banner */}
                <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-4 mb-6 flex items-start gap-3">
                    <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
                    <div className="text-sm">
                        <div className="text-amber-400 font-medium">Maintenance Mode Active</div>
                        <div className="text-amber-400/70 mt-1">
                            Only administrators can login during maintenance. Regular users will see the maintenance page.
                        </div>
                    </div>
                </div>

                {/* Login Form */}
                <form onSubmit={handleSubmit} className="bg-slate-900/50 backdrop-blur-xl border border-slate-700/50 rounded-2xl p-8">
                    {error && (
                        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 mb-6 text-red-400 text-sm">
                            {error}
                        </div>
                    )}

                    <div className="space-y-5">
                        <div>
                            <label className="block text-sm font-medium text-slate-400 mb-2">
                                Admin Email
                            </label>
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className="w-full px-4 py-3 bg-slate-800/50 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-red-500 transition"
                                placeholder="admin@example.com"
                                required
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-slate-400 mb-2">
                                Password
                            </label>
                            <div className="relative">
                                <input
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="w-full px-4 py-3 bg-slate-800/50 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-red-500 transition"
                                    placeholder="••••••••"
                                    required
                                />
                                <Lock className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                            </div>
                        </div>
                    </div>

                    <button
                        type="submit"
                        disabled={isLoading}
                        className="w-full mt-6 py-3 px-4 bg-gradient-to-r from-red-500 to-orange-500 hover:from-red-600 hover:to-orange-600 text-white font-bold rounded-lg transition disabled:opacity-50 flex items-center justify-center gap-2"
                    >
                        {isLoading ? (
                            <>
                                <div className="animate-spin w-5 h-5 border-2 border-white border-t-transparent rounded-full"></div>
                                Authenticating...
                            </>
                        ) : (
                            <>
                                <Shield className="w-5 h-5" />
                                Admin Login
                            </>
                        )}
                    </button>
                </form>

                <p className="text-center text-slate-600 text-xs mt-6">
                    This login is for system administrators only.
                </p>
            </motion.div>
        </div>
    );
}
